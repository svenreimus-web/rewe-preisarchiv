from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Legacy-Listen ohne Einheit erst nach Aufbau des Marken-Typ-Index migrieren
old="shoppingItems=Array.isArray(a)?a.filter(x=>x&&x.text).map(x=>({text:x.text,mode:x.mode||'auto',amount:Math.max(.1,Number(x.amount??x.qty??1)||1),unit:x.unit||recommendShoppingUnit(x.text)})):[];"
new="shoppingItems=Array.isArray(a)?a.filter(x=>x&&x.text).map(x=>({text:x.text,mode:x.mode||'auto',amount:Math.max(.1,Number(x.amount??x.qty??1)||1),unit:x.unit||null})):[];"
if old not in s: raise SystemExit('Legacy-Migration nicht gefunden')
s=s.replace(old,new,1)

# Kasten-Erkennung auch bei 20 x 0,5-l ohne explizites Wort Kasten
old="return raw.includes('kasten')||/\\b\\d+\\s*x\\s*\\d+(?:[.,]\\d+)?\\s*(?:l|ml)\\b/i.test(String(p.quantity||''))}"
new="return raw.includes('kasten')||/\\b\\d+\\s*[x×]\\s*\\d+(?:[.,]\\d+)?\\s*[- ]?\\s*(?:l|ml)\\b/i.test(String(p.quantity||''))}"
if old not in s: raise SystemExit('Kasten-RegEx nicht gefunden')
s=s.replace(old,new,1)

# Nach Markenindex Legacy-Einheiten sinnvoll setzen
old="shoppingTypeCache.clear();shopSuggestions.innerHTML=[...values]"
new="shoppingTypeCache.clear();let migrated=false;shoppingItems.forEach(x=>{if(!x.unit){x.unit=recommendShoppingUnit(x.text);migrated=true}});if(migrated)saveShoppingState();shopSuggestions.innerHTML=[...values]"
if old not in s: raise SystemExit('Suggestions-Migrationspunkt nicht gefunden')
s=s.replace(old,new,1)

# Cache nach Menge + Einheit; Auswahl nach Gesamtkosten der benötigten Packungen
old="function bestShoppingOffer(item,marketId){const key=`${marketId}|${item.mode||'auto'}|${norm(item.text)}`;if(shoppingOfferCache.has(key))return shoppingOfferCache.get(key);let best=null,bestScore=0,bestPrice=Infinity;for(const p of data){const m=shoppingMeta(p);if(m.market!==marketId)continue;const score=shoppingMatchScore(item,p);if(score>bestScore||(score===bestScore&&score>0&&m.price<bestPrice)){best=p;bestScore=score;bestPrice=m.price}}shoppingOfferCache.set(key,best);return best}"
new="function bestShoppingOffer(item,marketId){const key=`${marketId}|${item.mode||'auto'}|${norm(item.text)}|${item.unit||''}|${Number(item.amount)||1}`;if(shoppingOfferCache.has(key))return shoppingOfferCache.get(key);let best=null,bestScore=0,bestCost=Infinity;for(const p of data){const m=shoppingMeta(p);if(m.market!==marketId)continue;const score=shoppingMatchScore(item,p);if(score<=0)continue;const cost=m.price*shoppingOfferCount(item,p);if(score>bestScore||(score===bestScore&&cost<bestCost)){best=p;bestScore=score;bestCost=cost}}shoppingOfferCache.set(key,best);return best}"
if old not in s: raise SystemExit('bestShoppingOffer nicht gefunden')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Mengen-/Einheiten-Cache und Gesamtkostenvergleich korrigiert')
