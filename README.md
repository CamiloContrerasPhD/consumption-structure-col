# La Polarizacion Politica del Consumo - Colombia

Replica metodologica, adaptada a Colombia, del proyecto
[The Political Polarization of Consumption](https://liaukonyte.dyson.cornell.edu/polarization)
de Jura Liaukonyte (Cornell). En lugar de datos propietarios (Luminate / SafeGraph / Numerator)
y del voto presidencial de EE.UU. 2020, esta version usa fuentes abiertas y reproducibles.

## Idea
Cada cadena (tiendas, bancos, gasolineras, farmacias, comida, telecom) se ubica en un eje
izquierda-derecha segun la inclinacion politica de los municipios donde concentra sus locales
(su "huella territorial"), no segun la ideologia de sus clientes ni de la marca.

- Eje X: margen promedio **De La Espriella - Cepeda** (primera vuelta presidencial 2026), en puntos,
  ponderado por numero de locales de la marca.
- Eje Y: numero de locales (escala log) como proxy de tamano.

## Fuentes
- **Voto:** Registraduria Nacional, resultados primera vuelta 2026 (`resultados.registraduria.gov.co`),
  boletin de preconteo 67 (~100% mesas). JSON estatico `/json/ACT/PR/<DIVIPOLA>.json`, 1.189 municipios.
  Polos: Abelardo De La Espriella (Defensores de la Patria) vs Ivan Cepeda (Pacto Historico).
- **Tiendas:** OpenStreetMap via Overpass API. v2 (`02b_brands_v2.py`): ademas del tag `brand`, se barre
  por TIPO de tienda (supermarket/wholesale, pharmacy/chemist, clothes/shoes, fast_food/restaurant) para
  capturar cadenas REGIONALES sin tag `brand`. Fuentes: data/raw/{stores_raw, shops_super, shops_pharma,
  shops_ropa, shops_food}.json. Resultado: **8.121 locales, ~134 marcas, 5 dominios** (Tiendas, Comida,
  Servicios, Moda, Vehiculos), con normalizacion de variantes (D1/Ara/Surtimax/La Rebaja...).
  `02b` reemplaza a `02` para los sitios.
- **Internet:** MinTIC "Internet Fijo Accesos" 2023-T3 (datos.gov.co, dataset `n48w-gutb`), accesos por
  municipio (codigo DANE). Usado en el analisis centro-periferia.
- **Educacion:** MEN "Estadisticas en Educacion" 2024 (datos.gov.co, dataset `nudc-7mev`), cobertura neta
  en educacion media por municipio (codigo DANE), cap a 100. Pilar educativo del indice compuesto.
- **Poblacion:** DANE, proyecciones municipales CNPV 2018 (`PPED-AreaMun-2018-2042`), ano 2025: total y cabecera
  por municipio (1.122 munis, 53,06M hab) -> `data/processed/poblacion_municipio.csv`. Usada en el Sitio 2
  (acceso/desiertos de consumo: locales por 10.000 hab).
- **Busqueda online:** Google Trends, interes por subregion (departamento), ventana 12 meses. Sustituto del
  pilar de musica del original (los charts de Spotify por ciudad estan descontinuados). Extraido via la API
  interna de Trends desde el navegador (pytrends devuelve 429), en lotes comparados anclados en "Karol G".
- **Fronteras municipales:** OpenStreetMap admin_level=6 (1.129 poligonos, con codigo DIVIPOLA).

## Pipeline (scripts/)
1. `01_build_muni_polygons.py` - reconstruye poligonos municipales desde el volcado Overpass
   (`data/raw/muni_boundaries.json`) -> `data/processed/muni_polygons.pkl`.
2. `02_join_and_index.py` - asigna cada local a su municipio (point-in-polygon, shapely STRtree),
   une con el voto, calcula el indice por marca -> `data/processed/*.csv`, `site/data.json`, `site/data.js`.
3. `03_regions.py` - agrega el voto por region / departamento / ciudad (ponderado por votos validos),
   clasifica bastiones extremos y territorios 50/50, cruza con marcas (swing vs base) y exporta el
   choropleth municipal simplificado -> `site/geo.js` (`window.GEO_MUNI`, `window.GEO_AGG`).
4. `04_centro_periferia.py` - construye un INDICE compuesto de acceso por municipio = promedio de z-scores de
   (comercio/1k, internet/1k, cobertura educacion media). Calcula correlaciones con el voto (Spearman) y el
   scorecard regional -> `site/cp.js`. Hallazgo: voto-comercio +0.33, voto-internet +0.36, voto-educacion
   +0.20, voto-INDICE +0.35 (eje centro-periferia moderado; Andina = centro, Amazonia = periferia).
5. `05_online.py` - pilar "Que se busca online": ubica cada termino (artista/plataforma/IA) por su lean de
   audiencia (voto departamental ponderado por interes de busqueda x tamano electoral) y lo dimensiona por
   interes total -> `site/online.js`. 31 terminos en 10 categorias. Champeta y Afro/currulao del Pacifico
   (Kevin Florez, Herencia de Timbiqui, ChocQuibTown, Joe Arroyo) caen a la izquierda; popular andina a la
   derecha; plataformas e IA al centro (geografia neutra). Corroboracion: artistas de generos del Pacifico/
   Caribe aparecen en los bastiones de Cepeda; izquierda ideologica con publico nacional (Aterciopelados)
   cae al centro -> el eje mide geografia de audiencia, no ideologia. Datos en `data/raw/trends_online.json`.

El voto por municipio (`data/raw/voto_2026_municipio.csv`) se descargo del portal de la Registraduria
desde el navegador (CloudFront bloquea curl): ver nota en `scripts/NOTES.md`.

## Sitio (site/)
Replica multipagina del estudio original:
- `index.html` - hub con 4 tarjetas (histogramas) por dominio + caveat + recursos + enlace a metodologia.
- `metodologia.html` - declara que el sitio sigue la metodologia de Liaukonyte, Tuchman & Zhu (2023)
  (igual que el original), documenta el indice y respalda las variables agregadas (busqueda online, internet,
  educacion) con literatura: Choi & Varian (2012), Stephens-Davidowitz (2014), Mellon (2014),
  DellaPosta/Shi/Macy (2015), Lipset & Rokkan (1967), Norris (2001), Guler & Singh (2026).
- `analisis.html?d=<tiendas|comida|servicios>` - scatter interactivo del dominio (busqueda, chips de
  subcategoria, escala log, pantalla completa, tooltip).
- `regiones.html` - mapa coropletico municipal + rankings de bastiones (extremos) y territorios 50/50
  por region / departamento / ciudad, y que marcas viven en zonas swing vs zonas de base.
- `mapa-consumo.html` - los analisis de marcas llevados al territorio: cada local como punto sobre el
  mapa politico, con filtro por dominio (Tiendas / Comida / Servicios) y densidad de consumo por region.
- `online.html` - 4to pilar de consumo "Que se busca online": scatter de artistas, plataformas e IA por
  lean de audiencia (Google Trends) x interes de busqueda (log), con chips por categoria.
- `centro-periferia.html` - investiga el eje centro-periferia: mapa bivariado (voto x indice de acceso, 3x3)
  + scatter municipio (internet x comercio, color = voto, tamano = votos) + correlaciones + scorecard
  regional (comercio/internet/educacion + indice) + nota honesta sobre acceso a IA.
- `app.js` (render compartido) + `styles.css` + `data.js` + `geo.js` (cargan en file:// sin CORS).

Tres dominios de consumo (todos desde la huella de OSM, organizados como en el original):
1. **Tiendas y Compras** - supermercados, descuento, farmacias, hogar y tecnologia.
2. **Comida y Bebida** - cafe, comida rapida, restaurante (analogo al pilar CPG).
3. **Servicios Cotidianos** - bancos, gasolineras, telecomunicaciones.

D3 v7 por CDN (requiere internet). Servir con `python -m http.server` dentro de `site/`.

### Brechas frente al original
- **Musica en streaming** (Spotify por ciudad): los charts por ciudad se descontinuaron en 2023. **Resuelto**
  con un sustituto: pilar "Que se busca online" via Google Trends (interes de busqueda por departamento).
- **Paneles de compra de hogares** (tipo Numerator) para marcas CPG: no existen abiertos en Colombia
  (el pilar CPG se aproxima con la huella de marcas de consumo via OSM).

## Requisitos
`pip install shapely` (Python 3.x). El resto es stdlib.

## Limitaciones
- Resultados electorales **provisionales** (preconteo, no vinculantes).
- Resolucion **municipal**: Bogota es un solo municipio con ~38% de los locales, asi que no se observa
  la variacion intraurbana (norte vs sur). El original tiene el mismo limite con condados grandes.
  Mejora posible: bajar a nivel PUESTO de votacion para las ciudades grandes.
- Cobertura de OpenStreetMap incompleta y desigual entre marcas.
- El indice es descriptivo/correlacional, no causal.
