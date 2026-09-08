import requests

CATALOGS={
 'BUCH':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_ED_ABH/blaetterkatalog/',
 'HALLER':'https://blaetterkatalog.edeka.de/SUEDWEST/MG_328_EC_Raunheim/blaetterkatalog/'
}
HEAD={'User-Agent':'Mozilla/5.0','Accept':'*/*'}
CANDIDATES=['','index.html','config.js','data.js','pages.js','search.json','search.xml','text.xml','blaetterkatalog.pdf','download.pdf','pdf/blaetterkatalog.pdf','js/config.js','js/data.js','assets/config.js']
for label,base in CATALOGS.items():
 print('===',label,'===')
 for rel in CANDIDATES:
  try:
   r=requests.get(base+rel,headers=HEAD,timeout=20,allow_redirects=True)
   print('META',rel or '/',r.status_code,r.headers.get('content-type'),len(r.content),r.url)
   if r.status_code==200 and ('text' in (r.headers.get('content-type') or '') or 'json' in (r.headers.get('content-type') or '') or 'javascript' in (r.headers.get('content-type') or '')):
    print(r.text[:700].replace('\n',' '))
  except Exception as e: print('METAERR',rel,repr(e))
 count=0
 for i in range(1,61):
  try:
   r=requests.get(base+f'large/bk_{i}.jpg',headers=HEAD,timeout=20)
   if r.status_code==200 and len(r.content)>1000:
    count=i
    if i in (1,2,3): print('PAGE',i,r.status_code,r.headers.get('content-type'),len(r.content))
   else:
    print('STOP',i,r.status_code,len(r.content)); break
  except Exception as e:
   print('PAGEERR',i,repr(e)); break
 print('PAGES_CONTIG',count)
