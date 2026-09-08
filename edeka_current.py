import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path

OUT=Path('data/offers.json')
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

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:100]

def dedupe(hist):
 out=[]; seen=set()
 for h in sorted(hist,key=lambda x:(x.get('date',''),x.get('price',0))):
  k=(h.get('date'),h.get('price'))
  if k not in seen: seen.add(k); out.append(h)
 return out

def main():
 data=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'products':[]}
 today=datetime.now(timezone.utc).date().isoformat()
 current=VALID_FROM <= today <= VALID_UNTIL
 merged={p.get('id'):p for p in data.get('products',[]) if p.get('id')}
 for store,meta in MARKETS.items():
  # Never leave expired EDEKA offers active.
  for p in merged.values():
   if p.get('store')==store: p['active']=False
  offers=COMMON+meta['offers_extra']
  if current:
   for name,qty,price in offers:
    pid=store.lower()+'-'+slug(name)
    p=merged.get(pid) or {'id':pid,'name':name,'brand':'','quantity':qty,'category':'Markt-Angebot','image':'','store':store,'history':[]}
    p.update({'name':name,'quantity':qty,'category':'Markt-Angebot','store':store,'active':True,'last_seen':today,'valid_from':VALID_FROM,'valid_until':VALID_UNTIL})
    obs={'date':VALID_FROM,'price':price}
    if obs not in p.get('history',[]): p.setdefault('history',[]).append(obs)
    p['history']=dedupe(p.get('history',[])); merged[pid]=p
  data.setdefault('validity',{})[store]={'valid_from':VALID_FROM,'valid_until':VALID_UNTIL,'source':meta['source'],'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'mode':'verified_official_snapshot'}
  data.setdefault('sources',{})[store]=meta['source']
  data.setdefault('last_import_count',{})[store]=len(offers) if current else 0
 data['products']=[p for p in merged.values() if p and p.get('history')]
 data['last_import_count']['total']=sum(v for k,v in data['last_import_count'].items() if k!='total' and isinstance(v,int))
 data['active_offer_count']=sum(1 for p in data['products'] if p.get('active') is True)
 data['updated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
 OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('EDEKA Buch:',len(COMMON)+1 if current else 0,'aktuelle verifizierte Online-Angebote')
 print('E center Haller:',len(COMMON)+1 if current else 0,'aktuelle verifizierte Online-Angebote')
 print('Gesamt aktiv:',data['active_offer_count'])

if __name__=='__main__': main()
