import io,re,requests
from PIL import Image
import pytesseract

CATALOGS={
 'EDEKA_BUCH':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/large/bk_{}.jpg',
 'EDEKA_HALLER':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_EC_Raunheim/blaetterkatalog/large/bk_{}.jpg'
}
HEAD={'User-Agent':'Mozilla/5.0'}
PRICE=re.compile(r'(?<!\d)(\d{1,3})[,.](\d{2})(?!\d)')
NOISE=('edeka','gültig','prospekt','rabatt','aktion','app','payback','preis bei','grundpreis','pfand','seite','kw','www.','abbildung','sortiere selbst','diese woche')

def clean(s): return re.sub(r'\s+',' ',s).strip(' |:;,.–-')

def extract_page(img,page):
 d=pytesseract.image_to_data(img,lang='deu',config='--psm 11',output_type=pytesseract.Output.DICT)
 words=[]
 for i,t in enumerate(d['text']):
  t=clean(t)
  if not t or int(d['conf'][i] or -1)<25: continue
  words.append({'t':t,'x':d['left'][i],'y':d['top'][i],'w':d['width'][i],'h':d['height'][i]})
 out=[]
 for w in words:
  m=PRICE.search(w['t'])
  if not m: continue
  price=float(m.group(1)+'.'+m.group(2))
  if not (0.09<=price<=199.99): continue
  cx=w['x']+w['w']/2; py=w['y']
  near=[q for q in words if q is not w and abs((q['x']+q['w']/2)-cx)<300 and 0<py-(q['y']+q['h'])<180]
  near=sorted(near,key=lambda q:q['y'],reverse=True)[:12]
  text=clean(' '.join(q['t'] for q in reversed(near)))
  parts=[p.strip() for p in re.split(r'\s{2,}|\|',text) if p.strip()]
  name=clean(' '.join(parts[-2:])) if parts else text
  nl=name.casefold()
  if len(name)<4 or all(n in nl for n in ('preis','kg')) or any(nl==n for n in NOISE): continue
  out.append((page,price,name[:180],w['x'],w['y']))
 return out

for store,urlpat in CATALOGS.items():
 print('=== OCR',store,'===')
 allc=[]
 for page in range(1,6):
  r=requests.get(urlpat.format(page),headers=HEAD,timeout=25); print('PAGE',page,r.status_code,len(r.content)); r.raise_for_status()
  img=Image.open(io.BytesIO(r.content)).convert('RGB')
  c=extract_page(img,page); allc.extend(c)
  for row in c[:25]: print('CAND',row)
 print('TOTAL',store,len(allc))
