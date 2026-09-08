import json, re, unicodedata
from copy import deepcopy
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

REWE_URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
REWE_FALLBACK='https://prospektewoche.de/rewe'
GLOBUS_OFFICIAL='https://www.globus.de/hattersheim/aktuelles-prospekt.php'
GLOBUS_FALLBACK='https://prospektewoche.de/globus'
OUT=Path('data/offers.json')
TZ=ZoneInfo('Europe/Berlin')
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9,en;q=0.7'}
S=requests.Session(); S.headers.update(HEADERS)

def now(): return datetime.now(TZ)
def today_iso(): return now().date().isoformat()

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); s=re.sub(r'\bvegan\b','',s); s=re.sub(r'\s*,\s*',' ',s)
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def price_from_text(s):
 # Ein Angebotspreis muss explizit mit € ausgezeichnet sein. So werden
 # Pfand-, Liter-, Prozent- oder Mengenangaben nicht versehentlich als Preis gelesen.
 m=re.search(r'(?<!\d)(\d{1,3})[,.](\d{2})\s*€',s)
 return float(m.group(1)+'.'+m.group(2)) if m else None

def get(url):
 r=S.get(url,timeout=40); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser')

def parse_period(text):
 patterns=[
  r'(?:Angebot\s+gültig\s+vom\s*|Gültig\s+vom\s*)?(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?\s*(?:bis(?:\s+zum)?|[-–])\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})',
  r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})'
 ]
 for pat in patterns:
  m=re.search(pat,text,re.I)
  if not m: continue
  try:
   d1,mo1,y1,d2,mo2,y2=m.groups(); y2=int(y2); y2=y2+2000 if y2<100 else y2; y1=int(y1) if y1 else y2; y1=y1+2000 if y1<100 else y1
   start=date(y1,int(mo1),int(d1)); end=date(y2,int(mo2),int(d2))
   return {'valid_from':start.isoformat(),'valid_until':end.isoformat()}
  except ValueError: pass
 return None

def source_period(url):
 soup=get(url); return parse_period(' '.join(soup.stripped_strings)),soup

def offer_block_for_image(img):
 for parent in list(img.parents)[:9]:
  if parent.name in ('body','html'): break
  text=' '.join(parent.stripped_strings)
  prices=re.findall(r'(?<!\d)\d{1,3}[,.]\d{2}\s*€',text)
  product_imgs=[i for i in parent.find_all('img') if (i.get('alt') or '').strip() and 'prospekt seite' not in (i.get('alt') or '').casefold()]
  if len(prices)==1 and len(product_imgs)<=2 and len(text)<600:return parent
 return None

def extract_prospektewoche(base,store):
 first=get(f'{base}?slide=0&week=1'); text=' '.join(first.stripped_strings); period=parse_period(text)
 m=re.search(r'(?:1\s*/\s*|Seite\s+1\s+von\s+)(\d{1,2})',text,re.I)
 pages=int(m.group(1)) if m else (38 if store=='GLOBUS' else 26); pages=max(1,min(pages,60)); all_found=[]; seen=set()
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
   block_text=' '.join(block.stripped_strings); p=price_from_text(block_text)
   if p is None:continue
   pieces=[x.strip() for x in block.stripped_strings if x.strip()]
   desc=next((x for x in pieces if x!=name and price_from_text(x) is None and 3<len(x)<240 and not x.lower().startswith(('image:','angebote auf'))),'')
   src=img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''; key=(slug(name),p)
   if key in seen:continue
   seen.add(key); count+=1; all_found.append({'name':name,'quantity':desc,'category':'Prospekt','price':p,'image':urljoin(url,src) if src else '','store':store})
  print(f'{store} Prospektseite {slide+1}/{pages}: {count} Angebote')
 return all_found,period

def extract_rewe_direct():
 period,soup=source_period(REWE_URL); found=[]; seen=set()
 for el in soup.select('article,[class*=offer],[class*=product],[data-testid*=offer],[data-testid*=product]'):
  p=price_from_text(' '.join(el.stripped_strings)); img=el.find('img'); name=((img.get('alt') or '').strip() if img else '')
  if p is None or not name:continue
  key=(slug(name),p)
  if key in seen:continue
  seen.add(key); src=(img.get('src') or img.get('data-src') or '') if img else ''
  found.append({'name':name,'quantity':'','category':'Markt-Angebot','price':p,'image':urljoin(REWE_URL,src) if src else '','store':'REWE'})
 return found,period

def dedupe_history(history):
 out=[];seen=set()
 for h in sorted(history,key=lambda x:(x.get('date',''),x.get('price',0))):
  key=(h.get('date'),h.get('price'))
  if key not in seen:seen.add(key);out.append(h)
 return out

def upsert_history(history,obs):
 # Pro Angebotsperiode genau einen beobachteten Preis speichern. Ein erneuter
 # Crawl ersetzt damit frühere Fehlwerte desselben Gültigkeitsstarts.
 cleaned=[h for h in dedupe_history(history) if h.get('date')!=obs.get('date')]
 cleaned.append(obs)
 return sorted(cleaned,key=lambda x:(x.get('date',''),x.get('price',0)))

def period_is_current(p,today): return bool(p and p.get('valid_from')<=today<=p.get('valid_until'))
def period_is_new(p,old): return bool(p and (not old or (p.get('valid_from'),p.get('valid_until'))!=(old.get('valid_from'),old.get('valid_until'))))

def stable_view(data):
 x=deepcopy(data); x.pop('updated_at',None)
 return x

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]}
 before=stable_view(data); old_updated_at=data.get('updated_at'); today=today_iso(); old_periods=data.get('validity',{})
 try:
  rewe,rewe_period=extract_rewe_direct()
  if not rewe:raise RuntimeError('keine Direktangebote')
  rewe_source=REWE_URL
 except Exception as e:
  print('REWE Direktabruf nicht möglich:',e); rewe,rewe_period=extract_prospektewoche(REWE_FALLBACK,'REWE'); rewe_source=REWE_FALLBACK
 try:
  globus_period,official_soup=source_period(GLOBUS_OFFICIAL); official=' '.join(official_soup.stripped_strings)
  if 'GLOBUS Hattersheim' not in official:raise RuntimeError('Hattersheim auf Marktseite nicht bestätigt')
  print('GLOBUS Hattersheim Marktseite bestätigt')
 except Exception as e: print('GLOBUS Marktseitenprüfung fehlgeschlagen:',e); globus_period=None
 globus,globus_fallback_period=extract_prospektewoche(GLOBUS_FALLBACK,'GLOBUS'); globus_period=globus_period or globus_fallback_period; globus_source=GLOBUS_FALLBACK
 candidates={'REWE':(rewe,rewe_period,rewe_source),'GLOBUS':(globus,globus_period,globus_source)}; accepted={}; validity=dict(old_periods)
 for st,(items,period,src) in candidates.items():
  if period_is_current(period,today) and items:
   accepted[st]=items
   old=old_periods.get(st,{})
   if period_is_new(period,old) or old.get('source')!=src:
    validity[st]={**period,'source':src,'checked_at':now().isoformat(timespec='seconds')}
   else:
    validity[st]=old
   print(st,'Zeitraum akzeptiert:',period,'neu=',period_is_new(period,old))
  else:
   accepted[st]=None; print(st,'nicht übernommen: Zeitraum fehlt/veraltet oder keine Angebote:',period,len(items))
 merged={}
 for old in data.get('products',[]):
  st=old.get('store') or 'REWE'; old['store']=st; pid=st.lower()+'-'+slug(old.get('name') or old.get('id',''))
  if not pid:continue
  old['id']=pid; old['history']=dedupe_history(old.get('history',[])); old['active']=period_is_current(validity.get(st),today); merged[pid]=old
 for st,items in accepted.items():
  if items is None:continue
  for item in merged.values():
   if item.get('store')==st:item['active']=False
  for o in items:
   pid=st.lower()+'-'+slug(o['name']); item=merged.get(pid)
   if item is None:item={'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'store':st,'history':[]}
   period_changed=item.get('valid_from')!=validity[st]['valid_from'] or item.get('valid_until')!=validity[st]['valid_until']
   item.update({'name':o['name'],'quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'store':st,'active':True,'valid_from':validity[st]['valid_from'],'valid_until':validity[st]['valid_until']})
   if period_changed or not item.get('last_seen'):item['last_seen']=today
   if o.get('image'):item['image']=o['image']
   item['history']=upsert_history(item.get('history',[]),{'date':validity[st]['valid_from'],'price':o['price']}); merged[pid]=item
 data['products']=[p for p in merged.values() if p.get('history')]; data['validity']=validity
 sources=data.get('sources',{}); sources.update({'REWE':rewe_source,'GLOBUS':globus_source,'GLOBUS_market_confirmation':GLOBUS_OFFICIAL}); data['sources']=sources
 counts=data.get('last_import_count',{}); counts.update({st:(len(v) if v is not None else 0) for st,v in accepted.items()}); counts['total']=sum(v for k,v in counts.items() if k!='total' and isinstance(v,int)); data['last_import_count']=counts
 data['active_offer_count']=sum(1 for p in data['products'] if p.get('active') is True)
 if stable_view(data)!=before:data['updated_at']=now().isoformat(timespec='seconds')
 elif old_updated_at:data['updated_at']=old_updated_at
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Fertig:',data['active_offer_count'],'aktuelle Angebote; Archiv',len(data['products']))

if __name__=='__main__':main()
