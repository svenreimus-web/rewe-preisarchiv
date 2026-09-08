from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

old_phrase="function phraseHit(hay,phrase){const p=norm(phrase),tokens=hay.split(' ');return (` ${hay} `).includes(` ${p} `)||(p.length>=5&&tokens.some(t=>t.length>=5&&(t.includes(p)||p.includes(t))))}"
new_phrase=r'''const MATCH_INFLECTIONS=new Set(['','e','en','er','n','s','es']);
const MATCH_COMPOUND_PREFIXES=new Set(['schwein','schweine','rind','rinder','hahnchen','hähnchen','pute','puten','fisch','lachs','kartoffel','apfel','äpfel']);
function lexicalTokens(text){return norm(text).split(' ').filter(Boolean)}
function lexicalRuleTokenHit(token,rule){if(token===rule)return true;if(token.startsWith(rule)&&MATCH_INFLECTIONS.has(token.slice(rule.length)))return true;return MATCH_COMPOUND_PREFIXES.has(rule)&&token.startsWith(rule)}
function lexicalRuleHit(text,phrase){const hay=lexicalTokens(text),parts=lexicalTokens(phrase);if(!hay.length||!parts.length)return false;if(parts.length===1)return hay.some(token=>lexicalRuleTokenHit(token,parts[0]));for(let i=0;i<=hay.length-parts.length;i++){let ok=true;for(let j=0;j<parts.length;j++){if(!lexicalRuleTokenHit(hay[i+j],parts[j])){ok=false;break}}if(ok)return true}return false}
function lexicalQueryHit(text,query){const hay=lexicalTokens(text),terms=lexicalTokens(query);if(!terms.length)return true;return terms.every(term=>hay.some(token=>token===term||token.startsWith(term)))}
function phraseHit(hay,phrase){return lexicalRuleHit(hay,phrase)}'''
if old_phrase not in s:
    raise SystemExit('phraseHit nicht gefunden')
s=s.replace(old_phrase,new_phrase,1)

old_strict="function strictTypeHit(text,term){const hay=norm(text),p=norm(term);if(!hay||!p)return false;if((` ${hay} `).includes(` ${p} `))return true;if(p.includes(' '))return false;return hay.split(' ').some(token=>{if(!token.startsWith(p))return false;const suffix=token.slice(p.length);return ['','e','en','er','n','s'].includes(suffix)})}"
new_strict="function strictTypeHit(text,term){return lexicalRuleHit(text,term)}"
if old_strict not in s:
    raise SystemExit('strictTypeHit nicht gefunden')
s=s.replace(old_strict,new_strict,1)

# Wein-Compounds explizit modellieren statt unsicherem Teilstring-Matching.
s=s.replace("['Wein',['wein','riesling'", "['Wein',['wein','rotwein','weisswein','weißwein','riesling'", 1)

old_fav="function isProductFavorite(p){const key=productKey(p),hay=norm(p.name||'');return favoriteProducts.has(key)||[...favoriteProducts].some(k=>k.length>=3&&hay.includes(k))}"
new_fav="function isProductFavorite(p){const key=productKey(p),text=`${p.name||''} ${p.brand||''}`;return favoriteProducts.has(key)||[...favoriteProducts].some(k=>k.length>=3&&lexicalQueryHit(text,k))}"
if old_fav not in s:
    raise SystemExit('isProductFavorite nicht gefunden')
s=s.replace(old_fav,new_fav,1)

s,n=re.subn(r"function searchMatches\(p,query\)\{.*?\}\nfunction render\(\)", "function searchMatches(p,query){return lexicalQueryHit(`${p.name||''} ${p.brand||''} ${p.quantity||''} ${productType(p)||''} ${category(p)||''}`,query)}\nfunction render()", s, count=1, flags=re.S)
if n!=1:
    raise SystemExit(f'searchMatches nicht eindeutig: {n}')

old_shop="if((` ${m.name} `).includes(` ${q} `))return 220;if(q.length>=4&&m.name.includes(q))return 190;"
new_shop="if(lexicalQueryHit(m.name,item.text))return 220;"
if old_shop not in s:
    raise SystemExit('Shopping-Teilstring-Matching nicht gefunden')
s=s.replace(old_shop,new_shop,1)

p.write_text(s,encoding='utf-8')
print('Matching zentralisiert: Kategorie, Produktart, Suche, Favoriten und Einkauf verwenden gemeinsame Lexik-Regeln.')
