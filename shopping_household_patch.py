from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1) CSS: schnellere/erweiterte Einkaufseingabe + Haushalt
s=s.replace(
".shop-form{display:grid;grid-template-columns:minmax(0,1fr) 145px 72px auto;gap:8px;margin-top:12px}",
".shop-form{display:grid;grid-template-columns:minmax(0,1fr) 145px 86px 110px auto;gap:8px;margin-top:12px}",1)
s=s.replace(
".location-ok{color:var(--green);font-weight:700}@media(max-width:600px)",
".location-ok{color:var(--green);font-weight:700}.household-box{margin-top:12px;padding:12px;border:1px solid #e5e7eb;border-radius:12px;background:#fafafa}.household-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:8px}.household-grid label{font-size:12px;font-weight:700}.household-grid input,.household-grid select{display:block;width:100%;margin-top:4px;border:1px solid #d1d5db;border-radius:9px;padding:9px;background:#fff}.amount-hint{font-size:12px;color:var(--muted);margin-top:8px}.shop-item-amount{font-weight:800;white-space:nowrap}@media(max-width:600px)",1)
s=s.replace(
"@media(max-width:600px){.shop-form{grid-template-columns:1fr 1fr}.shop-form input:first-child{grid-column:1/-1}.shop-add{grid-column:1/-1}#marketMap{height:260px}}",
"@media(max-width:600px){.shop-form{grid-template-columns:1fr 1fr}.shop-form input:first-child{grid-column:1/-1}.shop-add{grid-column:1/-1}.household-grid{grid-template-columns:1fr 1fr}.household-grid label:last-child{grid-column:1/-1}#marketMap{height:260px}}",1)

# 2) HTML Einkauf: Haushaltsgröße + Einheit
old_html='''<section id="shoppingView" class="hidden"><div class="shop-intro"><h2>🛒 Meine Einkaufsliste</h2><div class="hint">Du kannst allgemein nach einer Produktart suchen – z. B. Butter, Wasser oder Bier – oder eine konkrete Marke bzw. ein konkretes Produkt eintragen.</div><div class="shop-form"><input id="shopText" list="shopSuggestions" placeholder="z. B. Butter oder Krombacher"><select id="shopMode"><option value="auto">Automatisch</option><option value="type">Produktart</option><option value="product">Marke / Produkt</option></select><input id="shopQty" type="number" min="1" step="1" value="1" aria-label="Menge"><button class="shop-add" onclick="addShoppingItem()">Hinzufügen</button></div><datalist id="shopSuggestions"></datalist></div>'''
new_html='''<section id="shoppingView" class="hidden"><div class="shop-intro"><h2>🛒 Meine Einkaufsliste</h2><div class="hint">Du kannst allgemein nach einer Produktart suchen – z. B. Butter, Wasser oder Bier – oder eine konkrete Marke bzw. ein konkretes Produkt eintragen. Mengen sind nur Startvorschläge und jederzeit änderbar.</div><div class="household-box"><b>Haushalt für den Wocheneinkauf</b><div class="household-grid"><label>Erwachsene<input id="houseAdults" type="number" min="1" max="12" step="1" value="2" onchange="updateHousehold()"></label><label>Kinder<input id="houseChildren" type="number" min="0" max="12" step="1" value="0" onchange="updateHousehold()"></label><label>Alter der Kinder<select id="houseChildAge" onchange="updateHousehold()"><option value="4-6">4–6 Jahre</option><option value="7-9" selected>7–9 Jahre</option><option value="10-12">10–12 Jahre</option><option value="13-14">13–14 Jahre</option><option value="15-18">15–18 Jahre</option></select></label></div><div class="amount-hint">Die Haushaltsgröße dient nur dazu, sinnvolle Mengen vorzuschlagen. Sie wird lokal auf diesem Gerät gespeichert.</div></div><div class="shop-form"><input id="shopText" list="shopSuggestions" placeholder="z. B. Butter oder Krombacher"><select id="shopMode"><option value="auto">Automatisch</option><option value="type">Produktart</option><option value="product">Marke / Produkt</option></select><input id="shopAmount" type="number" min="0.1" step="0.1" value="1" aria-label="Menge"><select id="shopUnit" aria-label="Einheit"><option>Stück</option><option>Packung</option><option>Kasten</option><option>Flasche</option><option>Becher</option><option>Dose</option><option>Glas</option><option>g</option><option>kg</option><option>ml</option><option>l</option><option>Bund</option><option>Netz</option><option>Rolle</option></select><button class="shop-add" onclick="addShoppingItem()">Hinzufügen</button></div><div id="shopSuggestionHint" class="amount-hint"></div><datalist id="shopSuggestions"></datalist></div>'''
if old_html not in s:
    raise SystemExit('Shopping-HTML nicht gefunden')
s=s.replace(old_html,new_html,1)

# 3) globale Zustände
old="let data=[],archive=[],selected='Alle',market='Alle',recipeMarket='REWE',recipeStyle='alle',shoppingItems=[],lastRecipes=[];"
new="let data=[],archive=[],selected='Alle',market='Alle',recipeMarket='REWE',recipeStyle='alle',shoppingItems=[],lastRecipes=[],household={adults:2,children:0,childAge:'7-9'},shoppingSuggestionsReady=false;"
if old not in s: raise SystemExit('Globalzustand nicht gefunden')
s=s.replace(old,new,1)

# 4) Shopping-State inkl. Haushalt und Migration alter qty-Einträge
old=re.search(r"function loadShoppingState\(\)\{.*?\}\nfunction saveShoppingState\(\)\{.*?\}\nfunction shoppingModeLabel",s,re.S)
if not old: raise SystemExit('Shopping-State nicht gefunden')
state='''function loadShoppingState(){try{const a=JSON.parse(localStorage.getItem('priceArchive.shopping')||'[]');shoppingItems=Array.isArray(a)?a.filter(x=>x&&x.text).map(x=>({text:x.text,mode:x.mode||'auto',amount:Math.max(.1,Number(x.amount??x.qty??1)||1),unit:x.unit||recommendShoppingUnit(x.text)})):[];const m=JSON.parse(localStorage.getItem('priceArchive.markets')||'null');if(Array.isArray(m))selectedShoppingMarkets=new Set(m.filter(x=>MARKET_IDS.includes(x)));const h=JSON.parse(localStorage.getItem('priceArchive.household')||'null');if(h&&typeof h==='object')household={adults:Math.max(1,Number(h.adults)||2),children:Math.max(0,Number(h.children)||0),childAge:['4-6','7-9','10-12','13-14','15-18'].includes(h.childAge)?h.childAge:'7-9'}}catch(e){shoppingItems=[];selectedShoppingMarkets=new Set(MARKET_IDS)}if(!selectedShoppingMarkets.size)selectedShoppingMarkets=new Set(MARKET_IDS)}
function saveShoppingState(){localStorage.setItem('priceArchive.shopping',JSON.stringify(shoppingItems));localStorage.setItem('priceArchive.markets',JSON.stringify([...selectedShoppingMarkets]));localStorage.setItem('priceArchive.household',JSON.stringify(household))}
function shoppingModeLabel'''
s=s[:old.start()]+state+s[old.end():]

# 5) Mengen-/Einheitenlogik vor Cache einfügen
marker="const shoppingOfferCache=new Map(),shoppingTypeCache=new Map(),shoppingMetaCache=new WeakMap();"
if marker not in s: raise SystemExit('Cache-Marker nicht gefunden')
logic=r'''const CHILD_WEEKLY_WATER_ML={'4-6':800,'7-9':900,'10-12':1000,'13-14':1250,'15-18':1450};
const CHILD_MEAL_G={'4-6':{pasta:70,meat:70,cheese:20},'7-9':{pasta:80,meat:80,cheese:20},'10-12':{pasta:95,meat:95,cheese:25},'13-14':{pasta:110,meat:110,cheese:25},'15-18':{pasta:120,meat:120,cheese:30}};
function syncHouseholdUI(){if(!document.getElementById('houseAdults'))return;houseAdults.value=household.adults;houseChildren.value=household.children;houseChildAge.value=household.childAge}
function updateHousehold(){household={adults:Math.max(1,Number(houseAdults.value)||1),children:Math.max(0,Number(houseChildren.value)||0),childAge:houseChildAge.value};saveShoppingState();applyShoppingSuggestion()}
function recommendShoppingUnit(text){const t=resolveShoppingType(text);if(['Wasser','Bier','Saft','Cola & Limonade'].includes(t))return 'Kasten';if(['Pasta & Nudeln','Wurst & Aufschnitt','Käse','Hackfleisch','Rindfleisch','Schweinefleisch','Geflügel','Fisch','Garnelen','Butter','Margarine'].includes(t))return 'g';if(t==='Milch')return 'l';if(t==='Eier')return 'Stück';if(['Kartoffeln','Äpfel','Bananen','Tomaten','Paprika','Zwiebeln'].includes(t))return 'kg';return 'Packung'}
function recommendShoppingAmount(text){const t=resolveShoppingType(text),a=household.adults,c=household.children,cp=CHILD_MEAL_G[household.childAge]||CHILD_MEAL_G['7-9'];if(t==='Wasser'){const liters=(a*1500+c*(CHILD_WEEKLY_WATER_ML[household.childAge]||900))*7/1000;return{amount:Math.max(1,Math.ceil(liters/12)),unit:'Kasten',note:`Wochenorientierung: ca. ${liters.toFixed(1).replace('.',',')} l Getränke für den Haushalt; für den Kasten-Vorschlag rechnen wir grob mit 12 l je Kasten.`}}if(['Bier','Saft','Cola & Limonade'].includes(t))return{amount:1,unit:'Kasten',note:'Kasten ist als übliche Einkaufseinheit vorausgewählt; die Menge ist keine Verzehrempfehlung.'};if(t==='Pasta & Nudeln')return{amount:Math.round(a*125+c*cp.pasta),unit:'g',note:'Startwert für eine Nudelmahlzeit: 125 g trockene Nudeln je Erwachsenem, für Kinder altersabhängig kleiner.'};if(t==='Wurst & Aufschnitt')return{amount:Math.max(30,Math.round(a*60+c*40)),unit:'g',note:'Wochen-Startwert: Erwachsene 2 × 30 g Wurst; Kinder grob kleiner angesetzt.'};if(t==='Käse')return{amount:Math.max(30,Math.round(a*30+c*cp.cheese)),unit:'g',note:'Startwert für eine Käseportion: 30 g je Erwachsenem, Kinder altersabhängig kleiner.'};if(['Hackfleisch','Rindfleisch','Schweinefleisch','Geflügel','Fisch'].includes(t))return{amount:Math.round(a*120+c*cp.meat),unit:'g',note:'Startwert für eine Hauptmahlzeit: etwa 120 g je Erwachsenem, Kinder altersabhängig kleiner.'};if(t==='Butter'||t==='Margarine')return{amount:Math.max(50,Math.round(a*70+c*50)),unit:'g',note:'Grobe Wochenorientierung für Streich-/Zubereitungsfett; Butter und Margarine zählen dabei zusammen.'};if(t==='Milch')return{amount:Math.max(.5,Math.round((a*.25+c*.2)*10)/10),unit:'l',note:'Startwert für eine Milchportion im Haushalt; bei täglichem Verbrauch entsprechend erhöhen.'};if(t==='Eier')return{amount:Math.max(1,Math.round(a*1+c*2)),unit:'Stück',note:'Grobe Wochenorientierung; Eier in verarbeiteten Lebensmitteln sind darin nicht enthalten.'};return{amount:1,unit:recommendShoppingUnit(text),note:''}}
function applyShoppingSuggestion(){if(!document.getElementById('shopText'))return;const text=shopText.value.trim();if(!text){shopSuggestionHint.textContent='';return}const r=recommendShoppingAmount(text);shopAmount.value=r.amount;shopUnit.value=r.unit;shopSuggestionHint.textContent=r.note||''}
function formatShoppingAmount(item){const n=Number(item.amount)||1,shown=Number.isInteger(n)?String(n):String(Math.round(n*10)/10).replace('.',',');return `${shown} ${item.unit||'Packung'}`}
function parseOfferPackage(p){const raw=String(p.quantity||'').toLowerCase().replace(/,/g,'.');let m=raw.match(/(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[- ]?(kg|g|l|ml)\b/i);if(m){const count=Number(m[1]),v=Number(m[2]),u=m[3].toLowerCase();return{kind:(u==='kg'||u==='g')?'mass':'volume',base:count*v*(u==='kg'?1000:u==='l'?1000:1)}}m=raw.match(/(\d+(?:\.\d+)?)\s*[- ]?(kg|g|l|ml)\b/i);if(!m)return null;const v=Number(m[1]),u=m[2].toLowerCase();return{kind:(u==='kg'||u==='g')?'mass':'volume',base:v*(u==='kg'?1000:u==='l'?1000:1)}}
function shoppingOfferCount(item,p){const amount=Math.max(.1,Number(item.amount)||1),unit=item.unit||'Packung';if(['Stück','Packung','Kasten','Flasche','Becher','Dose','Glas','Bund','Netz','Rolle'].includes(unit))return Math.max(1,Math.ceil(amount));const pack=parseOfferPackage(p);if(!pack)return 1;const need=(unit==='kg'||unit==='l')?amount*1000:amount;if((unit==='g'||unit==='kg')&&pack.kind!=='mass')return 1;if((unit==='ml'||unit==='l')&&pack.kind!=='volume')return 1;return Math.max(1,Math.ceil(need/pack.base))}
'''
s=s.replace(marker,logic+marker,1)

# 6) Add/remove nur noch Fast-Render; Menge + Einheit speichern
old=re.search(r"function addShoppingItem\(\)\{.*?\}\nfunction addShoppingItemText\(.*?\nfunction clearShoppingList\(\)\{.*?\}",s,re.S)
if not old: raise SystemExit('Add/Remove-Block nicht gefunden')
new=r'''function addShoppingItem(){const text=shopText.value.trim(),amount=Math.max(.1,Number(shopAmount.value)||1),unit=shopUnit.value,mode=shopMode.value;if(!text)return;addShoppingItemText(text,amount,mode,true,unit);shopText.value='';shopSuggestionHint.textContent='';shopAmount.value='1';shopUnit.value='Packung';shopText.focus()}
function addShoppingItemText(text,amount=null,mode='auto',rerender=true,unit=null){text=String(text||'').trim();if(!text)return;const rec=recommendShoppingAmount(text);amount=amount==null?rec.amount:Math.max(.1,Number(amount)||1);unit=unit||rec.unit;const existing=shoppingItems.find(x=>norm(x.text)===norm(text)&&(x.mode||'auto')===mode&&(x.unit||'Packung')===unit);if(existing)existing.amount=(Number(existing.amount)||1)+amount;else shoppingItems.push({text,amount,unit,mode});saveShoppingState();if(rerender)renderShoppingFast()}
function removeShoppingItem(i){shoppingItems.splice(i,1);saveShoppingState();renderShoppingFast()}
function clearShoppingList(){shoppingItems=[];saveShoppingState();renderShoppingFast()}'''
s=s[:old.start()]+new+s[old.end():]

# 7) Suggestions nur einmal bauen
old="function renderShoppingSuggestions(){if(!data.length)return;const values=new Set();TYPE_RULES.forEach(([type])=>values.add(type));data.forEach(p=>{const b=(p.brand||'').trim(),l=productLabel(p);if(b)values.add(b);if(l&&l.length<45)values.add(l)});shopSuggestions.innerHTML=[...values].sort((a,b)=>a.localeCompare(b,'de')).slice(0,500).map(x=>`<option value=\"${htmlEsc(x)}\"></option>`).join('')}"
new="function renderShoppingSuggestions(){if(shoppingSuggestionsReady||!data.length)return;const values=new Set();TYPE_RULES.forEach(([type])=>values.add(type));data.forEach(p=>{const b=(p.brand||'').trim(),l=productLabel(p);if(b)values.add(b);if(l&&l.length<45)values.add(l)});shopSuggestions.innerHTML=[...values].sort((a,b)=>a.localeCompare(b,'de')).slice(0,500).map(x=>`<option value=\"${htmlEsc(x)}\"></option>`).join('');shoppingSuggestionsReady=true}"
if old not in s: raise SystemExit('Suggestions-Funktion nicht gefunden')
s=s.replace(old,new,1)

# 8) Listendarstellung Menge/Einheit
old="function renderShoppingList(){shoppingList.innerHTML=shoppingItems.length?shoppingItems.map((x,i)=>`<div class=\"shop-item\"><div><b>${htmlEsc(x.text)}</b><div class=\"shop-kind\">${shoppingModeLabel(x.mode||'auto')}</div></div><span>${Number(x.qty)||1}×</span><button onclick=\"removeShoppingItem(${i})\" aria-label=\"Entfernen\">✕</button></div>`).join('')+'<button class=\"shop-add\" onclick=\"clearShoppingList()\">Liste leeren</button>':'<div class=\"empty\">Deine Einkaufsliste ist noch leer.</div>'}"
new="function renderShoppingList(){shoppingList.innerHTML=shoppingItems.length?shoppingItems.map((x,i)=>`<div class=\"shop-item\"><div><b>${htmlEsc(x.text)}</b><div class=\"shop-kind\">${shoppingModeLabel(x.mode||'auto')}</div></div><span class=\"shop-item-amount\">${formatShoppingAmount(x)}</span><button onclick=\"removeShoppingItem(${i})\" aria-label=\"Entfernen\">✕</button></div>`).join('')+'<button class=\"shop-add\" onclick=\"clearShoppingList()\">Liste leeren</button>':'<div class=\"empty\">Deine Einkaufsliste ist noch leer.</div>'}"
if old not in s: raise SystemExit('ShoppingList nicht gefunden')
s=s.replace(old,new,1)

# 9) Marktergebnis nutzt tatsächliche benötigte Angebots-Packungszahl
old="function shoppingMarketResult(id){const details=shoppingItems.map(item=>{const p=bestShoppingOffer(item,id);return{item,p}}),found=details.filter(x=>x.p),sum=found.reduce((s,x)=>s+currentPrice(x.p)*(Number(x.item.qty)||1),0);return{id,details,found,sum}}"
new="function shoppingMarketResult(id){const details=shoppingItems.map(item=>{const p=bestShoppingOffer(item,id),count=p?shoppingOfferCount(item,p):0;return{item,p,count}}),found=details.filter(x=>x.p),sum=found.reduce((s,x)=>s+currentPrice(x.p)*x.count,0);return{id,details,found,sum}}"
if old not in s: raise SystemExit('shoppingMarketResult nicht gefunden')
s=s.replace(old,new,1)

# In Detailanzeige qty durch count/Bedarf ersetzen
s=s.replace("${euro(currentPrice(x.p))}${Number(x.item.qty)>1?` × ${Number(x.item.qty)}`:''}","${euro(currentPrice(x.p))}${x.count>1?` × ${x.count} Packungen`:''} · Bedarf ${formatShoppingAmount(x.item)}",1)

# Combo: count berechnen + Summe
old_combo="return{item,best:opts[0]||null}}),comboFound=combo.filter(x=>x.best),comboSum=comboFound.reduce((s,x)=>s+currentPrice(x.best.p)*(Number(x.item.qty)||1),0),comboMarkets=[...new Set(comboFound.map(x=>x.best.id))];"
new_combo="const best=opts[0]||null;return{item,best,count:best?shoppingOfferCount(item,best.p):0}}),comboFound=combo.filter(x=>x.best),comboSum=comboFound.reduce((s,x)=>s+currentPrice(x.best.p)*x.count,0),comboMarkets=[...new Set(comboFound.map(x=>x.best.id))];"
if old_combo not in s: raise SystemExit('Combo-Summe nicht gefunden')
s=s.replace(old_combo,new_combo,1)
s=s.replace("${euro(currentPrice(x.best.p))}</li>","${euro(currentPrice(x.best.p))}${x.count>1?` × ${x.count} Packungen`:''} · Bedarf ${formatShoppingAmount(x.item)}</li>",1)

# 10) Fast render statt Karte/Suggestions bei jeder Listenänderung
old="function renderShopping(){renderShoppingMarkets();renderShoppingList();renderShoppingSuggestions();renderShoppingResults();if(!shoppingView.classList.contains('hidden'))setTimeout(initMarketMap,30)}"
new="function renderShoppingFast(){renderShoppingList();renderShoppingResults(false)}\nfunction renderShopping(){syncHouseholdUI();renderShoppingMarkets();renderShoppingList();renderShoppingSuggestions();renderShoppingResults(false);if(!shoppingView.classList.contains('hidden'))setTimeout(initMarketMap,30)}"
if old not in s: raise SystemExit('renderShopping nicht gefunden')
s=s.replace(old,new,1)

# 11) Rezepte verwenden Mengenempfehlung statt 1 g etc.
s=s.replace("r.items.forEach(p=>addShoppingItemText(productType(p),1,'type',false));r.extras.forEach(x=>addShoppingItemText(x,1,'auto',false));", "r.items.forEach(p=>addShoppingItemText(productType(p),null,'type',false));r.extras.forEach(x=>addShoppingItemText(x,null,'auto',false));",1)

# 12) Events: Textänderung passt Vorschlag an
old="q.oninput=render;shopText.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addShoppingItem()}};modal.onclick"
new="q.oninput=render;shopText.oninput=applyShoppingSuggestion;shopText.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addShoppingItem()}};modal.onclick"
if old not in s: raise SystemExit('Eventblock nicht gefunden')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Shopping V2 eingebaut: Fast-Render, Haushalt, Einheiten, Mengenempfehlungen, Kasten-Default.')
