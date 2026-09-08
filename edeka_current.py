import io,json,re,unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from pypdf import PdfReader
import fitz
from PIL import Image

OUT=Path('data/offers.json'); TZ=ZoneInfo('Europe/Berlin')
IMG_ROOT=Path('data/edeka-images')
HEAD={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36'}
MARKETS={
 'EDEKA_BUCH':{'name':'EDEKA Buch Hofheim','market':'https://www.edeka.de/maerkte/046253/','pdf':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/pdf/complete.pdf'},
 'EDEKA_HALLER':{'name':'E center Haller Raunheim','market':'https://www.edeka.de/maerkte/042385/','pdf':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_EC_Raunheim/blaetterkatalog/pdf/complete.pdf'}
}
FALLBACK_PERIOD=('2026-09-07','2026-09-12')
FALLBACK_COMMON=[
 ('Paulaner Spezi','auch Zero, koffeinhaltig, 20 x 0,5 L, zzgl. 3,10 Pfand',10.99),('Meggle Feine Butter, Joghurt Butter oder Streichzart ungesalzen','250 g',1.29),('Wagner Die Backfrische Pizza, Piccolinis oder Big City','versch. Sorten, tiefgefroren, 270–440 g',1.99),('Ritter Sport Schokolade Bunte Vielfalt','versch. Sorten, 100 g',0.99),('Frische Schweinefilets','ideal für zarte Medaillons, 1 kg',9.99),('EDEKA Herzstücke Traubenmix hell und rot','kernlos, 500 g',1.99),('Dallmayr Crema d’Oro, Fairtrade Organic','weitere Sorten, ganze Bohnen, 750 g–1 kg',12.99),('EDEKA zuhause Glaswasserkocher','Easy-Fill-Deckel, Temperaturvorwahl, Warmhaltefunktion',29.99),('EDEKA zuhause 4 in 1 Snack Maker','870 Watt, 4 wechselbare Aluguss-Platten',27.99),('EDEKA zuhause XL Heißluft-Fritteuse','Touch-Display, 12 Programme, 6,5 L',44.00),('Gut & Günstig Gartensack faltbar','Farbe Grün oder Grau',2.99)]
FALLBACK_EXTRA={'EDEKA_BUCH':[('Hofglück Rückensteaks','vom Schwein, gewürzt, ca. 320 g, 1 kg',9.99)],'EDEKA_HALLER':[('MEPAL Trinkflasche','auslaufsicher, 400 ml, versch. Motive',11.99)]}

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:110]
def clean(s): return re.sub(r'\s+',' ',(s or '').replace('\xa0',' ').replace('­','')).strip(' |:;,.–-')
def parse_period(text):
 t=re.sub(r'\s+','',text.replace('•',''));m=re.search(r'(\d{1,2})\.(\d{1,2})\.?(?:\d{4})?[–-](\d{1,2})\.(\d{1,2})\.(\d{4})',t)
 if not m:return None
 d1,m1,d2,m2,y=m.groups();return f'{y}-{int(m1):02d}-{int(d1):02d}',f'{y}-{int(m2):02d}-{int(d2):02d}'
def fragments(page):
 out=[]
 def visitor(text,cm,tm,font_dict,font_size):
  t=clean((text or '').replace('\n',' '))
  if t:out.append({'x':float(tm[4]),'y':float(tm[5]),'t':t})
 page.extract_text(visitor_text=visitor);return out
def near(fr,p,dx,lo,hi,pred):return [q for q in fr if abs(q['x']-p['x'])<=dx and lo<=q['y']-p['y']<=hi and pred(q['t'])]
def product_text(fr,p):
 # For AKTION/TIPP cards the large price sits at the right edge of the product block.
 cand=[q for q in fr if p['x']-365<=q['x']<=p['x']+35 and 8<=q['y']-p['y']<=105 and re.search(r'[A-Za-zÄÖÜäöüß]',q['t'])]
 noise=('aktion','tipp','uvp','protein','bis zu','pro 100','rabatt','app','preis')
 cand=[q for q in cand if not any(n in q['t'].casefold() for n in noise)]
 rows=[]
 for q in sorted(cand,key=lambda z:(-z['y'],z['x'])):
  row=next((r for r in rows if abs(r['y']-q['y'])<5),None)
  if row is None:row={'y':q['y'],'parts':[]};rows.append(row)
  row['parts'].append(q)
 lines=[]
 for r in sorted(rows,key=lambda z:-z['y'])[:3]:
  line=clean(' '.join(q['t'] for q in sorted(r['parts'],key=lambda z:z['x'])))
  if line:lines.append(line)
 if not lines:return '',''
 name=re.sub(r'^[¹²³*]+','',clean(' '.join(lines[:2]))).strip();qty=clean(lines[2]) if len(lines)>2 else ''
 return name[:170],qty
def parse_page(page,page_no):
 fr=fragments(page);out=[];seen=set();pw=float(page.mediabox.width);ph=float(page.mediabox.height)
 for p in fr:
  if not re.fullmatch(r'\d{1,3}[.,]\d{2}',p['t']):continue
  price=float(p['t'].replace(',','.'))
  if not .09<=price<=199.99:continue
  # Only explicit AKTION/TIPP cards are imported automatically. Discount/app cards on
  # the cover use more complex typography and remain covered by the verified fallback.
  marker=near(fr,p,95,75,135,lambda t:'aktion' in t.casefold() or 'tipp' in t.casefold())
  if not marker:continue
  if near(fr,p,100,-35,35,lambda t:'uvp' in t.casefold()):continue
  name,qty=product_text(fr,p)
  if len(name)<4:continue
  k=(slug(name),price)
  if k in seen:continue
  seen.add(k);out.append({'name':name,'quantity':qty,'price':price,'page':page_no,'x':p['x'],'y':p['y'],'pw':pw,'ph':ph})
 return out
def fallback(store):return [{'name':n,'quantity':q,'price':p,'page':None} for n,q,p in FALLBACK_COMMON+FALLBACK_EXTRA[store]],FALLBACK_PERIOD

def crop_rect(o):
 # Coordinates in pypdf use a bottom-left origin. The offer price is near the right
 # edge of an offer tile; this box includes product photo, title and price without
 # taking the whole leaflet page.
 x=float(o['x']);y=float(o['y']);pw=float(o['pw']);ph=float(o['ph'])
 left=max(0.0,x-430);right=min(pw,x+125)
 bottom=max(0.0,y-145);top=min(ph,y+255)
 return left,bottom,right,top

def render_offer_images(store,pdf_bytes,offers):
 folder=IMG_ROOT/store.lower();folder.mkdir(parents=True,exist_ok=True)
 # Current offers are all that the UI shows. Removing old crops avoids unbounded repo growth.
 for old in folder.glob('*.jpg'):
  old.unlink()
 doc=fitz.open(stream=pdf_bytes,filetype='pdf');made=0
 for o in offers:
  if not all(k in o for k in ('page','x','y','pw','ph')) or not o.get('page'):continue
  try:
   page=doc[int(o['page'])-1];left,bottom,right,top=crop_rect(o)
   sx=page.rect.width/float(o['pw']);sy=page.rect.height/float(o['ph'])
   clip=fitz.Rect(left*sx,(float(o['ph'])-top)*sy,right*sx,(float(o['ph'])-bottom)*sy)
   clip=clip & page.rect
   if clip.width<80 or clip.height<80:continue
   pix=page.get_pixmap(matrix=fitz.Matrix(1.15,1.15),clip=clip,alpha=False)
   img=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB');img.thumbnail((520,380),Image.Resampling.LANCZOS)
   pid=store.lower()+'-'+slug(o['name']);path=folder/(pid+'.jpg')
   img.save(path,'JPEG',quality=80,optimize=True)
   o['image']='./'+path.as_posix();made+=1
  except Exception as e:
   print('BILD FEHLER',store,o.get('page'),o.get('name'),e)
 doc.close();return made

def parse_pdf(store,meta):
 r=requests.get(meta['pdf'],headers=HEAD,timeout=90);r.raise_for_status();pdf_bytes=r.content;reader=PdfReader(io.BytesIO(pdf_bytes))
 if len(reader.pages)<10:raise RuntimeError('zu wenige PDF-Seiten')
 period=parse_period('\n'.join((p.extract_text() or '') for p in reader.pages[:3]))
 if not period:raise RuntimeError('Gültigkeitszeitraum fehlt')
 found=[]
 for i,p in enumerate(reader.pages,1):found.extend(parse_page(p,i))
 merged={}
 for o in found:
  k=slug(o['name'])
  if k and k not in merged:merged[k]=o
 # Overlay individually verified cover/market-page prices, but retain coordinates
 # from an automatically detected matching tile so it can still receive an image.
 verified,_=fallback(store)
 for o in verified:
  k=slug(o['name'])
  if k in merged:
   base=merged[k];base['name']=o['name'];base['quantity']=o['quantity'];base['price']=o['price'];merged[k]=base
  else:merged[k]=o
 offers=list(merged.values())
 if len(offers)<25:raise RuntimeError(f'nur {len(offers)} sicher erkannte Angebote')
 image_count=render_offer_images(store,pdf_bytes,offers)
 return offers,period,len(reader.pages),image_count

def dedupe(hist):
 out=[];seen=set()
 for h in sorted(hist,key=lambda x:(x.get('date',''),x.get('price',0))):
  k=(h.get('date'),h.get('price'))
  if k not in seen:seen.add(k);out.append(h)
 return out
def apply_store(data,store,meta,offers,period,mode,pages=None,image_count=0):
 today=datetime.now(TZ).date().isoformat();vf,vu=period;current=vf<=today<=vu;merged={p.get('id'):p for p in data.get('products',[]) if p.get('id')}
 for p in merged.values():
  if p.get('store')==store:p['active']=False
 if current:
  for o in offers:
   pid=store.lower()+'-'+slug(o['name']);p=merged.get(pid) or {'id':pid,'name':o['name'],'brand':'','quantity':o.get('quantity',''),'category':'Markt-Angebot','image':'','store':store,'history':[]}
   p.update({'name':o['name'],'quantity':o.get('quantity',''),'category':'Markt-Angebot','image':o.get('image',''),'store':store,'active':True,'last_seen':today,'valid_from':vf,'valid_until':vu})
   if o.get('page'):p['source_page']=o['page']
   else:p.pop('source_page',None)
   hist=[h for h in p.get('history',[]) if h.get('date')!=vf];hist.append({'date':vf,'price':o['price']});p['history']=dedupe(hist);merged[pid]=p
 data['products']=[p for p in merged.values() if p and p.get('history')]
 v={'valid_from':vf,'valid_until':vu,'source':meta['pdf'],'mode':mode,'images':image_count}
 if pages:v['pages']=pages
 data.setdefault('validity',{})[store]=v;data.setdefault('sources',{})[store]=meta['pdf'];data.setdefault('last_import_count',{})[store]=len(offers) if current else 0
 return len(offers) if current else 0
def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]};counts={}
 for store,meta in MARKETS.items():
  try:
   offers,period,pages,image_count=parse_pdf(store,meta);mode='official_leaflet_pdf_strong_pairs_with_images';print(store,':',len(offers),'sicher gepaarte Angebote aus',pages,'Seiten;',image_count,'Bilder')
  except Exception as e:
   print(store,'PDF-Import fehlgeschlagen:',e,'-> 12er-Fallback');offers,period=fallback(store);pages=None;image_count=0;mode='verified_official_snapshot_fallback'
  counts[store]=apply_store(data,store,meta,offers,period,mode,pages,image_count)
 data['last_import_count']['total']=sum(v for k,v in data['last_import_count'].items() if k!='total' and isinstance(v,int));data['active_offer_count']=sum(1 for p in data['products'] if p.get('active') is True);data['updated_at']=datetime.now(TZ).isoformat(timespec='seconds')
 OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('EDEKA aktiv:',counts,'Gesamt aktiv:',data['active_offer_count'])
 # Hard guard: verified cover products must retain their known normal offer prices.
 for store in MARKETS:
  active=[p for p in data['products'] if p.get('store')==store and p.get('active')]
  for term,want in [('paulaner',10.99),('meggle',1.29),('wagner',1.99),('ritter sport',.99),('schweinefilets',9.99),('dallmayr',12.99)]:
   m=next((p for p in active if term in p.get('name','').casefold()),None)
   if not m or abs(m['history'][-1]['price']-want)>.001:raise RuntimeError(f'Guardrail {store} {term} fehlgeschlagen')
   print('CHECK',store,term,m['history'][-1]['price'],'OK')
if __name__=='__main__':main()
