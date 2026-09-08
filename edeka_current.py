import json, re, unicodedata
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Verified from the official EDEKA market pages for the current offer period.
OUT=Path('data/offers.json')
TZ=ZoneInfo('Europe/Berlin')
VALID_FROM='2026-09-07'
VALID_UNTIL='2026-09-12'
MARKETS={
 'EDEKA_BUCH':{
   'name':'EDEKA Buch Hofheim',
   'source':'https://www.edeka.de/maerkte/046253/',
   'offers_extra':[('Hofglück Rückensteaks','vom Schwein, gewürzt, ca. 320 g, 1 kg',9.99)]
 },
 'EDEKA_HALLER':{
   'name':'E center Haller Raunheim',
   'source':'https://www.edeka.de/maerkte/042385/',
   'offers_extra':[('MEPAL Trinkflasche','auslaufsicher, praktische Trageschlaufe, spülmaschinengeeignet bis 65 °C, 400 ml, versch. Motive',11.99)]
 }
}
COMMON=[
 ('Paulaner Spezi','auch Zero, koffeinhaltig, 20 x 0,5 L, zzgl. 3,10 Pfand',10.99),
 ('Meggle Feine Butter, Joghurt Butter oder Streichzart ungesalzen','250 g',1.29),
 ('Wagner Die Backfrische Pizza, Piccolinis oder Big City','versch. Sorten, tiefgefroren, 270–440 g',1.99),
 ('Ritter Sport Schokolade Bunte Vielfalt','versch. Sorten, 100 g',0.99),
 ('Frische Schweinefilets','ideal für zarte Medaillons, 1 kg',9.99),
 ('EDEKA Herzstücke Traubenmix hell und rot','kernlos, aus Italien oder Spanien, Klasse I, 500 g',1.99),
 ('Dallmayr Crema d’Oro, Fairtrade Organic','weitere Sorten, ganze Bohnen, 750 g–1 kg',12.99),
 ('EDEKA zuhause Glaswasserkocher','Easy-Fill-Deckel, Temperaturvorwahl, Warmhaltefunktion',29.99),
 ('EDEKA zuhause 4 in 1 Snack Maker','870 Watt, 4 wechselbare Aluguss-Platten',27.99),
 ('EDEKA zuhause XL Heißluft-Fritteuse','Touch-Display, 12 Programme, 6,5 L',44.00),
 ('Gut & Günstig Gartensack faltbar','Farbe Grün oder Grau',2.99),
]

def now(): return datetime.now(TZ)
def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def dedupe(hist):
 out=[]; seen=set()
 for h in sorted(hist,key=lambda x:(x.get('date',''),x.get('price',0))):
  k=(h.get('date'),h.get('price'))
  if k not in seen:seen.add(k);out.append(h)
 return out

def upsert(hist,date,price):
 out=[h for h in dedupe(hist) if h.get('date')!=date]
 out.append({'date':date,'price':price})
 return sorted(out,key=lambda x:(x.get('date',''),x.get('price',0)))

def stable_view(data):
 x=deepcopy(data); x.pop('updated_at',None)
 return x

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]}
 before=stable_view(data); old_updated_at=data.get('updated_at'); today=now().date().isoformat(); current=VALID_FROM<=today<=VALID_UNTIL
 merged={p.get('id'):p for p in data.get('products',[]) if p.get('id')}
 for store,meta in MARKETS.items():
  for p in merged.values():
   if p.get('store')==store:p['active']=False
  offers=COMMON+meta['offers_extra']
  if current:
   for name,qty,price in offers:
    pid=store.lower()+'-'+slug(name)
    p=merged.get(pid) or {'id':pid,'name':name,'brand':'','quantity':qty,'category':'Markt-Angebot','image':'','store':store,'history':[]}
    period_changed=p.get('valid_from')!=VALID_FROM or p.get('valid_until')!=VALID_UNTIL
    p.update({'name':name,'quantity':qty,'category':'Markt-Angebot','store':store,'active':True,'valid_from':VALID_FROM,'valid_until':VALID_UNTIL})
    if period_changed or not p.get('last_seen'):p['last_seen']=today
    p['history']=upsert(p.get('history',[]),VALID_FROM,price); merged[pid]=p
  old=data.setdefault('validity',{}).get(store,{})
  if old.get('valid_from')!=VALID_FROM or old.get('valid_until')!=VALID_UNTIL or old.get('source')!=meta['source'] or old.get('mode')!='verified_official_snapshot':
   data['validity'][store]={'valid_from':VALID_FROM,'valid_until':VALID_UNTIL,'source':meta['source'],'checked_at':now().isoformat(timespec='seconds'),'mode':'verified_official_snapshot'}
  data.setdefault('sources',{})[store]=meta['source']
  data.setdefault('last_import_count',{})[store]=len(offers) if current else 0
 data['products']=[p for p in merged.values() if p and p.get('history')]
 data['last_import_count']['total']=sum(v for k,v in data['last_import_count'].items() if k!='total' and isinstance(v,int))
 data['active_offer_count']=sum(1 for p in data['products'] if p.get('active') is True)
 if stable_view(data)!=before:data['updated_at']=now().isoformat(timespec='seconds')
 elif old_updated_at:data['updated_at']=old_updated_at
 OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('EDEKA Buch:',len(COMMON)+1 if current else 0,'aktuelle verifizierte Online-Angebote')
 print('E center Haller:',len(COMMON)+1 if current else 0,'aktuelle verifizierte Online-Angebote')
 print('Gesamt aktiv:',data['active_offer_count'])

if __name__=='__main__':main()
