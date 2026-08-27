from __future__ import annotations
import html,re
from html.parser import HTMLParser
from pathlib import Path

class _TextExtractor(HTMLParser):
    def __init__(self)->None: super().__init__(); self.parts=[]; self._skip=0
    def handle_starttag(self,tag,attrs):
        if tag in {"script","style","noscript"}: self._skip+=1
        elif tag in {"p","div","br","li","h1","h2","h3","h4","tr"} and not self._skip: self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in {"script","style","noscript"} and self._skip: self._skip-=1
    def handle_data(self,data):
        if not self._skip: self.parts.append(data)

def clean_text(text:str)->str:
    text=html.unescape(text); text=re.sub(r"[\t\r ]+"," ",text); text=re.sub(r"\n\s*\n+","\n\n",text); return text.strip()

def html_to_text(raw_html:str)->str:
    p=_TextExtractor(); p.feed(raw_html); return clean_text("".join(p.parts))

def extract_pdf_text(path:str|Path)->str:
    try: from pypdf import PdfReader
    except ImportError as exc: raise RuntimeError("PDF extraction requires: pip install 'ue-xchanges-os[pdf]'") from exc
    return clean_text("\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages))
