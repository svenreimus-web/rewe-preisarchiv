from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'Anker nicht gefunden: {label}')
    text = text.replace(old, new, 1)


# Zusätzliche Styles + Leaflet
if 'id="marketMap"' not in text:
    replace_once(
        '</style></head>',
        '''
.shop-intro,.shop-panel,.shop-results{background:#fff;border-radius:15px;padding:15px;box-shadow:0 1px 4px #0001;margin-top:12px}.shop-intro h2,.shop-panel h3,.shop-results h3{margin:0 0 7px}.shop-form{display:grid;grid-template-columns:minmax(0,1fr) 145px 72px auto;gap:8px;margin-top:12px}.shop-form input,.shop-form select,.recipe-controls select{border:1px solid #d1d5db;border-radius:10px;padding:10px;background:#fff;min-width:0}.shop-add,.locate,.recipe-add{border:0;border-radius:10px;padding:10px 12px;font-weight:800;background:#171717;color:#fff}.locate{margin-top:10px}.recipe-add{margin-top:10px;width:100%}#marketMap{height:310px;border-radius:14px;overflow:hidden;margin-top:12px;background:#e5e7eb}.market-select-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin-top:10px}.market-select{display:flex;gap:9px;align-items:flex-start;border:1px solid #e5e7eb;border-radius:11px;padding:10px;background:#fafafa}.market-select input{margin-top:3px;transform:scale(1.15)}.market-select b{display:block}.market-select small{display:block;color:var(--muted);margin-top:3px;line-height:1.35}.shopping-list{display:grid;gap:8px;margin-top:10px}.shop-item{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;border-bottom:1px solid #eee;padding:9px 0}.shop-item .shop-kind{font-size:12px;color:var(--muted);margin-top:2px}.shop-item button{border:0;background:#f3f4f6;border-radius:8px;padding:7px 9px}.shop-summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin-top:10px}.shop-market-result,.shop-best{border:1px solid #e5e7eb;border-radius:12px;padding:12px}.shop-market-result h4,.shop-best h4{margin:0 0 5px}.shop-best{border-width:2px;margin-top:10px}.shop-result-list{font-size:12px;color:#4b5563;margin:8px 0 0;padding-left:18px}.shop-result-list li{margin:4px 0}.shop-note{font-size:12px;color:var(--muted);margin-top:10px}.recipe-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}.recipe-tags{font-size:12px;color:var(--muted);margin:3px 0 8px}.location-ok{color:var(--green);font-weight:700}@media(max-width:600px){.shop-form{grid-template-columns:1fr 1fr}.shop-form input:first-child{grid-column:1/-1}.shop-add{grid-column:1/-1}#marketMap{height:260px}}
</style><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"></head>''',
        'Styles/Leaflet',
    )

    replace_once(
        '<button id="tabFavorites" class="tab" onclick="setView(\'favorites\')">★ Favoriten</button><button id="tabRecipes" class="tab" onclick="setView(\'recipes\')">🥗 Rezepte aus Angeboten</button>',
        '<button id="tabFavorites" class="tab" onclick="setView(\'favorites\')">★ Favoriten</button><button id="tabShopping" class="tab" onclick="setView(\'shopping\')">🛒 Einkauf</button><button id="tabRecipes" class="tab" onclick="setView(\'recipes\')">🥗 Rezepte aus Angeboten</button>',
        'Einkauf-Tab',
    )

    shopping_section = '''<section id="shoppingView" class="hidden"><div class="shop-intro"><h2>🛒 Meine Einkaufsliste</h2><div class="hint">Du kannst allgemein nach einer Produktart suchen – z. B. Butter, Wasser oder Bier – oder eine konkrete Marke bzw. ein konkretes Produkt eintragen.</div><div class="shop-form"><input id="shopText" list="shopSuggestions" placeholder="z. B. Butter oder Krombacher"><select id="shopMode"><option value="auto">Automatisch</option><option value="type">Produktart</option><option value="product">Marke / Produkt</option></select><input id="shopQty" type="number" min="1" step="1" value="1" aria-label="Menge"><button class="shop-add" onclick="addShoppingItem()">Hinzufügen</button></div><datalist id="shopSuggestions"></datalist></div><div class="shop-panel"><h3>Meine Märkte</h3><div class="hint">Wähle nur Märkte aus, die für dich tatsächlich infrage kommen. Auf der Karte stehen aktuell die vier Märkte, für die wir Angebotsdaten haben. Ein Klick auf einen Marker wählt den Markt an oder ab.</div><button class="locate" onclick="requestLocation()">📍 Standort verwenden</button><div id="locationStatus" class="status">Der genaue Standort wird nicht gespeichert.</div><div id="marketMap"></div><div id="shoppingMarkets" class="market-select-grid"></div></div><div class="shop-panel"><h3>Einkaufsliste</h3><div id="shoppingList" class="shopping-list"></div></div><div class="shop-results"><h3>Angebotsvergleich</h3><div class="hint">Verglichen werden derzeit die aktuellen Angebotsartikel. Reguläre Ladenpreise für Artikel ohne Angebot liegen uns noch nicht vollständig vor.</div><div id="shoppingResults"></div></div></section>\n'''
    replace_once(
        '<section id="recipesView" class="hidden">',
        shopping_section + '<section id="recipesView" class="hidden">',
        'Einkaufsbereich',
    )

    replace_once(
        '</div></div><div id="recipeStatus" class="status"></div><div id="recipeGrid" class="recipe-grid"></div></section>',
        '</div><div class="recipe-controls"><b>Richtung:</b><select id="recipeStyle" onchange="setRecipeStyle(this.value)"><option value="alle">Alle</option><option value="gesund">Gesund</option><option value="leicht">Leicht</option><option value="deftig">Deftig</option><option value="vegetarisch">Vegetarisch</option><option value="schnell">Schnell</option><option value="guenstig">Günstig</option></select></div></div><div id="recipeStatus" class="status"></div><div id="recipeGrid" class="recipe-grid"></div></section>',
        'Rezept-Richtung',
    )

    replace_once(
        '<script>\nlet data=',
        '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n<script>\nlet data=',
        'Leaflet-JS',
    )

replace_once(
    "let data=[],archive=[],selected='Alle',market='Alle',recipeMarket='REWE';",
    "let data=[],archive=[],selected='Alle',market='Alle',recipeMarket='REWE',recipeStyle='alle',shoppingItems=[],lastRecipes=[];",
    'globale Zustände',
)

replace_once(
    "const MARKET_NAMES={REWE:'REWE Weilbach',GLOBUS:'GLOBUS Hattersheim',EDEKA_BUCH:'EDEKA Buch Hofheim',EDEKA_HALLER:'E center Haller Raunheim'};",
    "const MARKET_NAMES={REWE:'REWE Weilbach',GLOBUS:'GLOBUS Hattersheim',EDEKA_BUCH:'EDEKA Buch Hofheim',EDEKA_HALLER:'E center Haller Raunheim'};\nconst MARKET_META={REWE:{address:'Industriestraße 40, 65439 Flörsheim / Weilbach',lat:50.040728,lng:8.444120},GLOBUS:{address:'Heddingheimer Straße 2-4, 65795 Hattersheim',lat:50.071756,lng:8.474116},EDEKA_BUCH:{address:'Chinonplatz 6, 65719 Hofheim',lat:50.085870,lng:8.448530},EDEKA_HALLER:{address:'Flörsheimer Straße 2, 65479 Raunheim',lat:50.008191,lng:8.435327}};\nlet selectedShoppingMarkets=new Set(MARKET_IDS),marketMap=null,marketMarkers={},userMarker=null,userPosition=null;",
    'Markt-Metadaten',
)

old_setview = "function setView(v){offersView.classList.toggle('hidden',v!=='offers');favoritesView.classList.toggle('hidden',v!=='favorites');recipesView.classList.toggle('hidden',v!=='recipes');tabOffers.classList.toggle('active',v==='offers');tabFavorites.classList.toggle('active',v==='favorites');tabRecipes.classList.toggle('active',v==='recipes');if(v==='favorites')renderFavorites();if(v==='recipes')renderRecipes()}"
new_setview = "function setView(v){offersView.classList.toggle('hidden',v!=='offers');favoritesView.classList.toggle('hidden',v!=='favorites');shoppingView.classList.toggle('hidden',v!=='shopping');recipesView.classList.toggle('hidden',v!=='recipes');tabOffers.classList.toggle('active',v==='offers');tabFavorites.classList.toggle('active',v==='favorites');tabShopping.classList.toggle('active',v==='shopping');tabRecipes.classList.toggle('active',v==='recipes');if(v==='favorites')renderFavorites();if(v==='shopping'){renderShopping();setTimeout(initMarketMap,30)}if(v==='recipes')renderRecipes()}"
replace_once(old_setview, new_setview, 'setView')

replace_once(
    "function setRecipeMarket(m){recipeMarket=m;MARKET_IDS.forEach(x=>document.getElementById('r'+x)?.classList.toggle('active',x===m));renderRecipes()}",
    "function setRecipeMarket(m){recipeMarket=m;MARKET_IDS.forEach(x=>document.getElementById('r'+x)?.classList.toggle('active',x===m));renderRecipes()}\nfunction setRecipeStyle(s){recipeStyle=s;renderRecipes()}",
    'Rezeptfilter',
)

shopping_js = r'''
function htmlEsc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function loadShoppingState(){try{const a=JSON.parse(localStorage.getItem('priceArchive.shopping')||'[]');shoppingItems=Array.isArray(a)?a.filter(x=>x&&x.text):[];const m=JSON.parse(localStorage.getItem('priceArchive.markets')||'null');if(Array.isArray(m))selectedShoppingMarkets=new Set(m.filter(x=>MARKET_IDS.includes(x)))}catch(e){shoppingItems=[];selectedShoppingMarkets=new Set(MARKET_IDS)}if(!selectedShoppingMarkets.size)selectedShoppingMarkets=new Set(MARKET_IDS)}
function saveShoppingState(){localStorage.setItem('priceArchive.shopping',JSON.stringify(shoppingItems));localStorage.setItem('priceArchive.markets',JSON.stringify([...selectedShoppingMarkets]))}
function shoppingModeLabel(mode){return mode==='type'?'Produktart':mode==='product'?'Marke / Produkt':'Automatisch'}
function resolveShoppingType(text){const q=norm(text);for(const [type,terms] of TYPE_RULES){if(norm(type)===q||terms.some(term=>norm(term)===q||strictTypeHit(text,term)))return type}const cats=[...new Set(data.map(category))];return cats.find(c=>norm(c)===q)||null}
function shoppingMatchScore(item,p){const q=norm(item.text),mode=item.mode||'auto',resolved=resolveShoppingType(item.text),ptype=productType(p),cat=category(p);const useType=mode==='type'||(mode==='auto'&&!!resolved);if(useType){const target=resolved||item.text;if(norm(ptype)===norm(target))return 220;if(norm(cat)===norm(target))return 170;return 0}const brand=norm(p.brand||''),label=norm(productLabel(p)),name=norm(`${p.name||''} ${p.brand||''}`);if(brand&&brand===q)return 260;if(label===q)return 250;if(name===q)return 240;if((` ${name} `).includes(` ${q} `))return 220;if(q.length>=4&&name.includes(q))return 190;return 0}
function bestShoppingOffer(item,marketId){return data.filter(p=>store(p)===marketId).map(p=>({p,score:shoppingMatchScore(item,p)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||currentPrice(a.p)-currentPrice(b.p))[0]?.p||null}
function addShoppingItem(){const text=shopText.value.trim(),qty=Math.max(1,Number(shopQty.value)||1),mode=shopMode.value;if(!text)return;addShoppingItemText(text,qty,mode);shopText.value='';shopQty.value='1';shopText.focus()}
function addShoppingItemText(text,qty=1,mode='auto',rerender=true){text=String(text||'').trim();if(!text)return;const existing=shoppingItems.find(x=>norm(x.text)===norm(text)&&(x.mode||'auto')===mode);if(existing)existing.qty=(Number(existing.qty)||1)+Math.max(1,Number(qty)||1);else shoppingItems.push({text,qty:Math.max(1,Number(qty)||1),mode});saveShoppingState();if(rerender)renderShopping()}
function removeShoppingItem(i){shoppingItems.splice(i,1);saveShoppingState();renderShopping()}
function clearShoppingList(){shoppingItems=[];saveShoppingState();renderShopping()}
function setShoppingMarket(id,on){if(on)selectedShoppingMarkets.add(id);else selectedShoppingMarkets.delete(id);saveShoppingState();if(marketMarkers[id])marketMarkers[id].setOpacity(selectedShoppingMarkets.has(id)?1:.35);renderShoppingMarkets();renderShoppingResults()}
function toggleShoppingMarket(id){setShoppingMarket(id,!selectedShoppingMarkets.has(id))}
function distanceKm(a,b){const R=6371,toRad=x=>x*Math.PI/180,dLat=toRad(b.lat-a.lat),dLon=toRad(b.lng-a.lng),x=Math.sin(dLat/2)**2+Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*Math.sin(dLon/2)**2;return 2*R*Math.asin(Math.sqrt(x))}
function requestLocation(){if(!navigator.geolocation){locationStatus.textContent='Standortbestimmung wird von diesem Gerät nicht unterstützt.';return}locationStatus.textContent='Standort wird ermittelt …';navigator.geolocation.getCurrentPosition(pos=>{userPosition={lat:pos.coords.latitude,lng:pos.coords.longitude};locationStatus.innerHTML='<span class="location-ok">Standort ermittelt.</span> Er wird nur für Entfernungen und die Karte verwendet und nicht gespeichert.';renderShoppingMarkets();initMarketMap(true)},err=>{locationStatus.textContent='Standort konnte nicht verwendet werden: '+(err.message||'keine Freigabe')},{enableHighAccuracy:false,timeout:10000,maximumAge:300000})}
function initMarketMap(refit=false){if(!window.L||!document.getElementById('marketMap'))return;if(!marketMap){marketMap=L.map('marketMap',{scrollWheelZoom:false}).setView([50.05,8.455],11);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap-Mitwirkende'}).addTo(marketMap);MARKET_IDS.forEach(id=>{const m=MARKET_META[id],marker=L.marker([m.lat,m.lng],{opacity:selectedShoppingMarkets.has(id)?1:.35}).addTo(marketMap).bindTooltip(MARKET_NAMES[id]);marker.on('click',()=>toggleShoppingMarket(id));marketMarkers[id]=marker})}setTimeout(()=>marketMap.invalidateSize(),30);if(userPosition){if(userMarker)userMarker.remove();userMarker=L.circleMarker([userPosition.lat,userPosition.lng],{radius:8,weight:3,fillOpacity:.6}).addTo(marketMap).bindTooltip('Dein Standort');if(refit){const pts=[L.latLng(userPosition.lat,userPosition.lng),...MARKET_IDS.map(id=>L.latLng(MARKET_META[id].lat,MARKET_META[id].lng))];marketMap.fitBounds(L.latLngBounds(pts).pad(.15))}}}
function renderShoppingMarkets(){const rows=MARKET_IDS.map(id=>({id,...MARKET_META[id],dist:userPosition?distanceKm(userPosition,MARKET_META[id]):null})).sort((a,b)=>(a.dist??999)-(b.dist??999));shoppingMarkets.innerHTML=rows.map(m=>`<label class="market-select"><input type="checkbox" ${selectedShoppingMarkets.has(m.id)?'checked':''} onchange="setShoppingMarket('${m.id}',this.checked)"><span><b>${MARKET_NAMES[m.id]}</b><small>${htmlEsc(m.address)}${m.dist!=null?` · ${m.dist.toFixed(1)} km Luftlinie`:''}</small></span></label>`).join('')}
function renderShoppingSuggestions(){if(!data.length)return;const values=new Set();TYPE_RULES.forEach(([type])=>values.add(type));data.forEach(p=>{const b=(p.brand||'').trim(),l=productLabel(p);if(b)values.add(b);if(l&&l.length<45)values.add(l)});shopSuggestions.innerHTML=[...values].sort((a,b)=>a.localeCompare(b,'de')).slice(0,500).map(x=>`<option value="${htmlEsc(x)}"></option>`).join('')}
function renderShoppingList(){shoppingList.innerHTML=shoppingItems.length?shoppingItems.map((x,i)=>`<div class="shop-item"><div><b>${htmlEsc(x.text)}</b><div class="shop-kind">${shoppingModeLabel(x.mode||'auto')}</div></div><span>${Number(x.qty)||1}×</span><button onclick="removeShoppingItem(${i})" aria-label="Entfernen">✕</button></div>`).join('')+'<button class="shop-add" onclick="clearShoppingList()">Liste leeren</button>':'<div class="empty">Deine Einkaufsliste ist noch leer.</div>'}
function shoppingMarketResult(id){const details=shoppingItems.map(item=>{const p=bestShoppingOffer(item,id);return{item,p}}),found=details.filter(x=>x.p),sum=found.reduce((s,x)=>s+currentPrice(x.p)*(Number(x.item.qty)||1),0);return{id,details,found,sum}}
function renderShoppingResults(){if(!shoppingItems.length){shoppingResults.innerHTML='<div class="empty">Füge zuerst Produkte oder Produktarten hinzu.</div>';return}const ids=[...selectedShoppingMarkets];if(!ids.length){shoppingResults.innerHTML='<div class="empty">Wähle mindestens einen Markt aus.</div>';return}const results=ids.map(shoppingMarketResult).sort((a,b)=>b.found.length-a.found.length||a.sum-b.sum);const perMarket=results.map(r=>`<div class="shop-market-result"><h4>${MARKET_NAMES[r.id]}</h4><b>${r.found.length}/${shoppingItems.length} Positionen mit aktuellem Angebot</b>${r.found.length?`<div class="price" style="margin-top:5px">${euro(r.sum)}</div><div class="meta">Summe der gefundenen Angebotsartikel</div>`:''}<ul class="shop-result-list">${r.details.map(x=>x.p?`<li>${htmlEsc(x.item.text)} → ${htmlEsc(x.p.name)} · ${euro(currentPrice(x.p))}${Number(x.item.qty)>1?` × ${Number(x.item.qty)}`:''}</li>`:`<li>${htmlEsc(x.item.text)} → kein aktuelles Angebot gefunden</li>`).join('')}</ul></div>`).join('');const combo=shoppingItems.map(item=>{const opts=ids.map(id=>({id,p:bestShoppingOffer(item,id)})).filter(x=>x.p).sort((a,b)=>currentPrice(a.p)-currentPrice(b.p));return{item,best:opts[0]||null}}),comboFound=combo.filter(x=>x.best),comboSum=comboFound.reduce((s,x)=>s+currentPrice(x.best.p)*(Number(x.item.qty)||1),0),comboMarkets=[...new Set(comboFound.map(x=>x.best.id))];const best=`<div class="shop-best"><h4>Günstigste Kombination der aktuellen Angebote</h4><b>${comboFound.length}/${shoppingItems.length} Positionen gefunden · ${comboMarkets.map(id=>MARKET_NAMES[id]).join(' + ')||'–'}</b>${comboFound.length?`<div class="price" style="margin-top:5px">${euro(comboSum)}</div>`:''}<ul class="shop-result-list">${combo.map(x=>x.best?`<li>${htmlEsc(x.item.text)} → ${MARKET_NAMES[x.best.id]}: ${htmlEsc(x.best.p.name)} · ${euro(currentPrice(x.best.p))}</li>`:`<li>${htmlEsc(x.item.text)} → in keinem ausgewählten Markt als aktuelles Angebot gefunden</li>`).join('')}</ul></div>`;shoppingResults.innerHTML=best+`<div class="shop-summary-grid">${perMarket}</div><div class="shop-note">Wichtig: Das ist noch kein vollständiger Kassenbon-Vergleich. Artikel ohne aktuelles Angebot werden derzeit nicht mit ihrem regulären Ladenpreis ergänzt.</div>`}
function renderShopping(){renderShoppingMarkets();renderShoppingList();renderShoppingSuggestions();renderShoppingResults();if(!shoppingView.classList.contains('hidden'))setTimeout(initMarketMap,30)}
function addRecipeToShopping(i){const r=lastRecipes[i];if(!r)return;r.items.forEach(p=>addShoppingItemText(productType(p),1,'type',false));r.extras.forEach(x=>addShoppingItemText(x,1,'auto',false));saveShoppingState();renderShopping();setView('shopping')}
'''

anchor = 'function marketItems(){return data.filter(p=>store(p)===recipeMarket)}'
if 'function renderShoppingResults()' not in text:
    replace_once(anchor, shopping_js + '\n' + anchor, 'Einkaufsfunktionen')

pattern = r"function renderRecipes\(\)\{.*?\}\nfunction show\(id\)"
new_recipe = r'''function pickNeed(need,used){let rows=marketItems().filter(p=>!used.has(p.id));if(need.types?.length){const exact=rows.filter(p=>need.types.includes(productType(p)));if(exact.length)rows=exact;else if(need.cats?.length)rows=rows.filter(p=>need.cats.includes(category(p)));else return null}else if(need.cats?.length)rows=rows.filter(p=>need.cats.includes(category(p)));return rows.sort((a,b)=>currentPrice(a)-currentPrice(b))[0]||null}
function renderRecipes(){if(!data.length){recipeStatus.textContent='Keine aktuell bestätigten Angebote für Rezepte vorhanden.';recipeGrid.innerHTML='';return}const specs=[
{title:'Gemüse-Pfanne',tags:['gesund','leicht','schnell','guenstig'],needs:[{cats:['Fleisch']},{cats:['Gemüse & Salat']}],extras:['Öl','Salz','Pfeffer'],steps:['Fleisch in wenig Öl anbraten.','Gemüse bissfest mitgaren.','Abschmecken und servieren.']},
{title:'Fisch mit Gemüse',tags:['gesund','leicht'],needs:[{cats:['Fisch & Meeresfrüchte']},{cats:['Gemüse & Salat']}],extras:['Öl','Zitrone','Salz','Pfeffer'],steps:['Gemüse vorbereiten und garen.','Fisch schonend braten oder backen.','Mit Zitrone abschmecken und zusammen anrichten.']},
{title:'Tofu-Gemüse-Wok',tags:['gesund','leicht','vegetarisch','schnell'],needs:[{cats:['Vegetarisch & Vegan']},{cats:['Gemüse & Salat']}],extras:['Sojasauce','Öl'],steps:['Tofu kräftig anbraten.','Gemüse kurz mitbraten.','Mit Sojasauce abschmecken.']},
{title:'Pasta mit Gemüse',tags:['vegetarisch','guenstig','schnell'],needs:[{types:['Pasta & Nudeln'],cats:['Nudeln, Reis & Beilagen']},{cats:['Gemüse & Salat']}],extras:['Olivenöl','Kräuter'],steps:['Pasta kochen.','Gemüse anbraten.','Vermengen und würzen.']},
{title:'Joghurt-Obst-Bowl',tags:['gesund','leicht','vegetarisch','schnell'],needs:[{types:['Joghurt & Skyr'],cats:['Molkerei & Käse']},{cats:['Obst']}],extras:['Zimt'],steps:['Milchprodukt in eine Schüssel geben.','Obst schneiden und darauf verteilen.','Mit etwas Zimt abschließen.']},
{title:'Deftiger Schweinebraten mit Kartoffeln',tags:['deftig'],needs:[{types:['Schweinefleisch'],cats:['Fleisch']},{types:['Kartoffeln'],cats:['Gemüse & Salat']}],extras:['Zwiebeln','Brühe','Salz','Pfeffer'],steps:['Fleisch kräftig anbraten.','Zwiebeln zugeben, mit Brühe ablöschen und schmoren.','Kartoffeln garen und zum Braten servieren.']},
{title:'Hackfleisch-Kartoffel-Pfanne',tags:['deftig','guenstig'],needs:[{types:['Hackfleisch'],cats:['Fleisch']},{types:['Kartoffeln'],cats:['Gemüse & Salat']}],extras:['Zwiebeln','Paprikapulver','Salz','Pfeffer'],steps:['Hackfleisch krümelig anbraten.','Kartoffeln und Zwiebeln zugeben und garen.','Kräftig würzen und heiß servieren.']},
{title:'Cremige Käse-Pasta',tags:['deftig','vegetarisch','guenstig'],needs:[{types:['Pasta & Nudeln'],cats:['Nudeln, Reis & Beilagen']},{types:['Käse'],cats:['Molkerei & Käse']}],extras:['Milch oder Sahne','Pfeffer'],steps:['Pasta kochen.','Käse mit etwas Milch oder Sahne schmelzen.','Pasta unterheben und kräftig pfeffern.']}
],out=[];for(const spec of specs){if(recipeStyle!=='alle'&&!spec.tags.includes(recipeStyle))continue;const used=new Set(),items=[];for(const need of spec.needs){const p=pickNeed(need,used);if(p){items.push(p);used.add(p.id)}}if(items.length===spec.needs.length)out.push({...spec,items})}lastRecipes=out;const marketName=MARKET_NAMES[recipeMarket]||recipeMarket;recipeStatus.textContent=`${out.length} passende Rezeptvorschläge · ${recipeStyle==='alle'?'alle Richtungen':recipeStyle==='guenstig'?'günstig':recipeStyle} · nur aktuelle Angebote von ${marketName}`;recipeGrid.innerHTML=out.map((r,i)=>`<article class="recipe"><span class="store ${recipeMarket==='GLOBUS'?'globus':recipeMarket.startsWith('EDEKA_')?'edeka':''}">${marketName}</span><h3>${r.title}</h3><div class="recipe-tags">${r.tags.map(x=>x==='guenstig'?'günstig':x).join(' · ')}</div><b>Im Angebot:</b><ul>${r.items.map(p=>`<li>${p.name} · ${euro(currentPrice(p))}</li>`).join('')}</ul><b>Zusätzlich:</b><ul>${r.extras.map(x=>`<li>${x}</li>`).join('')}</ul><ol>${r.steps.map(x=>`<li>${x}</li>`).join('')}</ol><button class="recipe-add" onclick="addRecipeToShopping(${i})">🛒 Zutaten auf Einkaufsliste</button></article>`).join('')||`<div class="empty">Aktuell keine passenden Kombinationen für ${marketName} in dieser Richtung.</div>`}
function show(id)'''
text2, n = re.subn(pattern, new_recipe, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Rezeptfunktion konnte nicht ersetzt werden')
text = text2

old_load = "async function load(){loadFavorites();try{const r=await fetch('./data/offers.json?'+Date.now());if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();archive=d.products||[];data=archive.filter(p=>p.active===true);drawFilters();render();renderFavorites();renderRecipes();const stand=d.updated_at?new Date(d.updated_at).toLocaleString('de-DE'):'unbekannt';status.textContent=data.length?`${data.length} aktuell gültige Angebote · ${archive.length} Produkte im Preisarchiv · Stand ${stand}`:`Keine als aktuell bestätigten Angebote vorhanden. Archiviert: ${archive.length} Produkte · letzter Datenstand ${stand}`;}catch(e){status.textContent='Fehler beim Laden: '+e.message}}"
new_load = "async function load(){loadFavorites();loadShoppingState();try{const r=await fetch('./data/offers.json?'+Date.now());if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();archive=d.products||[];data=archive.filter(p=>p.active===true);drawFilters();render();renderFavorites();renderShopping();renderRecipes();const stand=d.updated_at?new Date(d.updated_at).toLocaleString('de-DE'):'unbekannt';status.textContent=data.length?`${data.length} aktuell gültige Angebote · ${archive.length} Produkte im Preisarchiv · Stand ${stand}`:`Keine als aktuell bestätigten Angebote vorhanden. Archiviert: ${archive.length} Produkte · letzter Datenstand ${stand}`;}catch(e){status.textContent='Fehler beim Laden: '+e.message}}"
replace_once(old_load, new_load, 'load()')

replace_once(
    "q.oninput=render;modal.onclick=e=>{if(e.target===modal)modal.classList.remove('open')};load();",
    "q.oninput=render;shopText.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addShoppingItem()}};modal.onclick=e=>{if(e.target===modal)modal.classList.remove('open')};load();",
    'Eventhandler',
)

path.write_text(text, encoding='utf-8')

required = [
    'tabShopping', 'shoppingView', 'marketMap', 'addShoppingItem',
    'renderShoppingResults', 'requestLocation', 'Deftiger Schweinebraten',
    'addRecipeToShopping', 'leaflet@1.9.4',
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit('Fehlt: ' + ', '.join(missing))
print('Einkaufsplaner erfolgreich eingebaut')
