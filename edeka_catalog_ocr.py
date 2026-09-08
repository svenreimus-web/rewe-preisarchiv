import io,re,requests
from PIL import Image
import pytesseract
URL='https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/large/bk_1.jpg'
r=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=25); r.raise_for_status()
img=Image.open(io.BytesIO(r.content)).convert('RGB')
d=pytesseract.image_to_data(img,lang='deu',config='--psm 11',output_type=pytesseract.Output.DICT)
for i,t in enumerate(d['text']):
 t=(t or '').strip()
 try: conf=float(d['conf'][i])
 except: conf=-1
 if t and conf>=15 and d['height'][i]>=28 and (re.search(r'\d',t) or d['height'][i]>=55):
  print('TOK',repr(t),'x',d['left'][i],'y',d['top'][i],'w',d['width'][i],'h',d['height'][i],'conf',round(conf,1))
