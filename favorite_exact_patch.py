from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

old="function isProductFavorite(p){const key=productKey(p),text=`${p.name||''} ${p.brand||''}`;return favoriteProducts.has(key)||[...favoriteProducts].some(k=>k.length>=3&&lexicalQueryHit(text,k))}"
new="function isProductFavorite(p){return favoriteProducts.has(productKey(p))}"
if old not in s: raise SystemExit('isProductFavorite anchor not found')
s=s.replace(old,new,1)

pattern=r"function renderFavorites\(\)\{.*?\}\n\nfunction htmlEsc"
replacement="""function renderFavorites(){const allRows=data.filter(p=>favoriteProducts.has(productKey(p))||favoriteTypes.has(productType(p)));const rows=allRows.filter(p=>favoriteMarket==='Alle'||store(p)===favoriteMarket).filter(p=>favoriteProducts.has(productKey(p))||favoriteTypes.has(productType(p))).sort((a,b)=>productType(a).localeCompare(productType(b),'de')||a.name.localeCompare(b.name,'de',{sensitivity:'base'}));const marketText=favoriteMarket==='Alle'?'alle Märkte':(MARKET_NAMES[favoriteMarket]||favoriteMarket);favoriteStatus.textContent=`${favoriteProducts.size} Produktfavoriten · ${favoriteTypes.size} favorisierte Produktarten · ${rows.length} passende aktuelle Angebote · ${marketText}`;favoriteGrid.innerHTML=rows.map(cardHtml).join('')||'<div class=\"empty\">Keine passenden aktuellen Favoriten in diesem Markt.</div>'}

function htmlEsc"""
s,n=re.subn(pattern,lambda m:replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'renderFavorites block not found: {n}')
p.write_text(s,encoding='utf-8')
print('exact favorite matching applied')
