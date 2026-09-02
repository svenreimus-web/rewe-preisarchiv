import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

REWE_URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
REWE_FALLBACK='https://prospektewoche.de/rewe'
GLOBUS_OFFICIAL='https://www.globus.de/hattersheim/aktuelles-prospekt.php'
GLOBUS_FALLBACK='https://prospektewoche.de/globus'
OUT=Path('data/offers.json')
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9,en;q=0.7'}
S=requests.Session(); S.headers.update(HEADERS)

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 s=re.sub(r'\bvegan\b','',s); s=re.sub(r'\s*,\s*',' ',s)
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def price_from_text(s):
 m=re.search(r'(?<!\d)(\d{1,3})[,.](\d{2})\s*€',s)
 return float(m.group(1)+'.'+m.group(2)) if m else None

def get(url):
 r=S.get(url,timeout=40); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser')

def offer_block_for_image(img):
 for parent in list(img.parents)[:9]:
  if parent.name in ('body','html'): break
  text=' '.join(parent.stripped_strings)
  prices=re.findall(r'(?<!\d)\d{1,3}[,.]\d{2}\s*€',text)
  product_imgs=[i for i in parent.find_all('img') if (i.get('alt') or '').strip() and 'prospekt seite' not in (i.get('alt') or '').casefold()]
  if len(prices)==1 and len(product_imgs)<=2 and len(text)<600:return parent
 return None

def extract_prospektewoche(base,store):
 first=get(f'{base}?slide=0&week=1'); text=' '.join(first.stripped_strings)
 m=re.search(r'(?:1\s*/\s*|Seite\s+1\s+von\s+)(\d{1,2})',text,re.I); pages=int(m.group(1)) if m else (38 if store=='GLOBUS' else 26)
 pages=max(1,min(pages,60)); all_found=[]; seen=set()
 for slide in range(pages):
  url=f'{base}?slide={slide}&week=1'
  try:soup=get(url)
  except Exception as e: print(f'{store} Seite {slide+1} fehlgeschlagen: {e}'); continue
  count=0
  for img in soup.find_all('img'):
   name=(img.get('alt') or '').strip()
   if not name or 'prospekt seite' in name.casefold() or re.fullmatch(r'seite\s*\d+',name,re.I):continue
   block=offer_block_for_image(img)
   if not block:continue
   p=price_from_text(' '.join(block.stripped_strings))
   if p is None:continue
   pieces=[x.strip() for x in block.stripped_strings if x.strip()]
   desc=next((x for x in pieces if x!=name and price_from_text(x) is None and 3<len(x)<240 and not x.lower().startswith(('image:','angebote auf'))),'')
   src=img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
   key=(slug(name),p)
   if key in seen:continue
   seen.add(key); count+=1
   all_found.append({'name':name,'quantity':desc,'category':'Prospekt','price':p,'image':urljoin(url,src) if src else '','store':store})
  print(f'{store} Prospektseite {slide+1}/{pages}: {count} Angebote')
 return all_found

def extract_rewe_direct():
 soup=get(REWE_URL); found=[]; seen=set()
 for el in soup.select('article,[class*=offer],[class*=product],[data-testid*=offer],[data-testid*=product]'):
  p=price_from_text(' '.join(el.stripped_strings)); img=el.find('img'); name=((img.get('alt') or '').strip() if img else '')
  if p is None or not name:continue
  key=(slug(name),p)
  if key in seen:continue
  seen.add(key); src=(img.get('src') or img.get('data-src') or '') if img else ''
  found.append({'name':name,'quantity':'','category':'Markt-Angebot','price':p,'image':urljoin(REWE_URL,src) if src else '','store':'REWE'})
 return found

def dedupe_history(history):
 out=[];seen=set()
 for h in sorted(history,key=lambda x:(x.get('date',''),x.get('price',0))):
  key=(h.get('date'),h.get('price'))
  if key not in seen:seen.add(key);out.append(h)
 return out

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]}
 today=datetime.now(timezone.utc).date().isoformat()
 try:
  rewe=extract_rewe_direct()
  if not rewe:raise RuntimeError('keine Direktangebote')
  rewe_source=REWE_URL
 except Exception as e:
  print('REWE Direktabruf nicht möglich:',e); rewe=extract_prospektewoche(REWE_FALLBACK,'REWE'); rewe_source=REWE_FALLBACK
 # GLOBUS Hattersheim official page confirms the market/week; product extraction uses the weekly prospect fallback.
 try:
  official=' '.join(get(GLOBUS_OFFICIAL).stripped_strings)
  if 'GLOBUS Hattersheim' not in official:raise RuntimeError('Hattersheim auf Marktseite nicht bestätigt')
  print('GLOBUS Hattersheim Marktseite bestätigt')
 except Exception as e:print('GLOBUS Marktseitenprüfung fehlgeschlagen:',e)
 globus=extract_prospektewoche(GLOBUS_FALLBACK,'GLOBUS'); globus_source=GLOBUS_FALLBACK
 offers=rewe+globus
 # Preserve histories separately by market. Old records without a market are REWE records.
 merged={}
 for old in data.get('products',[]):
  st=old.get('store') or 'REWE'; old['store']=st
  pid=st.lower()+'-'+slug(old.get('name') or old.get('id',''))
  if not pid:continue
  old['id']=pid; old['history']=dedupe_history(old.get('history',[])); merged[pid]=old
 for item in merged.values():
  item['history']=[h for h in item.get('history',[]) if h.get('date')!=today]
 for o in offers:
  pid=o['store'].lower()+'-'+slug(o['name']); item=merged.get(pid)
  if item is None:
   item={'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'store':o['store'],'history':[]}; merged[pid]=item
  item.update({'name':o['name'],'quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'store':o['store']})
  if o.get('image'):item['image']=o['image']
  obs={'date':today,'price':o['price']}
  if obs not in item['history']:item['history'].append(obs)
  item['history']=dedupe_history(item['history'])
 data['products']=[p for p in merged.values() if p.get('history')]
 data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
 data['sources']={'REWE':rewe_source,'GLOBUS':globus_source,'GLOBUS_market_confirmation':GLOBUS_OFFICIAL}
 data['last_import_count']={'REWE':len(rewe),'GLOBUS':len(globus),'total':len(offers)}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'Fertig: REWE {len(rewe)}, GLOBUS {len(globus)}, gesamt {len(offers)} Angebote')
if __name__=='__main__':main()
