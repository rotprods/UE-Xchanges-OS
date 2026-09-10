# Erasmus+ email signature

Audience: organisers, sending organisations, partners, National Agencies and participant groups.

This version is warmer and more creative than the Swiss employment signature. It puts the personal creative brand, Travel Reels and WhatsApp first, while keeping every authorised professional channel one click away.

## Install in Gmail

1. Open `email-signature.html` from an HTTPS page or a local HTTP server.
2. Select **Copy signature**.
3. In Gmail, open **Settings → See all settings → General → Signature**.
4. Create a new signature and paste it.
5. Send a test email to yourself and verify the image and links.

The images use immutable commit-pinned HTTPS URLs. They are available while the pull request is open and remain stable if the branch is later deleted.

The copy button writes both rich HTML and plain text. On older browsers it uses a real `execCommand('copy')` fallback; if both browser mechanisms are blocked, it visibly selects the signature and asks for `Ctrl/Cmd+C` instead of reporting a false success.

Automated Playwright QA checks every image and favicon over HTTP, exact links, rich clipboard content, the forced fallback path, pasted HTML, responsive overflow and screenshots at seven viewport widths.
