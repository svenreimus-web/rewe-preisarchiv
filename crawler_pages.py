import json, re, unicodedata
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

STORE_ID='240367'
URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
OUT=Path('docs/data/offers.json')
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; REWE-Preisarchiv/1.0)'}

def slug(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def price(s):
    m=re.search(r'(\d{1,3}(?:[.,]\d{2}))\s*(?:€|EUR)',s)
    return float(m.group(1).replace(',','.')) if m else None

def extract():
    r=requests.get(URL,headers=HEADERS,timeout=30); r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser'); found=[]; seen=set()
    for el in soup.select('article, [class*=offer], [class*=product], [data-testid*=offer]'):
        text=' '.join(el.stripped_strings); p=price(text)
        if p is None or len(text)<4: continue
        lines=[x.strip() for x in el.stripped_strings if x.strip()]
        name=next((x for x in lines if not re.search(r'\d+[.,]\d{2}\s*(?:€|EUR)',x)),None)
        if not name or len(name)>140: continue
        key=(name.lower(),p)
        if key in seen: continue
        seen.add(key); img=el.find('img'); src=''
        if img: src=img.get('src') or img.get('data-src') or ''
        found.append({'name':name,'brand':'','category':'Angebot','price':p,'image':src})
    return found

def main():
    data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'store':{'id':STORE_ID},'products':[]}
    today=datetime.now().astimezone().date().isoformat(); byid={p['id']:p for p in data.get('products',[])}
    offers=extract()
    if not offers: raise RuntimeError('Keine Angebote erkannt; bestehendes Archiv bleibt unverändert.')
    for o in offers:
        pid=slug((o.get('brand','')+' '+o['name']).strip())
        p=byid.get(pid)
        if not p:
            p={'id':pid,'name':o['name'],'brand':o.get('brand',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'history':[]}; data.setdefault('products',[]).append(p); byid[pid]=p
        elif o.get('image') and not p.get('image'): p['image']=o['image']
        h=p.setdefault('history',[])
        if not h or h[-1].get('date')!=today or h[-1].get('price')!=o['price']: h.append({'date':today,'price':o['price']})
    data['updated_at']=datetime.now().astimezone().isoformat(timespec='seconds')
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(offers)} Angebote verarbeitet')
if __name__=='__main__': main()
