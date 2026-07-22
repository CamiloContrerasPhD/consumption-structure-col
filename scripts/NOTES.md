# Notas de captura de datos

## Voto 2026 por municipio
El portal `resultados.registraduria.gov.co` es una SPA que sirve JSON estaticos.
CloudFront bloquea `curl` (403 WAF), pero un fetch same-origin desde el navegador funciona.

- Config: `/json/web/config.json`
- Geografia/partidos: `/json/nomenclator.json` (niveles 1=COLOMBIA,2=DEPTO,3=MUNICIPIO; codigos `co` = DIVIPOLA)
- Resultados: `/json/ACT/PR/<co>.json` (00 = nacional; por municipio con su DIVIPOLA)

Estructura del resultado: `camaras[0].partotabla[].act` -> `{codpar, vot, pvot, cantotabla[]}`.
Candidatos por `codcan`: 4 = Abelardo De La Espriella, 1 = Ivan Cepeda, 11 = Paloma Valencia.
Totales del ambito: `totales.act.votval` (votos validos), `votant` (votantes).

Se recorrieron los 1.189 municipios con un fetch concurrente en consola del navegador y se
exporto `voto_2026_municipio.csv`. Para re-ejecutar, abrir el portal, entrar a "Presidente y
Vicepresidente" y correr el script de fetch (ver historial) en la consola.

## Tiendas (OpenStreetMap / Overpass)
Overpass SI responde a curl. Query usada (data/raw/stores_raw.json):

    [out:json][timeout:150];
    area["ISO3166-1"="CO"]->.co;
    ( nwr["brand"]["shop"](area.co);
      nwr["brand"]["amenity"~"fast_food|cafe|restaurant|fuel|pharmacy|bank|marketplace"](area.co); );
    out center tags;

## Fronteras municipales (Overpass)
    [out:json][timeout:260];
    area["ISO3166-1"="CO"]->.co;
    relation["boundary"="administrative"]["admin_level"="6"](area.co);
    out body;>;out skel qt;
