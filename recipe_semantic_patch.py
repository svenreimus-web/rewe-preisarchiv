from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Add strict Tofu product type before generic fallback categories.
needle=" ['Garnelen',['garnele','shrimp']],\n"
if needle not in s:
    raise SystemExit('TYPE_RULES anchor not found')
s=s.replace(needle, needle+" ['Tofu',['tofu']],\n", 1)

# Make recipe names and required main ingredients semantically exact.
repls={
"{title:'Gemüse-Pfanne',tags:['gesund','leicht','schnell','guenstig'],needs:[{cats:['Fleisch']},{cats:['Gemüse & Salat']}],extras:['Öl','Salz','Pfeffer'],steps:['Fleisch in wenig Öl anbraten.','Gemüse bissfest mitgaren.','Abschmecken und servieren.']}":
"{title:'Fleisch-Gemüse-Pfanne',tags:['gesund','leicht','schnell','guenstig'],needs:[{types:['Geflügel','Schweinefleisch','Rindfleisch','Hackfleisch']},{cats:['Gemüse & Salat']}],extras:['Öl','Salz','Pfeffer'],steps:['Fleisch in wenig Öl anbraten.','Gemüse bissfest mitgaren.','Abschmecken und servieren.']}",
"{title:'Fisch mit Gemüse',tags:['gesund','leicht'],needs:[{cats:['Fisch & Meeresfrüchte']},{cats:['Gemüse & Salat']}],extras:['Öl','Zitrone','Salz','Pfeffer'],steps:['Gemüse vorbereiten und garen.','Fisch schonend braten oder backen.','Mit Zitrone abschmecken und zusammen anrichten.']}":
"{title:'Fisch mit Gemüse',tags:['gesund','leicht'],needs:[{types:['Fisch']},{cats:['Gemüse & Salat']}],extras:['Öl','Zitrone','Salz','Pfeffer'],steps:['Gemüse vorbereiten und garen.','Fisch schonend braten oder backen.','Mit Zitrone abschmecken und zusammen anrichten.']}",
"{title:'Tofu-Gemüse-Wok',tags:['gesund','leicht','vegetarisch','schnell'],needs:[{cats:['Vegetarisch & Vegan']},{cats:['Gemüse & Salat']}],extras:['Sojasauce','Öl'],steps:['Tofu kräftig anbraten.','Gemüse kurz mitbraten.','Mit Sojasauce abschmecken.']}":
"{title:'Tofu-Gemüse-Wok',tags:['gesund','leicht','vegetarisch','schnell'],needs:[{types:['Tofu']},{cats:['Gemüse & Salat']}],extras:['Sojasauce','Öl'],steps:['Tofu kräftig anbraten.','Gemüse kurz mitbraten.','Mit Sojasauce abschmecken.']}"
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit('recipe anchor not found: '+old[:40])
    s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('recipe semantics tightened')
