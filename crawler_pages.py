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
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9,en;q=0.7'}
S=requests.Session(); S.headers.update(HEADERS)

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 s=re.sub(r'\bvegan\b','',s)
 s=re.sub(r'\s*,\s*', ' ', s)
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def price_from_text(s):
 m=re.search(r'(?<!\d)(\d{1,3})[,.](\d{2})\s*€',s)
 return float(m.group(1)+'.'+m.group(2)) if m else None

def get(url):
 r=S.get(url,timeout=40); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser')

def extract_rewe():
 soup=get(REWE_URL); found=[]; seen=set()
 for el in soup.select('article, [class*=offer], [class*=product], [data-testid*=offer], [data-testid*=product]'):
  p=price_from_text(' '.join(el.stripped_strings))
  if p is None: continue
  img=el.find('img'); name=((img.get('alt') or '').strip() if img else '')
  if not name: continue
  key=(slug(name),p)
  if key in seen: continue
  seen.add(key); src=(img.get('src') or img.get('data-src') or '') if img else ''
  found.append({'name':name,'quantity':'','category':'Markt-Angebot','price':p,'image':urljoin(REWE_URL,src) if src else ''})
 return found

def offer_block_for_image(img):
 for parent in list(img.parents)[:9]:
  if parent.name in ('body','html'): break
  text=' '.join(parent.stripped_strings)
  prices=re.findall(r'(?<!\d)\d{1,3}[,.]\d{2}\s*€',text)
  product_imgs=[i for i in parent.find_all('img') if (i.get('alt') or '').strip() and 'prospekt seite' not in (i.get('alt') or '').casefold()]
  if len(prices)==1 and len(product_imgs)<=2 and len(text)<600: return parent
 return None

def extract_fallback_page(slide):
 url=f'{FALLBACK_URL}?slide={slide}&week=1'; soup=get(url); found=[]; seen=set()
 for img in soup.find_all('img'):
  name=(img.get('alt') or '').strip()
  if not name or 'prospekt seite' in name.casefold() or re.fullmatch(r'seite\s*\d+',name,re.I): continue
  block=offer_block_for_image(img)
  if not block: continue
  text=' '.join(block.stripped_strings); p=price_from_text(text)
  if p is None: continue
  pieces=[x.strip() for x in block.stripped_strings if x.strip()]
  desc=next((x for x in pieces if x!=name and price_from_text(x) is None and 3<len(x)<240 and not x.lower().startswith(('image:', 'angebote auf'))), '')
  src=img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
  key=(slug(name),p)
  if key in seen: continue
  seen.add(key); found.append({'name':name,'quantity':desc,'category':'Prospekt','price':p,'image':urljoin(url,src) if src else ''})
 return found

def extract_fallback():
 first=get(f'{FALLBACK_URL}?slide=0&week=1'); text=' '.join(first.stripped_strings)
 m=re.search(r'(?:1\s*/\s*|Seite\s+1\s+von\s+)(\d{1,2})',text,re.I); pages=int(m.group(1)) if m else 26
 pages=max(1,min(pages,60)); all_found=[]; seen=set()
 for slide in range(pages):
  try: items=extract_fallback_page(slide)
  except Exception as e: print(f'Prospektseite {slide+1} fehlgeschlagen: {e}'); continue
  print(f'Prospektseite {slide+1}/{pages}: {len(items)} Angebote')
  for item in items:
   key=(slug(item['name']),item['price'])
   if key not in seen: seen.add(key); all_found.append(item)
 return all_found

def extract():
 try:
  offers=extract_rewe()
  if offers: return offers,REWE_URL
 except Exception as e: print('REWE Direktabruf nicht möglich:',e)
 offers=extract_fallback()
 if not offers: raise RuntimeError('Prospektquelle erreichbar, aber keine Produktangebote erkannt.')
 return offers,FALLBACK_URL

def dedupe_history(history):
 out=[]; seen=set()
 for h in sorted(history,key=lambda x:(x.get('date',''),x.get('price',0))):
  key=(h.get('date'),h.get('price'))
  if key not in seen: seen.add(key); out.append(h)
 return out

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'store':{},'products':[]}
 offers,source=extract(); today=datetime.now(timezone.utc).date().isoformat()
 # Merge old duplicate product records using the normalized product key.
 merged={}
 for old in data.get('products',[]):
  pid=slug(old.get('name') or old.get('id',''))
  if not pid: continue
  if pid not in merged:
   old['id']=pid; old['history']=dedupe_history(old.get('history',[])); merged[pid]=old
  else:
   target=merged[pid]
   target['history']=dedupe_history(target.get('history',[])+old.get('history',[]))
   if old.get('image') and not target.get('image'): target['image']=old['image']
   if old.get('quantity') and not target.get('quantity'): target['quantity']=old['quantity']
 data['products']=list(merged.values())
 # Replace today's observations atomically, preventing duplicate same-day entries.
 for item in data['products']:
  item['history']=[h for h in item.get('history',[]) if h.get('date')!=today]
 byid={p['id']:p for p in data['products']}
 for o in offers:
  pid=slug(o['name']); item=byid.get(pid)
  if item is None:
   item={'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'history':[]}; data['products'].append(item); byid[pid]=item
  item.update({'name':o['name'],'quantity':o.get('quantity',''),'category':o.get('category','Angebot')})
  if o.get('image'): item['image']=o['image']
  observation={'date':today,'price':o['price']}
  if observation not in item.setdefault('history',[]): item['history'].append(observation)
  item['history']=dedupe_history(item['history'])
 data['products']=[p for p in data['products'] if p.get('history')]
 data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds'); data['source']=source; data['last_import_count']=len(offers)
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'{len(offers)} Angebote verarbeitet aus {source}')
if __name__=='__main__': main()
