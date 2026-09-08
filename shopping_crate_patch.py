from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Kleinkinder ergänzen
s=s.replace('<option value="4-6">4–6 Jahre</option>', '<option value="1-3">1–3 Jahre</option><option value="4-6">4–6 Jahre</option>', 1)
s=s.replace("['4-6','7-9','10-12','13-14','15-18'].includes(h.childAge)", "['1-3','4-6','7-9','10-12','13-14','15-18'].includes(h.childAge)", 1)
s=s.replace("const CHILD_WEEKLY_WATER_ML={'4-6':800", "const CHILD_WEEKLY_WATER_ML={'1-3':820,'4-6':800", 1)
s=s.replace("const CHILD_MEAL_G={'4-6':{pasta:70,meat:70,cheese:20}", "const CHILD_MEAL_G={'1-3':{pasta:50,meat:50,cheese:15},'4-6':{pasta:70,meat:70,cheese:20}", 1)

# Marken -> Produktart Index, damit z.B. Krombacher automatisch Kasten wird
old="const shoppingOfferCache=new Map(),shoppingTypeCache=new Map(),shoppingMetaCache=new WeakMap();"
new="const shoppingOfferCache=new Map(),shoppingTypeCache=new Map(),shoppingMetaCache=new WeakMap(),shoppingBrandTypeMap=new Map();"
if old not in s: raise SystemExit('Cache-Deklaration nicht gefunden')
s=s.replace(old,new,1)

old="function resolveShoppingType(text){const q=norm(text);if(shoppingTypeCache.has(q))return shoppingTypeCache.get(q);let found=null;for(const [type,terms] of TYPE_RULES){if(norm(type)===q||terms.some(term=>norm(term)===q||strictTypeHit(text,term))){found=type;break}}if(!found){const cats=[...new Set(data.map(category))];found=cats.find(c=>norm(c)===q)||null}shoppingTypeCache.set(q,found);return found}"
new="function resolveShoppingType(text){const q=norm(text);if(shoppingTypeCache.has(q))return shoppingTypeCache.get(q);let found=shoppingBrandTypeMap.get(q)||null;for(const [type,terms] of TYPE_RULES){if(found)break;if(norm(type)===q||terms.some(term=>norm(term)===q||strictTypeHit(text,term))){found=type;break}}if(!found){const cats=[...new Set(data.map(category))];found=cats.find(c=>norm(c)===q)||null}shoppingTypeCache.set(q,found);return found}"
if old not in s: raise SystemExit('resolveShoppingType nicht gefunden')
s=s.replace(old,new,1)

# Kasten darf nur Mehrfachgebinde/Kasten treffen
old="function shoppingMatchScore(item,p){const q=norm(item.text),mode=item.mode||'auto',resolved=resolveShoppingType(item.text),m=shoppingMeta(p);"
new="function shoppingUnitCompatible(item,p){if((item.unit||'')!=='Kasten')return true;const raw=norm(`${p.name||''} ${p.quantity||''}`);return raw.includes('kasten')||/\\b\\d+\\s*x\\s*\\d+(?:[.,]\\d+)?\\s*(?:l|ml)\\b/i.test(String(p.quantity||''))}\nfunction shoppingMatchScore(item,p){if(!shoppingUnitCompatible(item,p))return 0;const q=norm(item.text),mode=item.mode||'auto',resolved=resolveShoppingType(item.text),m=shoppingMeta(p);"
if old not in s: raise SystemExit('shoppingMatchScore nicht gefunden')
s=s.replace(old,new,1)

# Vorschlagsindex baut zugleich zuverlässige Marken->Produktart Zuordnung
old="function renderShoppingSuggestions(){if(shoppingSuggestionsReady||!data.length)return;const values=new Set();TYPE_RULES.forEach(([type])=>values.add(type));data.forEach(p=>{const b=(p.brand||'').trim(),l=productLabel(p);if(b)values.add(b);if(l&&l.length<45)values.add(l)});shopSuggestions.innerHTML=[...values].sort((a,b)=>a.localeCompare(b,'de')).slice(0,500).map(x=>`<option value=\"${htmlEsc(x)}\"></option>`).join('');shoppingSuggestionsReady=true}"
new="function renderShoppingSuggestions(){if(shoppingSuggestionsReady||!data.length)return;const values=new Set(),counts=new Map();TYPE_RULES.forEach(([type])=>values.add(type));data.forEach(p=>{const b=(p.brand||'').trim(),l=productLabel(p),type=productType(p);for(const raw of [b,l]){if(!raw||raw.length>=45)continue;values.add(raw);const key=norm(raw);if(!counts.has(key))counts.set(key,new Map());const cm=counts.get(key);cm.set(type,(cm.get(type)||0)+1)}});shoppingBrandTypeMap.clear();for(const [key,cm] of counts){const ranked=[...cm.entries()].sort((a,b)=>b[1]-a[1]),total=ranked.reduce((n,x)=>n+x[1],0);if(ranked[0]&&ranked[0][1]/total>=.8)shoppingBrandTypeMap.set(key,ranked[0][0])}shoppingTypeCache.clear();shopSuggestions.innerHTML=[...values].sort((a,b)=>a.localeCompare(b,'de')).slice(0,500).map(x=>`<option value=\"${htmlEsc(x)}\"></option>`).join('');shoppingSuggestionsReady=true}"
if old not in s: raise SystemExit('renderShoppingSuggestions nicht gefunden')
s=s.replace(old,new,1)

# Kartoffeln sinnvoll als Haushaltsmenge pro Mahlzeit
old="if(t==='Eier')return{amount:Math.max(1,Math.round(a*1+c*2)),unit:'Stück',note:'Grobe Wochenorientierung; Eier in verarbeiteten Lebensmitteln sind darin nicht enthalten.'};return{amount:1,unit:recommendShoppingUnit(text),note:''}}"
new="if(t==='Eier')return{amount:Math.max(1,Math.round(a*1+c*2)),unit:'Stück',note:'Grobe Wochenorientierung; Eier in verarbeiteten Lebensmitteln sind darin nicht enthalten.'};if(t==='Kartoffeln')return{amount:Math.round((a*.25+c*.15)*10)/10,unit:'kg',note:'Startwert für eine Kartoffelmahlzeit: etwa 250 g je Erwachsenem, Kinder kleiner angesetzt.'};return{amount:1,unit:recommendShoppingUnit(text),note:''}}"
if old not in s: raise SystemExit('Ende recommendation nicht gefunden')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Kasten-Matching, Marken-Typen und Kleinkinder ergänzt')
