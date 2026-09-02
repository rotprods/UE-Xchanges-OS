import fs from 'node:fs/promises';
import path from 'node:path';

const batch = Number.parseInt(process.env.BATCH ?? '', 10);
if (!Number.isInteger(batch) || batch < 0 || batch > 5) throw new Error('BATCH must be an integer from 0 to 5');
const manifest = JSON.parse(await fs.readFile('ops/telegram/doc2-manifest.json', 'utf8'));
const items = manifest.items.slice(batch * 10, batch * 10 + 10);
if (items.length !== 10) throw new Error(`expected 10 items for batch ${batch}, got ${items.length}`);
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36';

function decodeEntities(input = '') {
  return input.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(Number.parseInt(h, 16)))
    .replace(/&#([0-9]+);/g, (_, d) => String.fromCodePoint(Number.parseInt(d, 10)))
    .replace(/&nbsp;/gi, ' ').replace(/&amp;/gi, '&').replace(/&lt;/gi, '<').replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"').replace(/&#39;/gi, "'");
}
function cleanText(html = '') {
  return decodeEntities(html.replace(/<br\s*\/?>/gi, '\n').replace(/<\/(?:p|div|li)>/gi, '\n').replace(/<[^>]+>/g, ''))
    .replace(/\r/g, '').replace(/[ \t]+\n/g, '\n').replace(/\n[ \t]+/g, '\n').replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]{2,}/g, ' ').trim();
}
function firstMatch(html, patterns) { for (const p of patterns) { const m = html.match(p); if (m?.[1]) return decodeEntities(m[1]).trim(); } return null; }
function exactMessageBlock(html, channel, postId) {
  const token = `${channel}/${postId}`;
  const start = html.indexOf(`data-post="${token}"`) >= 0 ? html.lastIndexOf('<div', html.indexOf(`data-post="${token}"`)) : -1;
  if (start < 0) return null;
  const next = html.indexOf('tgme_widget_message_wrap', start + 100);
  return html.slice(start, next > start ? next : Math.min(html.length, start + 150000));
}
function extractMessageText(html, channel, postId) {
  const block = exactMessageBlock(html, channel, postId) ?? html;
  for (const p of [
    /<div[^>]+class=["'][^"']*tgme_widget_message_text[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]+class=["'][^"']*js-message_text[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<meta[^>]+property=["']og:description["'][^>]+content=["']([\s\S]*?)["'][^>]*>/i,
    /<meta[^>]+name=["']description["'][^>]+content=["']([\s\S]*?)["'][^>]*>/i
  ]) { const m = block.match(p); if (m?.[1]) { const t = cleanText(m[1]); if (t) return t; } }
  return '';
}
function extractDate(html, channel, postId) {
  const block = exactMessageBlock(html, channel, postId) ?? html;
  return firstMatch(block, [/<time[^>]+datetime=["']([^"']+)["']/i, /data-time=["']([^"']+)["']/i]);
}
function extractLinks(html, channel, postId) {
  const block = exactMessageBlock(html, channel, postId) ?? html; const links = new Set();
  for (const m of block.matchAll(/href=["']([^"']+)["']/gi)) {
    let href = decodeEntities(m[1]).trim(); if (!href || href.startsWith('#') || href.startsWith('javascript:')) continue;
    if (href.startsWith('//')) href = `https:${href}`; if (href.startsWith('/')) href = `https://t.me${href}`; if (!/^https?:\/\//i.test(href)) continue;
    try { const u = new URL(href); u.hash = ''; if (u.hostname === 't.me' && !u.pathname.includes(`/${postId}`)) continue; links.add(u.toString()); } catch {}
  }
  return [...links].sort();
}
async function fetchCandidate(url) {
  const c = new AbortController(); const timeout = setTimeout(() => c.abort(), 20000);
  try { const r = await fetch(url, {redirect:'follow', signal:c.signal, headers:{'user-agent':UA,'accept':'text/html,application/xhtml+xml','accept-language':'en-US,en;q=0.9'}}); return {ok:r.ok,status:r.status,final_url:r.url,html:await r.text()}; }
  finally { clearTimeout(timeout); }
}
async function fetchPost(item) {
  const candidates = [`${item.url}?embed=1&mode=tme`, item.url, `https://t.me/s/${manifest.channel}?before=${Number(item.post_id)+1}`]; const attempts=[];
  for (const candidate of candidates) {
    try { const r=await fetchCandidate(candidate); const text=r.ok?extractMessageText(r.html,manifest.channel,item.post_id):''; const date=r.ok?extractDate(r.html,manifest.channel,item.post_id):null; const links=r.ok?extractLinks(r.html,manifest.channel,item.post_id):[]; attempts.push({url:candidate,http_status:r.status,final_url:r.final_url,text_length:text.length}); if(r.ok&&text.length>=20) return {...item,extraction_state:'SOURCE_CONTENT_RESOLVED',http_status:r.status,fetched_url:candidate,final_url:r.final_url,published_at:date,text,outbound_links:links,attempts}; }
    catch(error){ attempts.push({url:candidate,error:error?.name??'Error',message:String(error?.message??error).slice(0,180)}); }
  }
  return {...item,extraction_state:'SOURCE_FETCH_FAILED',http_status:attempts.find(x=>x.http_status)?.http_status??null,fetched_url:null,final_url:null,published_at:null,text:'',outbound_links:[],attempts};
}
const results=[];
for(const item of items){ const result=await fetchPost(item); results.push(result); console.log(`TELEGRAM_RESULT ${JSON.stringify({raw_node_id:result.raw_node_id,post_id:result.post_id,extraction_state:result.extraction_state,published_at:result.published_at,text:result.text,outbound_links:result.outbound_links})}`); }
const resolved=results.filter(x=>x.extraction_state==='SOURCE_CONTENT_RESOLVED').length; const failed=results.length-resolved;
const output={batch_index:batch,source_batch:manifest.batch,channel:manifest.channel,fetched_at:new Date().toISOString(),total:results.length,resolved,failed,results};
await fs.mkdir('telegram-artifacts',{recursive:true}); await fs.writeFile(path.join('telegram-artifacts',`batch-${batch}.json`),JSON.stringify(output,null,2));
console.log(`TELEGRAM_BATCH_SUMMARY ${JSON.stringify({batch,total:results.length,resolved,failed})}`);
