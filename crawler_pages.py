import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

STORE_ID='240367'
REWE_URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
FALLBACK_URL='https://prospektewoche.de/rewe'
OUT=Path('data/offers.json')
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9,en;q=0.7','Accept':'text/html,application/xhtml+xml'}
S=requests.Session(); S.headers.update(HEADERS)

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def parse_price(s):
 m=re.search(r'(?<!\d)(\d{1,3})[,.](\d{2})\s*€',s)
 return float(m.group(1)+'.'+m.group(2)) if m else None

def get(url):
 r=S.get(url,timeout=40); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser')

def extract_rewe():
 soup=get(REWE_URL); found=[]; seen=set()
 for el in soup.select('article, [class*=offer], [class*=product], [data-testid*=offer], [data-testid*=product]'):
  text=' '.join(el.stripped_strings); p=parse_price(text)
  if p is None: continue
  img=el.find('img'); alt=(img.get('alt') or '').strip() if img else ''
  lines=[x.strip() for x in el.stripped_strings if 2<len(x.strip())<140]
  name=alt or next((x for x in lines if parse_price(x) is None and not x.lower().startswith(('aktion','knaller'))),None)
  if not name: continue
  key=(name.casefold(),p)
  if key in seen: continue
  seen.add(key); src=(img.get('src') or img.get('data-src') or '') if img else ''
  found.append({'name':name,'brand':'','quantity':'','category':'Markt-Angebot','price':p,'image':urljoin(REWE_URL,src) if src else ''})
 return found

def product_from_price_node(node,page_url):
 # Walk upwards until the price belongs to a compact block containing a product image.
 for parent in list(node.parents)[:8]:
  if parent.name in ('body','html'): break
  text=' '.join(parent.stripped_strings)
  if len(text)>900: continue
  imgs=parent.find_all('img')
  alts=[(i.get('alt') or '').strip() for i in imgs]
  alts=[a for a in alts if a and 'prospekt seite' not in a.casefold() and not re.fullmatch(r'seite\s*\d+',a,re.I)]
  if not alts: continue
  name=max(alts,key=len)
  p=parse_price(node.get_text(' ',strip=True)) or parse_price(text)
  if p is None: continue
  img=next((i for i in imgs if (i.get('alt') or '').strip()==name),imgs[0])
  src=img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
  pieces=[x.strip() for x in parent.stripped_strings if x.strip()]
  desc=''
  for x in pieces:
   if x!=name and parse_price(x) is None and 3<len(x)<220 and 'Angebote auf dieser Seite' not in x:
    desc=x; break
  return {'name':name,'brand':'','quantity':desc,'category':'Prospekt','price':p,'image':urljoin(page_url,src) if src else ''}
 return None

def extract_fallback_page(slide):
 url=f'{FALLBACK_URL}?slide={slide}&week=1'
 soup=get(url); found=[]; seen=set()
 # The site renders each offer with an image alt (product name) and a separate price text.
 for txt in soup.find_all(string=re.compile(r'\d{1,3}[,.]\d{2}\s*€')):
  item=product_from_price_node(txt.parent,url)
  if not item: continue
  key=(item['name'].casefold(),item['price'])
  if key in seen: continue
  seen.add(key); found.append(item)
 return found

def extract_fallback():
 # Determine page count from the prospect page; default safely to 26 for current format.
 first=get(f'{FALLBACK_URL}?slide=0&week=1')
 text=' '.join(first.stripped_strings)
 m=re.search(r'(?:1\s*/\s*|Seite\s+1\s+von\s+)(\d{1,2})',text,re.I)
 pages=int(m.group(1)) if m else 26
 pages=max(1,min(pages,60))
 all_found=[]; seen=set()
 for slide in range(pages):
  try: page_items=extract_fallback_page(slide)
  except Exception as e:
   print(f'Prospektseite {slide+1} fehlgeschlagen: {e}'); continue
  print(f'Prospektseite {slide+1}/{pages}: {len(page_items)} Angebote')
  for item in page_items:
   key=(item['name'].casefold(),item['price'])
   if key not in seen: seen.add(key); all_found.append(item)
 return all_found

def extract():
 try:
  offers=extract_rewe()
  if offers:
   print(f'Direkter REWE-Abruf: {len(offers)} Angebote')
   return offers,REWE_URL
 except Exception as e: print('REWE Direktabruf nicht möglich:',e)
 offers=extract_fallback()
 if not offers: raise RuntimeError('Prospektquelle erreichbar, aber keine Produktangebote erkannt.')
 return offers,FALLBACK_URL

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'store':{'id':STORE_ID,'name':'REWE Vigheshan Gahndi oHG','address':'Industriestraße 40, 65439 Flörsheim-Weilbach'},'products':[]}
 offers,source=extract(); today=datetime.now(timezone.utc).date().isoformat(); byid={p['id']:p for p in data.get('products',[])}
 for o in offers:
  pid=slug(o['name']); item=byid.get(pid)
  if item is None:
   item={'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'history':[]}; data.setdefault('products',[]).append(item); byid[pid]=item
  if o.get('image'): item['image']=o['image']
  if o.get('quantity'): item['quantity']=o['quantity']
  h=item.setdefault('history',[])
  if not any(x.get('date')==today and x.get('price')==o['price'] for x in h): h.append({'date':today,'price':o['price']})
 data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds'); data['source']=source; data['last_import_count']=len(offers)
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'{len(offers)} Angebote verarbeitet aus {source}')
if __name__=='__main__': main()
