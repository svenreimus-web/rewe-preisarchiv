from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')
pat=re.compile(r"function resolveShoppingType\(text\)\{.*?\}\nfunction shoppingMatchScore\(item,p\)\{.*?\}\nfunction bestShoppingOffer\(item,marketId\)\{.*?\}\n",re.S)
new=r'''const shoppingOfferCache=new Map(),shoppingTypeCache=new Map(),shoppingMetaCache=new WeakMap();
function shoppingMeta(p){let m=shoppingMetaCache.get(p);if(m)return m;m={market:store(p),ptype:productType(p),cat:category(p),brand:norm(p.brand||''),label:norm(productLabel(p)),name:norm(`${p.name||''} ${p.brand||''}`),price:currentPrice(p)};shoppingMetaCache.set(p,m);return m}
function resolveShoppingType(text){const q=norm(text);if(shoppingTypeCache.has(q))return shoppingTypeCache.get(q);let found=null;for(const [type,terms] of TYPE_RULES){if(norm(type)===q||terms.some(term=>norm(term)===q||strictTypeHit(text,term))){found=type;break}}if(!found){const cats=[...new Set(data.map(category))];found=cats.find(c=>norm(c)===q)||null}shoppingTypeCache.set(q,found);return found}
function shoppingMatchScore(item,p){const q=norm(item.text),mode=item.mode||'auto',resolved=resolveShoppingType(item.text),m=shoppingMeta(p);const useType=mode==='type'||(mode==='auto'&&!!resolved);if(useType){const target=resolved||item.text;if(norm(m.ptype)===norm(target))return 220;if(norm(m.cat)===norm(target))return 170;return 0}if(m.brand&&m.brand===q)return 260;if(m.label===q)return 250;if(m.name===q)return 240;if((` ${m.name} `).includes(` ${q} `))return 220;if(q.length>=4&&m.name.includes(q))return 190;return 0}
function bestShoppingOffer(item,marketId){const key=`${marketId}|${item.mode||'auto'}|${norm(item.text)}`;if(shoppingOfferCache.has(key))return shoppingOfferCache.get(key);let best=null,bestScore=0,bestPrice=Infinity;for(const p of data){const m=shoppingMeta(p);if(m.market!==marketId)continue;const score=shoppingMatchScore(item,p);if(score>bestScore||(score===bestScore&&score>0&&m.price<bestPrice)){best=p;bestScore=score;bestPrice=m.price}}shoppingOfferCache.set(key,best);return best}
'''
s2,n=pat.subn(new,s,count=1)
if n!=1:
    raise SystemExit(f'Patchstelle nicht eindeutig gefunden: {n}')
p.write_text(s2,encoding='utf-8')
print('Shopping-Vergleich auf Cache/Index umgestellt')
