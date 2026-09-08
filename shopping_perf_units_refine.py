from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1. Kategorie und Produktart cachen: beide werden sehr oft gebraucht.
old="function category(p){const f=fields(p),scored=RULES.map(r=>{const nameHits=r.n?.filter(x=>phraseHit(f.name,x)).length||0,descHits=r.d?.filter(x=>phraseHit(f.desc,x)).length||0;return{cat:r.cat,score:nameHits*12+descHits*5+r.pri/100,pri:r.pri}}).filter(x=>x.score>=5);if(!scored.length)return 'Weitere';scored.sort((a,b)=>b.score-a.score||b.pri-a.pri);return scored[0].cat}"
new="const categoryCache=new WeakMap();\nfunction category(p){if(categoryCache.has(p))return categoryCache.get(p);const f=fields(p),scored=RULES.map(r=>{const nameHits=r.n?.filter(x=>phraseHit(f.name,x)).length||0,descHits=r.d?.filter(x=>phraseHit(f.desc,x)).length||0;return{cat:r.cat,score:nameHits*12+descHits*5+r.pri/100,pri:r.pri}}).filter(x=>x.score>=5);const result=scored.length?(scored.sort((a,b)=>b.score-a.score||b.pri-a.pri),scored[0].cat):'Weitere';categoryCache.set(p,result);return result}"
if old not in s: raise SystemExit('category nicht gefunden')
s=s.replace(old,new,1)

old="function productType(p){const name=`${p.name||''} ${p.brand||''}`;for(const [type,terms] of TYPE_RULES)if(terms.some(t=>strictTypeHit(name,t)))return type;const cat=category(p),desc=p.quantity||'';for(const [type,terms] of TYPE_RULES)if(DESC_TYPE_CATEGORY[type]===cat&&terms.some(t=>strictTypeHit(desc,t)))return type;return cat}"
new="const productTypeCache=new WeakMap();\nfunction productType(p){if(productTypeCache.has(p))return productTypeCache.get(p);const name=`${p.name||''} ${p.brand||''}`;let result=null;for(const [type,terms] of TYPE_RULES){if(terms.some(t=>strictTypeHit(name,t))){result=type;break}}if(!result){const cat=category(p),desc=p.quantity||'';for(const [type,terms] of TYPE_RULES){if(DESC_TYPE_CATEGORY[type]===cat&&terms.some(t=>strictTypeHit(desc,t))){result=type;break}}result=result||cat}productTypeCache.set(p,result);return result}"
if old not in s: raise SystemExit('productType nicht gefunden')
s=s.replace(old,new,1)

# 2. Kategorien für Shopping nicht mehr bei jedem Tastendruck über alle Angebote neu berechnen.
old="const shoppingOfferCache=new Map(),shoppingTypeCache=new Map(),shoppingMetaCache=new WeakMap(),shoppingBrandTypeMap=new Map();"
new="const shoppingOfferCache=new Map(),shoppingTypeCache=new Map(),shoppingMetaCache=new WeakMap(),shoppingBrandTypeMap=new Map();let shoppingCategoryNames=[];"
if old not in s: raise SystemExit('shopping cache declaration nicht gefunden')
s=s.replace(old,new,1)
old="if(!found){const cats=[...new Set(data.map(category))];found=cats.find(c=>norm(c)===q)||null}"
new="if(!found)found=shoppingCategoryNames.find(c=>norm(c)===q)||null"
if old not in s: raise SystemExit('category fallback nicht gefunden')
s=s.replace(old,new,1)

# 3. Wasser: ausdrücklich EIN Kasten vorselektieren; Literbedarf nur als Hinweis.
old=re.search(r"if\(t==='Wasser'\)\{const liters=.*?\}\}if\(\['Bier','Saft','Cola & Limonade'\]",s,re.S)
if not old: raise SystemExit('Wasser recommendation nicht gefunden')
new="if(t==='Wasser'){const liters=(a*1500+c*(CHILD_WEEKLY_WATER_ML[household.childAge]||900))*7/1000;return{amount:1,unit:'Kasten',note:`1 Kasten ist vorausgewählt. Zur Orientierung entspräche der Wochen-Trinkmenge für diesen Haushalt grob ${liters.toFixed(1).replace('.',',')} l; Kastengrößen unterscheiden sich, deshalb wird die Kastenanzahl nicht automatisch hochgerechnet.`}}if(['Bier','Saft','Cola & Limonade']"
s=s[:old.start()]+new+s[old.end():]

# 4. Wurst/Käse: nachvollziehbare Portionen; Kinder altersabhängig kleiner.
old="if(t==='Wurst & Aufschnitt')return{amount:Math.max(30,Math.round(a*60+c*40)),unit:'g',note:'Wochen-Startwert: Erwachsene 2 × 30 g Wurst; Kinder grob kleiner angesetzt.'};if(t==='Käse')return{amount:Math.max(30,Math.round(a*30+c*cp.cheese)),unit:'g',note:'Startwert für eine Käseportion: 30 g je Erwachsenem, Kinder altersabhängig kleiner.'};"
new="if(t==='Wurst & Aufschnitt'){const cw={'1-3':15,'4-6':20,'7-9':20,'10-12':25,'13-14':25,'15-18':30}[household.childAge]||20;return{amount:Math.max(30,Math.round(a*60+c*cw*2)),unit:'g',note:'Wochen-Startwert: Erwachsene 2 × 30 g Wurst. Kinderportionen werden altersabhängig kleiner skaliert.'}}if(t==='Käse')return{amount:Math.max(30,Math.round(a*30+c*cp.cheese)),unit:'g',note:'Startwert für eine Haushaltsportion: 30 g Käse je Erwachsenem, Kinder altersabhängig kleiner. Die Zahl der Käsemahlzeiten pro Woche bleibt bewusst dir überlassen.'};"
if old not in s: raise SystemExit('Wurst/Käse recommendation nicht gefunden')
s=s.replace(old,new,1)

# 5. Vorschlagsliste einmalig und deutlich kleiner; Kategorien ebenfalls einmalig aufbauen.
old=re.search(r"function renderShoppingSuggestions\(\)\{.*?shoppingSuggestionsReady=true\}",s,re.S)
if not old: raise SystemExit('renderShoppingSuggestions nicht gefunden')
new=r'''function renderShoppingSuggestions(){if(shoppingSuggestionsReady||!data.length)return;shoppingCategoryNames=[...new Set(data.map(category))];const types=TYPE_RULES.map(x=>x[0]),extras=new Set(),counts=new Map();data.forEach(p=>{const b=(p.brand||'').trim(),l=productLabel(p),type=productType(p);for(const raw of [b,l]){if(!raw||raw.length>=45)continue;extras.add(raw);const key=norm(raw);if(!counts.has(key))counts.set(key,new Map());const cm=counts.get(key);cm.set(type,(cm.get(type)||0)+1)}});shoppingBrandTypeMap.clear();for(const [key,cm] of counts){const ranked=[...cm.entries()].sort((a,b)=>b[1]-a[1]),total=ranked.reduce((n,x)=>n+x[1],0);if(ranked[0]&&ranked[0][1]/total>=.8)shoppingBrandTypeMap.set(key,ranked[0][0])}shoppingTypeCache.clear();let migrated=false;shoppingItems.forEach(x=>{if(!x.unit){x.unit=recommendShoppingUnit(x.text);migrated=true}});if(migrated)saveShoppingState();const values=[...new Set([...types,...[...extras].sort((a,b)=>a.localeCompare(b,'de')).slice(0,100)])];shopSuggestions.innerHTML=values.map(x=>`<option value="${htmlEsc(x)}"></option>`).join('');shoppingSuggestionsReady=true}'''
s=s[:old.start()]+new+s[old.end():]

# 6. Einheiten direkt in der bestehenden Liste editierbar machen.
old="function renderShoppingList(){shoppingList.innerHTML=shoppingItems.length?shoppingItems.map((x,i)=>`<div class=\"shop-item\"><div><b>${htmlEsc(x.text)}</b><div class=\"shop-kind\">${shoppingModeLabel(x.mode||'auto')}</div></div><span class=\"shop-item-amount\">${formatShoppingAmount(x)}</span><button onclick=\"removeShoppingItem(${i})\" aria-label=\"Entfernen\">✕</button></div>`).join('')+'<button class=\"shop-add\" onclick=\"clearShoppingList()\">Liste leeren</button>':'<div class=\"empty\">Deine Einkaufsliste ist noch leer.</div>'}"
unit_options="['Stück','Packung','Kasten','Flasche','Becher','Dose','Glas','g','kg','ml','l','Bund','Netz','Rolle']"
new=f'''const SHOP_UNITS={unit_options};
function shoppingUnitOptions(selected){{return SHOP_UNITS.map(u=>`<option ${{u===selected?'selected':''}}>${{u}}</option>`).join('')}}
function updateShoppingItem(i,field,value){{const x=shoppingItems[i];if(!x)return;if(field==='amount')x.amount=Math.max(.1,Number(value)||1);if(field==='unit')x.unit=value;saveShoppingState();renderShoppingResults(false)}}
function renderShoppingList(){{shoppingList.innerHTML=shoppingItems.length?shoppingItems.map((x,i)=>`<div class="shop-item"><div><b>${{htmlEsc(x.text)}}</b><div class="shop-kind">${{shoppingModeLabel(x.mode||'auto')}}</div></div><span class="shop-item-amount"><input style="width:72px;padding:7px;border:1px solid #d1d5db;border-radius:8px" type="number" min="0.1" step="0.1" value="${{Number(x.amount)||1}}" onchange="updateShoppingItem(${{i}},'amount',this.value)"> <select style="padding:7px;border:1px solid #d1d5db;border-radius:8px" onchange="updateShoppingItem(${{i}},'unit',this.value)">${{shoppingUnitOptions(x.unit||'Packung')}}</select></span><button onclick="removeShoppingItem(${{i}})" aria-label="Entfernen">✕</button></div>`).join('')+'<button class="shop-add" onclick="clearShoppingList()">Liste leeren</button>':'<div class="empty">Deine Einkaufsliste ist noch leer.</div>'}}'''
if old not in s: raise SystemExit('renderShoppingList nicht gefunden')
s=s.replace(old,new,1)

# 7. Eingabe-Vorschlag leicht verzögert statt schwere Logik bei jedem einzelnen Tastendruck.
old="q.oninput=render;shopText.oninput=applyShoppingSuggestion;shopText.onkeydown=e=>"
new="let shopSuggestTimer=null;q.oninput=render;shopText.oninput=()=>{clearTimeout(shopSuggestTimer);shopSuggestTimer=setTimeout(applyShoppingSuggestion,80)};shopText.onkeydown=e=>"
if old not in s: raise SystemExit('shopText oninput nicht gefunden')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Finale Shopping-Optimierung: Caches, kleinere Vorschlagsliste, 1 Kasten Wasser, editierbare Einheiten.')
