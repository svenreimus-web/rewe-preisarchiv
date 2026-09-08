from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1) Einkaufseinheiten und Mengenempfehlungen: Getränke als definierte Kästen,
# Butter/Margarine als Packung statt Gramm.
pattern=r"function recommendShoppingUnit\(text\)\{.*?\}\nfunction recommendShoppingAmount\(text\)\{.*?\}\nfunction applyShoppingSuggestion"
replacement=r'''function recommendShoppingUnit(text){const t=resolveShoppingType(text);if(['Wasser','Bier','Saft','Cola & Limonade'].includes(t))return 'Kasten';if(['Butter','Margarine'].includes(t))return 'Packung';if(['Pasta & Nudeln','Wurst & Aufschnitt','Käse','Hackfleisch','Rindfleisch','Schweinefleisch','Geflügel','Fisch','Garnelen'].includes(t))return 'g';if(t==='Milch')return 'l';if(t==='Eier')return 'Stück';if(['Kartoffeln','Äpfel','Bananen','Tomaten','Paprika','Zwiebeln'].includes(t))return 'kg';return 'Packung'}
function recommendShoppingAmount(text){const t=resolveShoppingType(text),a=household.adults,c=household.children,cp=CHILD_MEAL_G[household.childAge]||CHILD_MEAL_G['7-9'];if(t==='Wasser'){const liters=(a*1500+c*(CHILD_WEEKLY_WATER_ML[household.childAge]||900))*7/1000;return{amount:1,unit:'Kasten',note:`1 Kasten Wasser = 12 Flaschen. Zur Orientierung liegt die Wochen-Trinkmenge dieses Haushalts grob bei ${liters.toFixed(1).replace('.',',')} l; die Kastenanzahl bleibt bewusst manuell änderbar.`}}if(t==='Bier')return{amount:1,unit:'Kasten',note:'1 Kasten Bier = 20 Flaschen. 6er-, 11er- oder 24er-Gebinde werden bei dieser Auswahl nicht als Kasten verglichen.'};if(t==='Cola & Limonade')return{amount:1,unit:'Kasten',note:'1 Kasten Cola/Limo = 12 Flaschen. Andere Mehrfachgebinde werden nicht als Standardkasten gewertet.'};if(t==='Saft')return{amount:1,unit:'Kasten',note:'1 Kasten Saft = 6 Flaschen. Andere Mehrfachgebinde werden nicht als Standardkasten gewertet.'};if(t==='Butter')return{amount:1,unit:'Packung',note:'Butter wird als Packung gekauft. Für den Vergleich gelten handelsübliche Packungen um 250 g; Miniportionen werden ausgeschlossen.'};if(t==='Margarine')return{amount:1,unit:'Packung',note:'Margarine wird als Packung/Becher gekauft. Für den Vergleich gelten übliche Gebinde von etwa 400–450 g.'};if(t==='Pasta & Nudeln')return{amount:Math.round(a*125+c*cp.pasta),unit:'g',note:'Startwert für eine Nudelmahlzeit: 125 g trockene Nudeln je Erwachsenem, für Kinder altersabhängig kleiner.'};if(t==='Wurst & Aufschnitt'){const cw={'1-3':15,'4-6':20,'7-9':20,'10-12':25,'13-14':25,'15-18':30}[household.childAge]||20;return{amount:Math.max(30,Math.round(a*60+c*cw*2)),unit:'g',note:'Wochen-Startwert: Erwachsene 2 × 30 g Wurst. Kinderportionen werden altersabhängig kleiner skaliert.'}}if(t==='Käse')return{amount:Math.max(30,Math.round(a*30+c*cp.cheese)),unit:'g',note:'Startwert für eine Haushaltsportion: 30 g Käse je Erwachsenem, Kinder altersabhängig kleiner. Die Zahl der Käsemahlzeiten pro Woche bleibt bewusst dir überlassen.'};if(['Hackfleisch','Rindfleisch','Schweinefleisch','Geflügel','Fisch'].includes(t))return{amount:Math.round(a*120+c*cp.meat),unit:'g',note:'Startwert für eine Hauptmahlzeit: etwa 120 g je Erwachsenem, Kinder altersabhängig kleiner.'};if(t==='Milch')return{amount:Math.max(.5,Math.round((a*.25+c*.2)*10)/10),unit:'l',note:'Startwert für eine Milchportion im Haushalt; bei täglichem Verbrauch entsprechend erhöhen.'};if(t==='Eier')return{amount:Math.max(1,Math.round(a*1+c*2)),unit:'Stück',note:'Grobe Wochenorientierung; Eier in verarbeiteten Lebensmitteln sind darin nicht enthalten.'};if(t==='Kartoffeln')return{amount:Math.round((a*.25+c*.15)*10)/10,unit:'kg',note:'Startwert für eine Kartoffelmahlzeit: etwa 250 g je Erwachsenem, Kinder kleiner angesetzt.'};return{amount:1,unit:recommendShoppingUnit(text),note:''}}
function applyShoppingSuggestion'''
ns,n=re.subn(pattern,lambda m: replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'Empfehlungsblock nicht eindeutig gefunden: {n}')
s=ns

# 2) Gebindeparser, Standardkästen und lesbare Bedarfsanzeige.
pattern=r"function formatShoppingAmount\(item\)\{.*?\}\nfunction parseOfferPackage\(p\)\{.*?\}\nfunction shoppingOfferCount\(item,p\)\{.*?\}"
replacement=r'''const CRATE_SPECS={Bier:{count:20,label:'20 Flaschen'},Wasser:{count:12,label:'12 Flaschen'},'Cola & Limonade':{count:12,label:'12 Flaschen'},Saft:{count:6,label:'6 Flaschen'}};
function crateSpecForText(text){return CRATE_SPECS[resolveShoppingType(text)]||null}
function formatShoppingAmount(item){const n=Number(item.amount)||1,shown=Number.isInteger(n)?String(n):String(Math.round(n*10)/10).replace('.',','),unit=item.unit||'Packung';if(unit==='Kasten'){const spec=crateSpecForText(item.text);if(spec)return `${shown} Kasten (${spec.label})`}return `${shown} ${unit}`}
function parseOfferPackage(p){const raw=String(`${p.name||''} ${p.quantity||''}`).toLowerCase().replace(/,/g,'.');let m=raw.match(/(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[- ]?(kg|g|l|ml)\b/i);if(m){const count=Number(m[1]),v=Number(m[2]),u=m[3].toLowerCase();return{kind:(u==='kg'||u==='g')?'mass':'volume',base:count*v*(u==='kg'?1000:u==='l'?1000:1),count,each:v,unit:u}}m=raw.match(/(\d+(?:\.\d+)?)\s*[- ]?(kg|g|l|ml)\b/i);if(!m)return null;const v=Number(m[1]),u=m[2].toLowerCase();return{kind:(u==='kg'||u==='g')?'mass':'volume',base:v*(u==='kg'?1000:u==='l'?1000:1),count:1,each:v,unit:u}}
function parseDrinkMultipack(p){const raw=String(`${p.name||''} ${p.quantity||''}`);const m=raw.match(/\b(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*[- ]?\s*(?:l|ml)\b/i);return m?{count:Number(m[1]),each:Number(m[2].replace(',','.'))}:null}
function offerPackInfo(p){const q=String(p.quantity||'').trim();if(!q)return '';const short=q.length>64?q.slice(0,61)+'…':q;return ` · Gebinde: ${htmlEsc(short)}`}
function purchaseUnitWord(item,count){if((item.unit||'')==='Kasten')return count===1?'Kasten':'Kästen';return count===1?'Packung':'Packungen'}
function shoppingOfferCount(item,p){const amount=Math.max(.1,Number(item.amount)||1),unit=item.unit||'Packung';if(['Stück','Packung','Kasten','Flasche','Becher','Dose','Glas','Bund','Netz','Rolle'].includes(unit))return Math.max(1,Math.ceil(amount));const pack=parseOfferPackage(p);if(!pack)return 1;const need=(unit==='kg'||unit==='l')?amount*1000:amount;if((unit==='g'||unit==='kg')&&pack.kind!=='mass')return 1;if((unit==='ml'||unit==='l')&&pack.kind!=='volume')return 1;return Math.max(1,Math.ceil(need/pack.base))}'''
ns,n=re.subn(pattern,lambda m: replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'Gebindeblock nicht eindeutig gefunden: {n}')
s=ns

# 3) Kasten muss zur Produktart passen; Butter/Margarine nur in plausibler Packungsgröße.
old="function shoppingUnitCompatible(item,p){if((item.unit||'')!=='Kasten')return true;const raw=norm(`${p.name||''} ${p.quantity||''}`);return raw.includes('kasten')||/\\b\\d+\\s*[x×]\\s*\\d+(?:[.,]\\d+)?\\s*[- ]?\\s*(?:l|ml)\\b/i.test(String(p.quantity||''))}"
new="function shoppingUnitCompatible(item,p){const unit=item.unit||'Packung',t=resolveShoppingType(item.text)||productType(p);if(unit==='Kasten'){const spec=CRATE_SPECS[t],mp=parseDrinkMultipack(p);if(spec)return !!mp&&mp.count===spec.count;return !!mp&&norm(`${p.name||''} ${p.quantity||''}`).includes('kasten')}if(unit==='Packung'&&(t==='Butter'||t==='Margarine')){const pack=parseOfferPackage(p);if(!pack||pack.kind!=='mass')return false;if(t==='Butter')return pack.base>=200&&pack.base<=300;if(t==='Margarine')return pack.base>=350&&pack.base<=500}return true}"
if old not in s: raise SystemExit('shoppingUnitCompatible nicht gefunden')
s=s.replace(old,new,1)

# 4) Im Ergebnis tatsächliches Gebinde anzeigen und bei mehreren Kästen nicht "Packungen" schreiben.
s=s.replace("${htmlEsc(x.p.name)} · ${euro(currentPrice(x.p))}","${htmlEsc(x.p.name)}${offerPackInfo(x.p)} · ${euro(currentPrice(x.p))}")
s=s.replace("${htmlEsc(x.best.p.name)} · ${euro(currentPrice(x.best.p))}","${htmlEsc(x.best.p.name)}${offerPackInfo(x.best.p)} · ${euro(currentPrice(x.best.p))}")
s=s.replace("${x.count>1?` × ${x.count} Packungen`:''}","${x.count>1?` × ${x.count} ${purchaseUnitWord(x.item,x.count)}`:''}")

# 5) Marktübergreifende Kombination nach tatsächlichen Kosten der benötigten Gebinde sortieren.
s=s.replace(".filter(x=>x.p).sort((a,b)=>currentPrice(a.p)-currentPrice(b.p));return{item,best:opts[0]||null}",".filter(x=>x.p).sort((a,b)=>currentPrice(a.p)*shoppingOfferCount(item,a.p)-currentPrice(b.p)*shoppingOfferCount(item,b.p));return{item,best:opts[0]||null}")
s=s.replace(".filter(x=>x.p).sort((a,b)=>currentPrice(a.p)-currentPrice(b.p));const best=opts[0]||null;return{item,best,count:best?shoppingOfferCount(item,best.p):0}",".filter(x=>x.p).sort((a,b)=>currentPrice(a.p)*shoppingOfferCount(item,a.p)-currentPrice(b.p)*shoppingOfferCount(item,b.p));const best=opts[0]||null;return{item,best,count:best?shoppingOfferCount(item,best.p):0}")

p.write_text(s,encoding='utf-8')
print('Packungs- und Kastenlogik aktualisiert')
