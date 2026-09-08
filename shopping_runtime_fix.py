from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="if(!found)found=shoppingCategoryNames.find(c=>norm(c)===q)||nullshoppingTypeCache.set(q,found);return found}"
new="if(!found)found=shoppingCategoryNames.find(c=>norm(c)===q)||null;shoppingTypeCache.set(q,found);return found}"
if old not in s:
    raise SystemExit('Fehlerstelle nicht gefunden')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('resolveShoppingType Laufzeitfehler korrigiert')
