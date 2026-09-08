from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="function render(){const s=norm(q.value),rows=data.filter(p=>!s||norm(`${p.name} ${p.brand||''} ${p.quantity||''}`).includes(s)).filter(p=>selected==='Alle'||category(p)===selected).filter(p=>market==='Alle'||store(p)===market).sort((a,b)=>a.name.localeCompare(b.name,'de',{sensitivity:'base'}));grid.innerHTML=rows.map(cardHtml).join('')||'<div class=\"empty\">Keine aktuell gültigen Angebote in diesem Filter gefunden.</div>'}"
new="function searchMatches(p,query){const terms=norm(query).split(/\\s+/).filter(Boolean);if(!terms.length)return true;const text=norm(`${p.name||''} ${p.brand||''} ${p.quantity||''} ${productType(p)||''} ${category(p)||''}`),tokens=text.split(' ').filter(Boolean);return terms.every(term=>tokens.some(token=>token===term||token.startsWith(term)))}\nfunction render(){const s=q.value.trim(),rows=data.filter(p=>searchMatches(p,s)).filter(p=>selected==='Alle'||category(p)===selected).filter(p=>market==='Alle'||store(p)===market).sort((a,b)=>a.name.localeCompare(b.name,'de',{sensitivity:'base'}));grid.innerHTML=rows.map(cardHtml).join('')||'<div class=\"empty\">Keine aktuell gültigen Angebote in diesem Filter gefunden.</div>'}"
if old not in s:
    raise SystemExit('Render-Suchstelle nicht gefunden')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Suche auf wortbasierte Treffer umgestellt')
