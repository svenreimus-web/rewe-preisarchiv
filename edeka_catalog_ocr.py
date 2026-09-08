import io,requests
from pypdf import PdfReader
URL='https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/pdf/complete.pdf'
r=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=60); r.raise_for_status()
reader=PdfReader(io.BytesIO(r.content))
for n in (1,2,4,5,6,7):
 p=reader.pages[n-1]
 try: txt=p.extract_text(extraction_mode='layout') or ''
 except TypeError: txt=p.extract_text() or ''
 print('\n===== PAGE',n,'=====')
 print(txt[:10000])
