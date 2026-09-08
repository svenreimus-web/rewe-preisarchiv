from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# CSS for route-grouped shopping list and share button
anchor='.shop-item-amount{font-weight:800;white-space:nowrap}'
addition='''.shop-item-amount{font-weight:800;white-space:nowrap}.shop-route-info{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:8px 0 4px;padding:9px 10px;border-radius:10px;background:#f8fafc;border:1px solid #e5e7eb}.shop-route-info b{display:block}.shop-route-info span{font-size:12px;color:var(--muted)}.shop-route-actions{display:flex;gap:8px;flex-wrap:wrap}.shop-share{border:0;border-radius:9px;padding:8px 10px;font-weight:800;background:#171717;color:#fff;white-space:nowrap}.shop-route-zone{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.04em;color:#6b7280;padding:10px 0 2px;border-bottom:1px solid #e5e7eb}.shop-route-zone:first-child{padding-top:2px}'''
if anchor not in s:
    raise SystemExit('CSS anchor missing')
s=s.replace(anchor,addition,1)

# Add route explainer and share button above list
old='<div class="shop-panel"><h3>Einkaufsliste</h3><div id="shoppingList" class="shopping-list"></div></div>'
new='''<div class="shop-panel"><h3>Einkaufsliste</h3><div class="shop-route-info"><div><b id="shoppingRouteTitle">Sortiert nach typischem Laufweg</b><span id="shoppingRouteHint">Die Reihenfolge ist eine Orientierung und kann je Filiale abweichen.</span></div><div class="shop-route-actions"><button id="shareShoppingBtn" class="shop-share" onclick="shareShoppingList()">Einkaufsliste teilen</button></div></div><div id="shoppingList" class="shopping-list"></div></div>'''
if old not in s:
    raise SystemExit('shopping panel anchor missing')
s=s.replace(old,new,1)

# Replace shopping unit/list block with route-aware implementation
pattern=r"const SHOP_UNITS=\[.*?function shoppingMarketResult\(id\)"
replacement=r'''const SHOP_UNITS=['Stück','Packung','Kasten','Flasche','Becher','Dose','Glas','g','kg','ml','l','Bund','Netz','Rolle'];
const SHOP_ROUTE_ZONES={
  produce:'Obst & Gemüse',bakery:'Brot & Backwaren',dry:'Vorrat & Kochzutaten',chilled:'Molkerei & Kühlung',fresh:'Fleisch, Wurst & Fisch',frozen:'Tiefkühl',drinks:'Getränke',household:'Haushalt & Drogerie',other:'Sonstiges'
};
const SHOP_ROUTE_PROFILES={
  generic:['produce','bakery','dry','chilled','fresh','frozen','drinks','household','other'],
  REWE:['produce','bakery','dry','chilled','fresh','frozen','drinks','household','other'],
  EDEKA:['produce','bakery','chilled','fresh','dry','frozen','drinks','household','other'],
  GLOBUS:['produce','bakery','fresh','dry','chilled','frozen','drinks','household','other']
};
function shoppingRouteProfile(){const ids=[...selectedShoppingMarkets];if(ids.length!==1)return{key:'generic',label:'typischem Supermarkt-Laufweg'};const id=ids[0];if(id==='REWE')return{key:'REWE',label:'typischem REWE-Laufweg'};if(id==='GLOBUS')return{key:'GLOBUS',label:'typischem GLOBUS-Laufweg'};if(id.startsWith('EDEKA_'))return{key:'EDEKA',label:'typischem EDEKA-Laufweg'};return{key:'generic',label:'typischem Supermarkt-Laufweg'}}
function shoppingRouteZone(item){const t=norm(resolveShoppingType(item.text)||item.text);const has=(...xs)=>xs.some(x=>t.includes(norm(x)));
  if(has('äpfel','bananen','tomaten','paprika','kartoffeln','zwiebeln','obst','gemüse','salat','kräuter','blumen','pflanzen'))return'produce';
  if(has('brot','backwaren','brötchen','toast','baguette','kuchen'))return'bakery';
  if(has('butter','margarine','milch','joghurt','quark','käse','eier','molkerei'))return'chilled';
  if(has('wurst','aufschnitt','salami','hackfleisch','rindfleisch','schweinefleisch','geflügel','fisch','garnelen','fleisch'))return'fresh';
  if(has('tiefkühl','eis'))return'frozen';
  if(has('wasser','bier','wein','sekt','saft','cola','limonade','kaffeegetränk','alkoholfreie getränke','alkoholische getränke','spirituosen'))return'drinks';
  if(has('waschmittel','spülmittel','reinigung','papier','klopapier','küchenrolle','drogerie','baby','tierbedarf','haushalt','non-food'))return'household';
  if(has('nudeln','pasta','reis','konserven','sauce','gewürz','öl','frühstück','kaffee','tee','schokolade','süßwaren','chips','snacks','backen','vorrat'))return'dry';
  return'other'}
function sortedShoppingEntries(){const profile=shoppingRouteProfile(),order=SHOP_ROUTE_PROFILES[profile.key]||SHOP_ROUTE_PROFILES.generic;return shoppingItems.map((item,index)=>({item,index,zone:shoppingRouteZone(item)})).sort((a,b)=>order.indexOf(a.zone)-order.indexOf(b.zone)||a.item.text.localeCompare(b.item.text,'de',{sensitivity:'base'}))}
function shoppingUnitOptions(selected){return SHOP_UNITS.map(u=>`<option ${u===selected?'selected':''}>${u}</option>`).join('')}
function updateShoppingItem(i,field,value){const x=shoppingItems[i];if(!x)return;if(field==='amount')x.amount=Math.max(.1,Number(value)||1);if(field==='unit')x.unit=value;saveShoppingState();renderShoppingList();renderShoppingResults(false)}
function routeShareButtonLabel(){const ua=navigator.userAgent||'',isApple=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1),isAndroid=/Android/i.test(ua);return isApple?'In Notizen teilen':isAndroid?'In Notiz-App teilen':'Einkaufsliste teilen'}
function renderShoppingList(){const entries=sortedShoppingEntries(),profile=shoppingRouteProfile();if(document.getElementById('shoppingRouteTitle'))shoppingRouteTitle.textContent=`Sortiert nach ${profile.label}`;if(document.getElementById('shareShoppingBtn'))shareShoppingBtn.textContent=routeShareButtonLabel();if(!entries.length){shoppingList.innerHTML='<div class="empty">Deine Einkaufsliste ist noch leer.</div>';return}let lastZone=null,html='';for(const e of entries){if(e.zone!==lastZone){html+=`<div class="shop-route-zone">${SHOP_ROUTE_ZONES[e.zone]||'Sonstiges'}</div>`;lastZone=e.zone}const x=e.item,i=e.index;html+=`<div class="shop-item"><div><b>${htmlEsc(x.text)}</b><div class="shop-kind">${shoppingModeLabel(x.mode||'auto')}</div></div><span class="shop-item-amount"><input style="width:72px;padding:7px;border:1px solid #d1d5db;border-radius:8px" type="number" min="0.1" step="0.1" value="${Number(x.amount)||1}" onchange="updateShoppingItem(${i},'amount',this.value)"> <select style="padding:7px;border:1px solid #d1d5db;border-radius:8px" onchange="updateShoppingItem(${i},'unit',this.value)">${shoppingUnitOptions(x.unit||'Packung')}</select></span><button onclick="removeShoppingItem(${i})" aria-label="Entfernen">✕</button></div>`}shoppingList.innerHTML=html+'<button class="shop-add" onclick="clearShoppingList()">Liste leeren</button>'}
function shoppingShareText(){const entries=sortedShoppingEntries(),profile=shoppingRouteProfile();let lines=['🛒 Einkaufsliste',`Sortiert nach ${profile.label}`,''];let lastZone=null;for(const e of entries){if(e.zone!==lastZone){if(lastZone!==null)lines.push('');lines.push(SHOP_ROUTE_ZONES[e.zone]||'Sonstiges');lastZone=e.zone}lines.push(`☐ ${e.item.text} — ${formatShoppingAmount(e.item)}`)}if(selectedShoppingMarkets.size){lines.push('',`Ausgewählte Märkte: ${[...selectedShoppingMarkets].map(id=>MARKET_NAMES[id]||id).join(', ')}`)}return lines.join('\n')}
async function shareShoppingList(){if(!shoppingItems.length)return;const text=shoppingShareText(),shareData={title:'Einkaufsliste',text};try{if(navigator.share){await navigator.share(shareData);return}if(navigator.clipboard){await navigator.clipboard.writeText(text);alert('Einkaufsliste wurde in die Zwischenablage kopiert.')}else{prompt('Einkaufsliste kopieren:',text)}}catch(e){if(e&&e.name==='AbortError')return;try{if(navigator.clipboard){await navigator.clipboard.writeText(text);alert('Teilen war nicht möglich. Die Einkaufsliste wurde stattdessen kopiert.')}else{prompt('Einkaufsliste kopieren:',text)}}catch(_){prompt('Einkaufsliste kopieren:',text)}}}
function shoppingMarketResult(id)'''
ns,n=re.subn(pattern,lambda m: replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'list block not found: {n}')
s=ns

# Ensure market selection rerenders route order too
s=s.replace("function toggleShoppingMarket(id){if(selectedShoppingMarkets.has(id))selectedShoppingMarkets.delete(id);else selectedShoppingMarkets.add(id);saveShoppingState();renderShoppingMarkets();renderShoppingResults(false);updateMapMarkers()}","function toggleShoppingMarket(id){if(selectedShoppingMarkets.has(id))selectedShoppingMarkets.delete(id);else selectedShoppingMarkets.add(id);saveShoppingState();renderShoppingMarkets();renderShoppingList();renderShoppingResults(false);updateMapMarkers()}")

p.write_text(s,encoding='utf-8')
print('shopping route sorting and sharing added')
