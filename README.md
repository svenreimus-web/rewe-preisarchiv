# REWE Preisarchiv

Preisarchiv für **REWE Vigheshan Gahndi oHG**, Industriestraße 40, 65439 Flörsheim-Weilbach (Markt 240367).

## Funktionen

- Angebote speichern und durchsuchen
- Preisverlauf je Produkt dauerhaft archivieren
- Diagramm-Symbol bei Produkten mit mehreren unterschiedlichen Preisen
- Preisdiagramm mit historischen Preisständen
- Produktbilder/Thumbnails, sofern die Quelle ein Bild liefert
- Mobile Web-App für iPhone und iPad
- SQLite-Datenbank auf persistentem Railway-Volume
- Geschützte Aktualisierung über `ADMIN_TOKEN`

## Railway

Das Repository ist für Deployment per Dockerfile vorbereitet.

1. In Railway ein neues Projekt aus diesem GitHub-Repository erstellen.
2. Ein persistentes Volume mit Mount Path `/app/data` hinzufügen.
3. Unter Variables `ADMIN_TOKEN` mit einem privaten Passwort setzen.
4. Eine öffentliche Domain für den Service erzeugen.
5. `/health` aufrufen; bei erfolgreichem Start wird `status: ok` ausgegeben.

## Hinweis zum Angebotsimport

Die Preisarchiv-, Graph- und Bildlogik ist implementiert. Der automatische Import von der REWE-Angebotsseite ist derzeit ein Best-Effort-Parser mit Playwright-Fallback. Die vollständige Auswertung aller Seiten des eingebetteten Wochenprospekts kann als nächster Schritt erweitert werden, ohne Datenbank oder Oberfläche neu aufzubauen.
