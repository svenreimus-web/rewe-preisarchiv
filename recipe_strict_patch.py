from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

old="function pickNeed(need,used){let rows=marketItems().filter(p=>!used.has(p.id));if(need.types?.length){const exact=rows.filter(p=>need.types.includes(productType(p)));if(exact.length)rows=exact;else if(need.cats?.length)rows=rows.filter(p=>need.cats.includes(category(p)));else return null}else if(need.cats?.length)rows=rows.filter(p=>need.cats.includes(category(p)));return rows.sort((a,b)=>currentPrice(a)-currentPrice(b))[0]||null}"
new="function recipeAnimalProduct(p){const t=productType(p),c=category(p),text=norm(`${p.name||''} ${p.brand||''}`);if(['Hackfleisch','Rindfleisch','Schweinefleisch','Geflügel','Fisch','Garnelen','Wurst & Aufschnitt'].includes(t))return true;if(['Fleisch','Fisch & Meeresfrüchte'].includes(c))return true;return /\\b(hackfleisch|rind|rinder|schwein|schweine|hahnchen|hähnchen|pute|geflugel|geflügel|huhn|hühner|fisch|lachs|forelle|dorade|makrele|matjes|hering|garnele|shrimp|wurst|salami|schinken)\\b/.test(text)}\nfunction pickNeed(need,used){let rows=marketItems().filter(p=>!used.has(p.id));if(need.types?.length){rows=rows.filter(p=>need.types.includes(productType(p)));if(!rows.length)return null}else if(need.cats?.length){rows=rows.filter(p=>need.cats.includes(category(p)))}return rows.sort((a,b)=>currentPrice(a)-currentPrice(b))[0]||null}"
if old not in s: raise SystemExit('pickNeed anchor not found')
s=s.replace(old,new,1)
old2="for(const need of spec.needs){const p=pickNeed(need,used);if(p){items.push(p);used.add(p.id)}}if(items.length===spec.needs.length)out.push({...spec,items})"
new2="for(const need of spec.needs){const p=pickNeed(need,used);if(p&&!(spec.tags.includes('vegetarisch')&&recipeAnimalProduct(p))){items.push(p);used.add(p.id)}}if(items.length===spec.needs.length)out.push({...spec,items})"
if old2 not in s: raise SystemExit('recipe loop anchor not found')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('strict recipe matching applied')
