import io,requests
from pypdf import PdfReader
CATALOGS={
 'EDEKA_BUCH':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/pdf/complete.pdf',
 'EDEKA_HALLER':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_EC_Raunheim/blaetterkatalog/pdf/complete.pdf'
}
for store,url in CATALOGS.items():
 r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=40)
 print(store,'HTTP',r.status_code,r.headers.get('content-type'),len(r.content))
 if r.status_code!=200: continue
 reader=PdfReader(io.BytesIO(r.content))
 print(store,'PAGES',len(reader.pages))
 for i,p in enumerate(reader.pages[:5],1):
  txt=(p.extract_text() or '').replace('\x00',' ')
  print('PAGE',i,'TEXTLEN',len(txt))
  print(txt[:3500].replace('\n',' | '))
