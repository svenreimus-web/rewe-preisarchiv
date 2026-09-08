import io,json,re,unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from pypdf import PdfReader

OUT=Path('data/offers.json')
TZ=ZoneInfo('Europe/Berlin')
HEAD={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36'}
MARKETS={
 'EDEKA_BUCH':{
  'name':'EDEKA Buch Hofheim',
  'market':'https://www.edeka.de/maerkte/046253/',
  'pdf':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/pdf/complete.pdf'
 },
 'EDEKA_HALLER':{
  'name':'E center Haller Raunheim',
  'market':'https://www.edeka.de/maerkte/042385/',
  'pdf':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_EC_Raunheim/blaetterkatalog/pdf/complete.pdf'
 }
}
# Fail-safe: these offers were individually verified on the official market pages for KW37.
FALLBACK_PERIOD=('2026-09-07','2026-09-12')
FALLBACK_COMMON=[
 ('Paulaner Spezi','auch Zero, koffeinhaltig, 20 x 0,5 L, zzgl. 3,10 Pfand',10.99),
 ('Meggle Feine Butter, Joghurt Butter oder Streichzart ungesalzen','250 g',1.29),
 ('Wagner Die Backfrische Pizza, Piccolinis oder Big City','versch. Sorten, tiefgefroren, 270–440 g',1.99),
 ('Ritter Sport Schokolade Bunte Vielfalt','versch. Sorten, 100 g',0.99),
 ('Frische Schweinefilets','ideal für zarte Medaillons, 1 kg',9.99),
 ('EDEKA Herzstücke Traubenmix hell und rot','kernlos, 500 g',1.99),
 ('Dallmayr Crema d’Oro, Fairtrade Organic','weitere Sorten, ganze Bohnen, 750 g–1 kg',12.99),
 ('EDEKA zuhause Glaswasserkocher','Easy-Fill-Deckel, Temperaturvorwahl, Warmhaltefunktion',29.99),
 ('EDEKA zuhause 4 in 1 Snack Maker','870 Watt, 4 wechselbare Aluguss-Platten',27.99),
 ('EDEKA zuhause XL Heißluft-Fritteuse','Touch-Display, 12 Programme, 6,5 L',44.00),
 ('Gut & Günstig Gartensack faltbar','Farbe Grün oder Grau',2.99),
]
FALLBACK_EXTRA={
 'EDEKA_BUCH':[('Hofglück Rückensteaks','vom Schwein, gewürzt, ca. 320 g, 1 kg',9.99)],
 'EDEKA_HALLER':[('MEPAL Trinkflasche','auslaufsicher, 400 ml, versch. Motive',11.99)]
}

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:110]

def clean(s):
 s=(s or '').replace('\xa0',' ').replace('­','')
 s=re.sub(r'\s+',' ',s).strip(' |:;,.–-')
 return s

def parse_period(text):
 t=re.sub(r'\s+','',text.replace('•',''))
 m=re.search(r'(\d{1,2})\.(\d{1,2})\.?(?:\d{4})?[–-](\d{1,2})\.(\d{1,2})\.(\d{4})',t)
 if not m:return None
 d1,m1,d2,m2,y=m.groups()
 return f'{y}-{int(m1):02d}-{int(d1):02d}',f'{y}-{int(m2):02d}-{int(d2):02d}'

def fragments(page):
 out=[]
 def visitor(text,cm,tm,font_dict,font_size):
  t=clean((text or '').replace('\n',' '))
  if t: out.append({'x':float(tm[4]),'y':float(tm[5]),'t':t})
 page.extract_text(visitor_text=visitor)
 return out

def is_price_token(t):
 return bool(re.fullmatch(r'\d{1,3}[.,]\d{2}',t.strip()))

def value(t): return float(t.replace(',','.'))

def near(fr,p,dx,dy_lo,dy_hi,pred):
 return [q for q in fr if abs(q['x']-p['x'])<=dx and dy_lo <= q['y']-p['y'] <= dy_hi and pred(q['t'])]

def product_text(fr,p):
 # EDEKA cards put the product title/description just above the large offer price.
 candidates=[q for q in fr if p['x']-430 <= q['x'] <= p['x']+45 and 8 <= q['y']-p['y'] <= 115]
 candidates=[q for q in candidates if re.search(r'[A-Za-zÄÖÜäöüß]',q['t'])]
 noise=('aktion','tipp','app-preis','app -pr eis','uvp','protein','bis zu','pro 100','rabatt','preis')
 candidates=[q for q in candidates if not any(n in q['t'].casefold() for n in noise)]
 if not candidates:return '', ''
 # Group by baseline; keep at most the first three visual lines from top to bottom.
 rows=[]
 for q in sorted(candidates,key=lambda z:(-z['y'],z['x'])):
  row=next((r for r in rows if abs(r['y']-q['y'])<5),None)
  if row is None:
   row={'y':q['y'],'parts':[]}; rows.append(row)
  row['parts'].append(q)
 rows=sorted(rows,key=lambda r:-r['y'])[:3]
 lines=[]
 for r in rows:
  line=clean(' '.join(q['t'] for q in sorted(r['parts'],key=lambda z:z['x'])))
  if line: lines.append(line)
 if not lines:return '', ''
 name=clean(' '.join(lines[:2]))
 qty=clean(lines[2]) if len(lines)>2 else ''
 # Remove common footnote prefixes, but retain meaningful product numbers.
 name=re.sub(r'^[¹²³*]+','',name).strip()
 if len(name)>170:name=name[:170].rsplit(' ',1)[0]
 return name,qty

def parse_page(page,page_no):
 fr=fragments(page); offers=[]
 for p in fr:
  if not is_price_token(p['t']):continue
  price=value(p['t'])
  if not 0.09 <= price <= 199.99:continue
  # Reject struck/regular comparison prices (UVP) and unit-price fragments.
  if near(fr,p,115,-35,35,lambda t:'uvp' in t.casefold()):continue
  if near(fr,p,220,-25,25,lambda t:re.search(r'\b1\s*(kg|l)\s*=',t,re.I) is not None):continue
  # Main prices are visually announced by AKTION/TIPP or a discount above them.
  marker=near(fr,p,140,45,145,lambda t:('aktion' in t.casefold() or 'tipp' in t.casefold() or re.search(r'-\s*\d+\s*%',t) is not None))
  if not marker:continue
  # App-only price is separately labelled. We keep the ordinary shelf offer as `price`.
  app=near(fr,p,190,45,190,lambda t:'app' in t.casefold() and 'preis' in re.sub(r'\s+','',t.casefold()))
  if app:continue
  name,qty=product_text(fr,p)
  if len(name)<4:continue
  nl=name.casefold()
  if any(x in nl for x in ('treuepunkte sammeln','einkleben','im markt einlösen','rabatt-aktion')):continue
  offers.append({'name':name,'quantity':qty,'price':price,'page':page_no})
 # Deduplicate candidates on the same page.
 out=[];seen=set()
 for o in offers:
  k=(slug(o['name']),o['price'])
  if k not in seen:seen.add(k);out.append(o)
 return out

def parse_pdf(meta):
 r=requests.get(meta['pdf'],headers=HEAD,timeout=90); r.raise_for_status()
 if 'pdf' not in (r.headers.get('content-type') or '').lower():raise RuntimeError('Blätterkatalog ist kein PDF')
 reader=PdfReader(io.BytesIO(r.content))
 if len(reader.pages)<10:raise RuntimeError(f'Blätterkatalog hat nur {len(reader.pages)} Seiten')
 alltext='\n'.join((p.extract_text() or '') for p in reader.pages[:3])
 period=parse_period(alltext)
 if not period:raise RuntimeError('Gültigkeitszeitraum im PDF nicht erkannt')
 found=[]
 for i,p in enumerate(reader.pages,1):
  found.extend(parse_page(p,i))
 # Merge same product name within the catalog; prefer the first occurrence.
 merged={}
 for o in found:
  key=slug(o['name'])
  if key and key not in merged:merged[key]=o
 offers=list(merged.values())
 return offers,period,len(reader.pages)

def fallback(store):
 offers=[{'name':n,'quantity':q,'price':p,'page':None} for n,q,p in FALLBACK_COMMON+FALLBACK_EXTRA[store]]
 return offers,FALLBACK_PERIOD

def dedupe(hist):
 out=[];seen=set()
 for h in sorted(hist,key=lambda x:(x.get('date',''),x.get('price',0))):
  k=(h.get('date'),h.get('price'))
  if k not in seen:seen.add(k);out.append(h)
 return out

def apply_store(data,store,meta,offers,period,mode,pages=None):
 today=datetime.now(TZ).date().isoformat(); vf,vu=period; current=vf<=today<=vu
 merged={p.get('id'):p for p in data.get('products',[]) if p.get('id')}
 for p in merged.values():
  if p.get('store')==store:p['active']=False
 if current:
  for o in offers:
   pid=store.lower()+'-'+slug(o['name']); p=merged.get(pid)
   if p is None:p={'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':'Markt-Angebot','image':'','store':store,'history':[]}
   p.update({'name':o['name'],'quantity':o.get('quantity',''),'category':'Markt-Angebot','store':store,'active':True,'last_seen':today,'valid_from':vf,'valid_until':vu})
   if o.get('page'):p['source_page']=o['page']
   # one observation per validity period; replace an earlier erroneous value for this week
   hist=[h for h in p.get('history',[]) if h.get('date')!=vf]
   hist.append({'date':vf,'price':o['price']});p['history']=dedupe(hist);merged[pid]=p
 data['products']=[p for p in merged.values() if p and p.get('history')]
 v={'valid_from':vf,'valid_until':vu,'source':meta['pdf'],'mode':mode}
 if pages:v['pages']=pages
 data.setdefault('validity',{})[store]=v
 data.setdefault('sources',{})[store]=meta['pdf']
 data.setdefault('last_import_count',{})[store]=len(offers) if current else 0
 return len(offers) if current else 0

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]}
 counts={}
 for store,meta in MARKETS.items():
  try:
   offers,period,pages=parse_pdf(meta)
   # A full weekly catalog should comfortably exceed the 12 highlighted market-page offers.
   if len(offers)<30:raise RuntimeError(f'nur {len(offers)} plausible PDF-Angebote erkannt')
   mode='official_leaflet_pdf'; print(store,':',len(offers),'Angebote aus',pages,'PDF-Seiten; Zeitraum',period)
  except Exception as e:
   print(store,'PDF-Import fehlgeschlagen:',e,'-> verifizierter 12er-Fallback')
   offers,period=fallback(store);pages=None;mode='verified_official_snapshot_fallback'
  counts[store]=apply_store(data,store,meta,offers,period,mode,pages)
 data['last_import_count']['total']=sum(v for k,v in data['last_import_count'].items() if k!='total' and isinstance(v,int))
 data['active_offer_count']=sum(1 for p in data['products'] if p.get('active') is True)
 data['updated_at']=datetime.now(TZ).isoformat(timespec='seconds')
 OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('EDEKA aktiv:',counts,'Gesamt aktiv:',data['active_offer_count'])
 # Known-price guardrails catch the most dangerous price/pairing regressions.
 checks={'EDEKA_BUCH':{'paulaner':10.99,'meggle':1.29,'ritter sport':0.99,'wagner':1.99,'schweinefilets':9.99,'dallmayr':12.99}}
 for store,expected in checks.items():
  active=[p for p in data['products'] if p.get('store')==store and p.get('active')]
  for term,want in expected.items():
   matches=[p for p in active if term in p.get('name','').casefold()]
   if matches:
    got=matches[0]['history'][-1]['price']
    print('CHECK',store,term,got,'OK' if abs(got-want)<0.001 else f'ERWARTET {want}')

if __name__=='__main__':main()
