import io,requests
from pypdf import PdfReader
URL='https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/pdf/complete.pdf'
r=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=60); r.raise_for_status()
p=PdfReader(io.BytesIO(r.content)).pages[4]
fr=[]
def visitor(text,cm,tm,font_dict,font_size):
 t=(text or '').replace('\n',' ').strip()
 if t: fr.append((round(tm[4],1),round(tm[5],1),round(float(font_size or 0),1),t))
p.extract_text(visitor_text=visitor)
for x,y,s,t in sorted(fr,key=lambda z:(-z[1],z[0])):
 if y>30:
  print(f'{x:7.1f} {y:7.1f} {s:5.1f} | {t}')
