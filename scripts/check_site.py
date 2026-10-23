"""Offline release checks; browser behaviour and public access require separate QA."""
import json
import re
from pathlib import Path
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set(); self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, 'Duplicate HTML id: '+a['id']
            self.ids.add(a['id'])
        self.links.extend(a[k] for k in ['href','src'] if k in a)
def local(url):
    if url.startswith(('https:','http:','mailto:')): return
    if url.startswith('#'):
        assert url[1:] in page.ids,url
    else: assert (ROOT/url.split('#')[0].split('?')[0].removeprefix('./')).is_file(),url
page=Page();html=(ROOT/'index.html').read_text(encoding='utf-8');page.feed(html)
for link in page.links: local(link)
registry=(ROOT/'src/charts.js').read_text(encoding='utf-8')
mounts=re.findall(r'''["']?mount["']?\s*:\s*["']#([^"']+)''',registry)
specs=re.findall(r'''["']?spec["']?\s*:\s*["'](\./charts/[^"']+)''',registry)
assert len(mounts)==len(set(mounts))==12
assert len(specs)==15
assert all(m in page.ids for m in mounts)
def walk(value):
    if isinstance(value,dict):
        if 'url' in value and isinstance(value['url'],str):local(value['url'])
        for child in value.values():walk(child)
    elif isinstance(value,list):
        for child in value:walk(child)
for name in specs:
    local(name);spec=json.loads((ROOT/name).read_text(encoding='utf-8'))
    assert any(spec['$schema'].startswith('https://vega.github.io/schema/'+kind+'/') for kind in ['vega-lite','vega'])
    walk(spec)
assert 'Laurence Downie' in html and '32477848' in html
for path in [ROOT/'index.html',*list((ROOT/'src').glob('*.js'))]:
    text=path.read_text(encoding='utf-8')
    assert not any(marker in text for marker in ['\ufffd','\u00c2\u00b7','\u00e2\u2020']),f'Encoding damage: {path}'
print('PASS: 12 unique mounts, 15 Vega/Vega-Lite views, local assets/data links, authorship; public deployment NOT VERIFIED')
