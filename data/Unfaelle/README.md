Datengrundlage sind offene Geodaten des **Unfallatlas** der Statistischen Ämter des Bundes und der Länder.

Der Datensatz enthält georeferenzierte Verkehrsunfälle mit Personenschaden. Die Daten wurden jahresweise als CSV-Dateien bezogen, automatisiert eingelesen und für das Gemeindegebiet **Magdeburg** gefiltert.

| Merkmal | Angabe |
|---|---|
| Datenquelle | Unfallatlas der Statistischen Ämter des Bundes und der Länder |
| Datenportal | [OpenGeodata.NRW – Verkehrsunfälle mit Personenschaden in Deutschland](https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/) |
| Inhalt | Verkehrsunfälle mit Personenschaden |
| Raumbezug | Gemeinde Magdeburg, AGS `15003000` |
| Zeitraum | `[Jahre einsetzen, z. B. 2017–2024]` |
| Zugriff | Automatisierter Download der bereitgestellten CSV-ZIP-Dateien |
| Dateimuster | `Unfallorte{jahr}_EPSG25832_CSV.zip` |
| Koordinaten | WGS84-Koordinaten aus den Feldern `XGCSWGS84` und `YGCSWGS84` |
| Verarbeitung | Umwandlung in Punktgeometrien und Filterung auf Magdeburg |
| Lizenz | Datenlizenz Deutschland – Namensnennung – Version 2.0 |
| Namensnennung | © Statistische Ämter des Bundes und der Länder |
| Weitere Informationen | [Datensatzbeschreibung Unfallatlas](https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/DSB_Unfallatlas.pdf), [interaktive Kartenanwendung](https://unfallatlas.statistikportal.de/) |