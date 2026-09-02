import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

STORE_ID='240367'
REWE_URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
FALLBACK_URL='https://prospektewoche.de/rewe'
OUT=Path('data/offers.json')
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9'}

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def parse_price(s):
 m=re.search(r'(\d{1,3})[,.](\d{2})\s*€',s)
 return float(m.group(1)+'.'+m.group(2)) if m else None

def get(url):
 r=requests.get(url,headers=HEADERS,timeout=40)
 r.raise_for_status()
 return BeautifulSoup(r.text,'html.parser')

def extract_rewe():
 soup=get(REWE_URL); found=[]; seen=set()
 for el in soup.select('article, [class*=offer], [class*=product], [data-testid*=offer], [data-testid*=product]'):
  text=' '.join(el.stripped_strings); p=parse_price(text)
  if p is None: continue
  lines=[x.strip() for x in el.stripped_strings if 2<len(x.strip())<140]
  name=next((x for x in lines if parse_price(x) is None and not x.lower().startswith(('aktion','knaller'))),None)
  if not name: continue
  key=(name.casefold(),p)
  if key in seen: continue
  seen.add(key); img=el.find('img'); src=(img.get('src') or img.get('data-src') or '') if img else ''
  found.append({'name':name,'brand':'','quantity':'','category':'Angebot','price':p,'image':src})
 return found

def extract_fallback():
 soup=get(FALLBACK_URL); found=[]; seen=set()
 # ProspekteWoche exposes product cards as image + title/description/price text.
 for el in soup.select('article, li, div'):
  text=' '.join(el.stripped_strings)
  p=parse_price(text)
  if p is None or len(text)>700: continue
  headings=el.find_all(['h2','h3','h4','strong','b'])
  candidates=[x.get_text(' ',strip=True) for x in headings]
  if not candidates:
   img=el.find('img'); alt=(img.get('alt') or '').strip() if img else ''
   if alt and 'prospekt seite' not in alt.casefold(): candidates=[alt]
  name=next((x for x in candidates if 2<len(x)<140 and parse_price(x) is None and 'seite ' not in x.casefold()),None)
  if not name: continue
  key=(name.casefold(),p)
  if key in seen: continue
  seen.add(key); img=el.find('img'); src=(img.get('src') or img.get('data-src') or '') if img else ''
  quantity=''
  m=re.search(r'(?:je\s+)?([\d.,]+\s*(?:g|kg|ml|l|x\s*[\d.,]+\s*l)[^€]{0,30})',text,re.I)
  if m: quantity=m.group(1).strip(' ,.-')
  found.append({'name':name,'brand':'','quantity':quantity,'category':'Prospekt','price':p,'image':src})
 return found

def extract():
 try:
  offers=extract_rewe()
  if offers: return offers, REWE_URL
 except Exception as e:
  print('REWE Direktabruf nicht möglich:',e)
 offers=extract_fallback()
 if not offers: raise RuntimeError('Auch die Prospekt-Fallbackquelle lieferte keine erkennbaren Angebote.')
 return offers, FALLBACK_URL

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'store':{'id':STORE_ID,'name':'REWE Vigheshan Gahndi oHG','address':'Industriestraße 40, 65439 Flörsheim-Weilbach'},'products':[]}
 offers,source=extract(); today=datetime.now(timezone.utc).date().isoformat(); byid={p['id']:p for p in data.get('products',[])}
 for o in offers:
  pid=slug((o.get('brand','')+' '+o['name']).strip()); item=byid.get(pid)
  if item is None:
   item={'id':pid,'name':o['name'],'brand':o.get('brand',''),'quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'history':[]}; data.setdefault('products',[]).append(item); byid[pid]=item
  if o.get('image'): item['image']=o['image']
  if o.get('quantity'): item['quantity']=o['quantity']
  h=item.setdefault('history',[])
  if not any(x.get('date')==today and x.get('price')==o['price'] for x in h): h.append({'date':today,'price':o['price']})
 data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds'); data['source']=source
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'{len(offers)} Angebote verarbeitet aus {source}')
if __name__=='__main__': main()
