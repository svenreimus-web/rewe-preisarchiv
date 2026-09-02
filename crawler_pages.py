import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
STORE_ID='240367'
URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
OUT=Path('data/offers.json')
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9'}
def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]
def price(s):
 m=re.search(r'(\d{1,3})[,.](\d{2})\s*(?:€|EUR)',s); return float(m.group(1)+'.'+m.group(2)) if m else None
def extract():
 r=requests.get(URL,headers=HEADERS,timeout=40); r.raise_for_status(); soup=BeautifulSoup(r.text,'html.parser'); found=[]; seen=set()
 for el in soup.select('article, [class*=offer], [class*=product], [data-testid*=offer], [data-testid*=product]'):
  text=' '.join(el.stripped_strings); p=price(text)
  if p is None: continue
  lines=[x.strip() for x in el.stripped_strings if 2<len(x.strip())<120]
  name=next((x for x in lines if not re.search(r'\d+[,.]\d{2}\s*(?:€|EUR)',x)),None)
  if not name: continue
  key=(name.casefold(),p)
  if key in seen: continue
  seen.add(key); img=el.find('img'); src=(img.get('src') or img.get('data-src') or '') if img else ''
  found.append({'name':name,'brand':'','quantity':'','category':'Angebot','price':p,'image':src})
 return found
def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'store':{'id':STORE_ID,'name':'REWE Vigheshan Gahndi oHG','address':'Industriestraße 40, 65439 Flörsheim-Weilbach'},'products':[]}
 offers=extract()
 if not offers: raise RuntimeError('Keine Angebote erkannt; Archiv bleibt unverändert.')
 today=datetime.now(timezone.utc).date().isoformat(); byid={p['id']:p for p in data.get('products',[])}
 for o in offers:
  pid=slug((o.get('brand','')+' '+o['name']).strip()); item=byid.get(pid)
  if item is None:
   item={'id':pid,'name':o['name'],'brand':o.get('brand',''),'quantity':o.get('quantity',''),'category':'Angebot','image':o.get('image',''),'history':[]}; data.setdefault('products',[]).append(item); byid[pid]=item
  if o.get('image'): item['image']=o['image']
  h=item.setdefault('history',[])
  if not any(x.get('date')==today and x.get('price')==o['price'] for x in h): h.append({'date':today,'price':o['price']})
 data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds'); data['source']=URL; OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'{len(offers)} Angebote verarbeitet')
if __name__=='__main__': main()
