from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="function renderShoppingResults(){if(!shoppingItems.length){shoppingResults.innerHTML='<div class=\"empty\">Füge zuerst Produkte oder Produktarten hinzu.</div>';return}const ids=[...selectedShoppingMarkets];if(!ids.length){shoppingResults.innerHTML='<div class=\"empty\">Wähle mindestens einen Markt aus.</div>';return}"
new="function renderShoppingResults(force=false){if(!shoppingItems.length){shoppingResults.innerHTML='<div class=\"empty\">Füge zuerst Produkte oder Produktarten hinzu.</div>';return}const ids=[...selectedShoppingMarkets];if(!ids.length){shoppingResults.innerHTML='<div class=\"empty\">Wähle mindestens einen Markt aus.</div>';return}if(!force){shoppingResults.innerHTML='<button class=\"shop-add\" onclick=\"renderShoppingResults(true)\">Preise vergleichen</button><div class=\"shop-note\">Die Liste kann erst vollständig erstellt werden. Der Preisvergleich startet erst, wenn du ihn antippst.</div>';return}"
if old not in s:
    raise SystemExit('Start von renderShoppingResults nicht gefunden')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Preisvergleich auf manuelles Starten umgestellt')
