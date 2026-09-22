from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

css_anchor = ".sub,.status,.hint{font-size:13px;color:var(--muted);margin-top:5px}"
if css_anchor not in s:
    raise SystemExit('CSS anchor not found')
s = s.replace(css_anchor, css_anchor + ".app-version{font-size:11px;color:#9ca3af;margin-top:4px;font-variant-numeric:tabular-nums}", 1)

header_anchor = '<header><div class="wrap"><h1>Preisarchiv</h1><div class="sub">Aktuell gültige Angebote von REWE Weilbach, GLOBUS Hattersheim, EDEKA Buch Hofheim und E center Haller Raunheim</div></div></header>'
if header_anchor not in s:
    raise SystemExit('Header anchor not found')
header_new = '<header><div class="wrap"><h1>Preisarchiv</h1><div class="sub">Aktuell gültige Angebote von REWE Weilbach, GLOBUS Hattersheim, EDEKA Buch Hofheim und E center Haller Raunheim</div><!--APP_VERSION_START--><div class="app-version">Version: __CHANGE_COMMIT__ · __CHANGE_TIME__</div><!--APP_VERSION_END--></div></header>'
s = s.replace(header_anchor, header_new, 1)

p.write_text(s, encoding='utf-8')
print('version badge placeholder added')
