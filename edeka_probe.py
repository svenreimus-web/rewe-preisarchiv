import requests

# Temporary probe used to verify EDEKA's public market-offer endpoint from GitHub Actions.
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36','Accept':'application/json','Accept-Language':'de-DE,de;q=0.9'}
for label, mids in {'BUCH':['046253','2679098','1'],'HALLER':['042385','1']}.items():
    for mid in mids:
        url=f'https://www.edeka.de/eh/service/eh/offers?limit=200&marketId={mid}'
        try:
            r=requests.get(url,headers=HEADERS,timeout=30)
            print(label, mid, r.status_code, r.headers.get('content-type'))
            print(r.text[:1500].replace('\n',' '))
        except Exception as e:
            print(label, mid, 'ERROR', repr(e))