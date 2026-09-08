import json, re, unicodedata
from datetime import datetime, timezone, date
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

REWE_URL='https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/'
REWE_FALLBACK='https://prospektewoche.de/rewe'
GLOBUS_OFFICIAL='https://www.globus.de/hattersheim/aktuelles-prospekt.php'
GLOBUS_FALLBACK='https://prospektewoche.de/globus'
EDEKA_BUCH='https://www.edeka.de/maerkte/046253/'
EDEKA_HALLER='https://www.edeka.de/maerkte/042385/'
OUT=Path('data/offers.json')
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36','Accept-Language':'de-DE,de;q=0.9,en;q=0.7'}
S=requests.Session(); S.headers.update(HEADERS)

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); s=re.sub(r'\bvegan\b','',s); s=re.sub(r'\s*,\s*',' ',s)
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def price_from_text(s):
 m=re.search(r'(?<!\d)(\d{1,3})[,.](\d{2})\s*€?',s); return float(m.group(1)+'.'+m.group(2)) if m else None

def get(url):
 r=S.get(url,timeout=40); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser')

def parse_period(text, today=None):
 today=today or datetime.now(timezone.utc).date()
 patterns=[r'(?:Angebot\s+gültig\s+vom\s*|Gültig\s+vom\s*)?(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?\s*(?:bis(?:\s+zum)?|[-–])\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})',r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})']
 for pat in patterns:
  m=re.search(pat,text,re.I)
  if not m: continue
  g=m.groups()
  try:
   if len(g)==6:
    d1,mo1,y1,d2,mo2,y2=g; y2=int(y2); y2=y2+2000 if y2<100 else y2; y1=int(y1) if y1 else y2; y1=y1+2000 if y1<100 else y1
   else: continue
   start=date(y1,int(mo1),int(d1)); end=date(y2,int(mo2),int(d2)); return {'valid_from':start.isoformat(),'valid_until':end.isoformat()}
  except ValueError: pass
 return None

def source_period(url):
 soup=get(url); text=' '.join(soup.stripped_strings); return parse_period(text), soup

def offer_block_for_image(img):
 for parent in list(img.parents)[:9]:
  if parent.name in ('body','html'): break
  text=' '.join(parent.stripped_strings); prices=re.findall(r'(?<!\d)\d{1,3}[,.]\d{2}\s*€',text); product_imgs=[i for i in parent.find_all('img') if (i.get('alt') or '').strip() and 'prospekt seite' not in (i.get('alt') or '').casefold()]
  if len(prices)==1 and len(product_imgs)<=2 and len(text)<600:return parent
 return None

def extract_prospektewoche(base,store):
 first=get(f'{base}?slide=0&week=1'); text=' '.join(first.stripped_strings); period=parse_period(text)
 m=re.search(r'(?:1\s*/\s*|Seite\s+1\s+von\s+)(\d{1,2})',text,re.I); pages=int(m.group(1)) if m else (38 if store=='GLOBUS' else 26); pages=max(1,min(pages,60)); all_found=[]; seen=set()
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
   pieces=[x.strip() for x in block.stripped_strings if x.strip()]; desc=next((x for x in pieces if x!=name and price_from_text(x) is None and 3<len(x)<240 and not x.lower().startswith(('image:','angebote auf'))),''); src=img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''; key=(slug(name),p)
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
  seen.add(key); src=(img.get('src') or img.get('data-src') or '') if img else ''; found.append({'name':name,'quantity':'','category':'Markt-Angebot','price':p,'image':urljoin(REWE_URL,src) if src else '','store':'REWE'})
 return found,period

def extract_edeka_from_text(text,url,store,market_name):
 if market_name.casefold() not in text.casefold(): raise RuntimeError(f'{market_name} auf EDEKA-Seite nicht bestätigt')
 period=parse_period(text); found=[]; seen=set()
 for seg in re.split(r'(?=#+\s*Angebot:\s*)',text):
  m=re.match(r'#+\s*Angebot:\s*(.+?)(?:\r?\n|$)',seg,re.I)
  if not m: continue
  name=re.sub(r'[*_`]+','',m.group(1)).strip()
  pm=re.search(r'Festpreis\s+von\s*(\d{1,3})[,.](\d{2})\s*€',seg,re.I)
  if pm: p=float(pm.group(1)+'.'+pm.group(2))
  else:
   p=price_from_text(seg)
  if p is None: continue
  key=(slug(name),p)
  if key in seen: continue
  seen.add(key); desc=''
  for line in seg.splitlines()[1:]:
   x=re.sub(r'^[\s>*#-]+','',line).replace('**','').strip(); xl=x.casefold()
   if not x or len(x)>320 or price_from_text(x) is not None or xl.startswith(('gültig ab','app preis','festpreis','rabattierter preis','grundpreis','image','diese artikel','abgabe in','niedrigster gesamtpreis','mit payback','dialog schließen')): continue
   if x.startswith('![') or x.startswith('['): continue
   if len(x)>4: desc=x; break
  found.append({'name':name,'quantity':desc,'category':'Markt-Angebot','price':p,'image':'','store':store})
 print(f'{store}: {len(found)} Angebote über EDEKA-Textquelle')
 return found,period

def extract_edeka_market(url,store,market_name):
 try:
  period,soup=source_period(url); page_text=' '.join(soup.stripped_strings)
  if market_name.casefold() not in page_text.casefold(): raise RuntimeError(f'{market_name} auf Marktseite nicht bestätigt')
  found=[]; seen=set()
  for h in soup.find_all(re.compile(r'^h[1-6]$')):
   raw=' '.join(h.stripped_strings); m=re.match(r'\s*Angebot:\s*(.+)',raw,re.I)
   if not m: continue
   name=m.group(1).strip(); block=None
   for parent in list(h.parents)[:7]:
    if parent.name in ('body','html'): break
    txt=' '.join(parent.stripped_strings)
    if price_from_text(txt) is not None and len(txt)<1800: block=parent; break
   if not block: continue
   txt=' '.join(block.stripped_strings); pm=re.search(r'Festpreis\s+von\s*(\d{1,3})[,.](\d{2})\s*€',txt,re.I); p=float(pm.group(1)+'.'+pm.group(2)) if pm else price_from_text(txt)
   if p is None: continue
   key=(slug(name),p)
   if key in seen: continue
   seen.add(key); img=block.find('img'); src=(img.get('src') or img.get('data-src') or img.get('data-lazy-src') or '') if img else ''
   pieces=[x.strip() for x in block.stripped_strings if x.strip()]; desc=''
   for x in pieces:
    xl=x.casefold()
    if x==raw or x==name or price_from_text(x) is not None or xl.startswith(('gültig ab','festpreis','rabattierter preis','app preis','grundpreis','image','diese artikel','abgabe in','niedrigster gesamtpreis','mit payback')): continue
    if 4<len(x)<320: desc=x; break
   found.append({'name':name,'quantity':desc,'category':'Markt-Angebot','price':p,'image':urljoin(url,src) if src else '','store':store})
  if found:
   print(f'{store}: {len(found)} Angebote direkt von offizieller EDEKA-Marktseite')
   return found,period
  raise RuntimeError('keine Angebote im Direkt-HTML')
 except Exception as direct_error:
  print(f'{store} Direktabruf nicht möglich: {direct_error}; nutze Text-Fallback')
  proxy='https://r.jina.ai/'+url
  r=S.get(proxy,timeout=60); r.raise_for_status()
  return extract_edeka_from_text(r.text,url,store,market_name)

def dedupe_history(history):
 out=[];seen=set()
 for h in sorted(history,key=lambda x:(x.get('date',''),x.get('price',0))):
  key=(h.get('date'),h.get('price'))
  if key not in seen:seen.add(key);out.append(h)
 return out

def period_is_current(p,today): return bool(p and p.get('valid_from')<=today<=p.get('valid_until'))
def period_is_new(p,old): return bool(p and (not old or (p.get('valid_from'),p.get('valid_until'))!=(old.get('valid_from'),old.get('valid_until'))))

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]}; today=datetime.now(timezone.utc).date().isoformat(); old_periods=data.get('validity',{})
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
 try: edeka_buch,edeka_buch_period=extract_edeka_market(EDEKA_BUCH,'EDEKA_BUCH','EDEKA Buch')
 except Exception as e: print('EDEKA Buch Abruf fehlgeschlagen:',e); edeka_buch=[]; edeka_buch_period=None
 try: edeka_haller,edeka_haller_period=extract_edeka_market(EDEKA_HALLER,'EDEKA_HALLER','E center Haller')
 except Exception as e: print('E center Haller Abruf fehlgeschlagen:',e); edeka_haller=[]; edeka_haller_period=None
 candidates={'REWE':(rewe,rewe_period,rewe_source),'GLOBUS':(globus,globus_period,globus_source),'EDEKA_BUCH':(edeka_buch,edeka_buch_period,EDEKA_BUCH),'EDEKA_HALLER':(edeka_haller,edeka_haller_period,EDEKA_HALLER)}; accepted={}; validity=dict(old_periods)
 for st,(items,period,src) in candidates.items():
  if period_is_current(period,today) and items:
   accepted[st]=items; validity[st]={**period,'source':src,'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds')}; print(st,'Zeitraum akzeptiert:',period,'neu=',period_is_new(period,old_periods.get(st)))
  else:
   accepted[st]=None; print(st,'nicht übernommen: Zeitraum fehlt/veraltet oder keine Angebote:',period,len(items))
 merged={}
 for old in data.get('products',[]):
  st=old.get('store') or 'REWE'; old['store']=st; pid=st.lower()+'-'+slug(old.get('name') or old.get('id',''))
  if not pid:continue
  old['id']=pid; old['history']=dedupe_history(old.get('history',[])); old['active']=period_is_current(validity.get(st),today); merged[pid]=old
 for st,items in accepted.items():
  if items is None: continue
  for item in merged.values():
   if item.get('store')==st:item['active']=False
  for o in items:
   pid=st.lower()+'-'+slug(o['name']); item=merged.get(pid)
   if item is None:item={'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'image':o.get('image',''),'store':st,'history':[]}; merged[pid]=item
   item.update({'name':o['name'],'quantity':o.get('quantity',''),'category':o.get('category','Angebot'),'store':st,'active':True,'last_seen':today,'valid_from':validity[st]['valid_from'],'valid_until':validity[st]['valid_until']})
   if o.get('image'):item['image']=o['image']
   obs={'date':validity[st]['valid_from'],'price':o['price']}
   if obs not in item['history']:item['history'].append(obs)
   item['history']=dedupe_history(item['history'])
 data['products']=[p for p in merged.values() if p.get('history')]; data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds'); data['validity']=validity; data['sources']={'REWE':rewe_source,'GLOBUS':globus_source,'GLOBUS_market_confirmation':GLOBUS_OFFICIAL,'EDEKA_BUCH':EDEKA_BUCH,'EDEKA_HALLER':EDEKA_HALLER}; data['last_import_count']={st:(len(v) if v is not None else 0) for st,v in accepted.items()}; data['last_import_count']['total']=sum(data['last_import_count'].values()); data['active_offer_count']=sum(1 for p in data['products'] if p.get('active') is True)
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print('Fertig:',data['active_offer_count'],'aktuelle Angebote; Archiv',len(data['products']))
if __name__=='__main__':main()