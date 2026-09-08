from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# separate state for favorites market filter
old="let data=[],archive=[],selected='Alle',market='Alle',recipeMarket='REWE',recipeStyle='alle',shoppingItems=[]"
new="let data=[],archive=[],selected='Alle',market='Alle',favoriteMarket='Alle',recipeMarket='REWE',recipeStyle='alle',shoppingItems=[]"
if old not in s: raise SystemExit('state anchor not found')
s=s.replace(old,new,1)

# add market buttons to favorites intro
old='<section id="favoritesView" class="hidden"><div class="fav-intro"><h2>Meine Favoriten</h2><div class="hint">★ links merkt das konkrete Produkt. ★ rechts merkt die Produktart, z. B. Bier. Angezeigt werden nur aktuell gültige Angebote.</div></div><div id="favoriteStatus" class="status"></div><div id="favoriteGrid" class="grid"></div></section>'
new='''<section id="favoritesView" class="hidden"><div class="fav-intro"><h2>Meine Favoriten</h2><div class="hint">★ links merkt das konkrete Produkt. ★ rechts merkt die Produktart, z. B. Bier. Angezeigt werden nur aktuell gültige Angebote.</div><div class="markets" style="margin-top:12px"><button id="fmAlle" class="marketbtn active" onclick="setFavoriteMarket(\'Alle\')">Alle Märkte</button><button id="fmREWE" class="marketbtn" onclick="setFavoriteMarket(\'REWE\')">REWE Weilbach</button><button id="fmGLOBUS" class="marketbtn" onclick="setFavoriteMarket(\'GLOBUS\')">GLOBUS Hattersheim</button><button id="fmEDEKA_BUCH" class="marketbtn" onclick="setFavoriteMarket(\'EDEKA_BUCH\')">EDEKA Buch Hofheim</button><button id="fmEDEKA_HALLER" class="marketbtn" onclick="setFavoriteMarket(\'EDEKA_HALLER\')">E center Haller Raunheim</button></div></div><div id="favoriteStatus" class="status"></div><div id="favoriteGrid" class="grid"></div></section>'''
if old not in s: raise SystemExit('favorites section anchor not found')
s=s.replace(old,new,1)

# replace renderFavorites and add setter
pattern=r"function renderFavorites\(\)\{.*?\}\n\nfunction htmlEsc"
replacement='''function setFavoriteMarket(m){favoriteMarket=m;MARKET_IDS.concat(['Alle']).forEach(id=>{const b=document.getElementById('fm'+id);if(b)b.classList.toggle('active',id===m)});renderFavorites()}
function renderFavorites(){const allRows=data.filter(p=>isProductFavorite(p)||isTypeFavorite(p));const rows=allRows.filter(p=>favoriteMarket==='Alle'||store(p)===favoriteMarket).sort((a,b)=>productType(a).localeCompare(productType(b),'de')||a.name.localeCompare(b.name,'de',{sensitivity:'base'}));const marketText=favoriteMarket==='Alle'?'alle Märkte':(MARKET_NAMES[favoriteMarket]||favoriteMarket);favoriteStatus.textContent=`${favoriteProducts.size} Produktfavoriten · ${favoriteTypes.size} favorisierte Produktarten · ${rows.length} passende aktuelle Angebote · ${marketText}`;favoriteGrid.innerHTML=rows.map(cardHtml).join('')||'<div class="empty">Keine passenden aktuellen Favoriten in diesem Markt.</div>'}

function htmlEsc'''
ns,n=re.subn(pattern,lambda m:replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'renderFavorites block not found: {n}')
s=ns
p.write_text(s,encoding='utf-8')
print('favorite market filter added')
