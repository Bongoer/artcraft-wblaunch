#!/usr/bin/env python3
"""Add a consistent, unobtrusive branded WASM startup screen to the official web sites.

Doesn't touch the engine, its bundled assets, or bootstrap module ordering. The overlay
remains while the app's existing loading element is visible and then fades away after
an actual canvas is sized. Errors remain visible (there is no unconditional timeout).
"""
from pathlib import Path
import re
import sys

site = Path(sys.argv[1])
slug = sys.argv[2]
name = {
    'photocraft':'PhotoCraft', 'lightcraft':'LightCraft', 'filmcraft':'FilmCraft',
    'designcraft':'DesignCraft', 'vectorcraft':'VectorCraft', 'pdfcraft':'PdfCraft',
    'effectcraft':'EffectCraft', 'wordcraft':'WordCraft', 'deckcraft':'DeckCraft',
    'gridcraft':'GridCraft', 'cadcraft':'CADCraft', 'soundcraft':'SoundCraft',
    'figcraft':'FigCraft',
}.get(slug)
if not name:
    raise SystemExit('Invalid Craft app name')
p = site / 'index.html'
html = p.read_text(encoding='utf-8')
if 'id="wikipod-startup"' in html:
    raise SystemExit('Startup screen already inserted')
if not re.search(r'<body(?:\s[^>]*)?>', html, re.I):
    raise SystemExit(f'{slug}: missing body element')
if '</head>' not in html.lower():
    raise SystemExit(f'{slug}: missing head element')

style = '''
<style id="wikipod-startup-style">
#wikipod-startup{position:fixed;inset:0;z-index:2147483500;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:18px;
  background:#191a1e;color:#ededf1;font:400 16px/1.4 system-ui,-apple-system,sans-serif;
  pointer-events:none;transition:opacity .27s ease-out,visibility .27s ease-out}
#wikipod-startup.is-finished{opacity:0;visibility:hidden}
#wikipod-startup img{width:72px;height:72px;object-fit:contain;border-radius:16px}
#wikipod-startup span{font-size:16px;letter-spacing:0}
#wikipod-startup small{position:absolute;bottom:22px;font-size:12px;color:#999aa1;
  text-align:center;max-width:80vw}
@media (prefers-reduced-motion:reduce){#wikipod-startup{transition:none}}
</style>
'''
body = f'''<div id="wikipod-startup" role="status" aria-live="polite">
<img src="./wikipod-app-icon.png" alt="" width="72" height="72">
<span>Loading {name}...</span>
<small id="wikipod-startup-hint"></small>
</div>
'''
script = '''
<script id="wikipod-startup-script">
(()=>{
  const splash=document.getElementById('wikipod-startup');
  if(!splash)return;
  const hint=document.getElementById('wikipod-startup-hint');
  const orig=[...document.querySelectorAll('[id]')].filter(el=>
    el!==splash && !el.id.startsWith('wikipod-startup') &&
    /(^|[-_])(loading|splash|loader)([-_]|$)/i.test(el.id));
  const start=performance.now();
  let removed=false;
  function visible(el){return el.isConnected && getComputedStyle(el).display!=='none' &&
    getComputedStyle(el).visibility!=='hidden' && Number(getComputedStyle(el).opacity)!==0;}
  function ready(){
    if(removed)return;
    const canvas=[...document.querySelectorAll('canvas')].some(c=>
      c.width>300 && c.height>200 && c.getBoundingClientRect().width>100);
    const nativeDone=orig.length===0 || orig.every(el=>!visible(el));
    if(canvas && nativeDone && performance.now()-start>750){
      removed=true;splash.classList.add('is-finished');
      splash.addEventListener('transitionend',()=>splash.remove(),{once:true});
      setTimeout(()=>splash.remove(),600);
      return;
    }
    if(performance.now()-start>20000 && hint && !hint.textContent){
      hint.textContent='Still loading. If this stays here, try reloading the page.';
    }
    setTimeout(ready,250);
  }
  setTimeout(ready,250);
})();
</script>
'''
html = re.sub(r'</head>', style+'</head>', html, count=1, flags=re.I)
html = re.sub(r'(<body(?:\s[^>]*)?>)', r'\1\n'+body, html, count=1, flags=re.I)
# Place script at end of body so the upstream app boot code is left intact.
if '</body>' in html.lower():
    html = re.sub(r'</body>', script+'</body>', html, count=1, flags=re.I)
else:
    html += script
p.write_text(html,encoding='utf-8')
print(f'Added real-app splash to {slug}')
