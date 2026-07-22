# Sitio 2 - Plan de desarrollo

Segundo sitio interactivo que REUSA el sistema de diseno del primero
(Swiss minimal: Inter + IBM Plex Mono, hairlines, scatters, coropletas,
bivariado 3x3, listas de bastiones, numeros mono, escala politica azul/rojo).
Cambia la PREGUNTA, no la estetica.

- Sitio 1 (actual): que consumo esta ligado a que candidato -> sorteo / polarizacion (descriptivo).
- Sitio 2 (este plan): como esta estructurado y distribuido el consumo en el territorio,
  que predice y donde estan los vacios -> estructura, acceso y oportunidad.
  La politica pasa a ser una CAPA TRANSVERSAL, no el eje.

Unidad principal: cambia de "marca" a "municipio" (y secundariamente "marca"),
que es lo que habilitan los metodos nuevos.

Activo base ya disponible (del Sitio 1):
- data/processed/muni_index.csv     (divipola, muni, dept, lean, votval) ~1.087 municipios
- data/processed/stores_geo.csv     (brand, domain, subcat, lon, lat, divipola, muni, lean) 5.334 locales
- data/processed/muni_polygons.pkl  (geometrias municipales)
- data/raw/internet_municipio_2023q3.json, educacion_municipio_2024.json, voto_2026_municipio.csv
- site/{geo.js, cp.js, online.js, data.js, app.js, styles.css}  (componentes reusables)
- data/raw/trends_online.json (interes de busqueda por departamento)

---

## 1. Indicadores (que miden y como)

| Indicador | Que mide | Metodo | Datos | Nivel* |
|---|---|---|---|---|
| ICC - Complejidad del consumo | Diversidad/sofisticacion de la canasta de marcas del municipio | Metodo de reflexiones / ECI sobre matriz municipio x marca | OSM (ya) | 1 |
| Ubicuidad / PCI de marca | Que tan comun vs exclusiva/sofisticada es cada marca | PCI (espejo del ECI) | OSM (ya) | 1 |
| Densidad de relatedness / oportunidad | Que marcas "deberian" estar en un municipio pero faltan = vacio de mercado | Proximidad + densidad sobre la matriz | OSM (ya) | 1 |
| Diversidad/entropia de canasta | Mezcla de dominios/subcategorias por municipio | Entropia de Shannon | OSM (ya) | 1 |
| Clusters LISA + anomalias | Hotspots/coldspots de consumo; co-clusters voto x consumo (vota X, consume como Y) | Moran global/local/bivariado | Poligonos + voto (ya) | 2 |
| Comunidades de marcas | "Vecindarios" de marcas que co-ocurren y su color politico | Red de co-localizacion + Louvain/Leiden | OSM (ya) | 2 |
| Indice con incertidumbre | El lean/ICC suavizado con intervalos de credibilidad | BYM/CAR bayesiano | Ya | 2 |
| Accesibilidad de consumo (2SFCA) | Acceso real ponderado por oferta, demanda y friccion (formaliza "desierto") | 2SFCA gravitacional | + WorldPop + tiempos OSRM | 3 |
| Actividad economica (luces) | Riqueza/actividad local para separar centro-periferia de puro ingreso | Zonal stats VIIRS | + Black Marble/EOG | 3 |
| GWR/MGWR consumo<->voto | Coeficiente que varia por municipio y escala | (M)GWR | Ya | 2 |
| Efectos espaciales (SAR/SEM) | Spillovers + correccion de dependencia espacial | Spatial lag/error/Durbin | Ya (panel: +elecciones 2018/2022) | 2 / 3 |
| Inferencia ecologica | Asociacion individual voto<->consumo desde agregados (cotas) | King EI / EI bayesiana / EI monotona | Ya | 2 / 4 |

*Nivel de esfuerzo/insumo (ver seccion 3).

---

## 2. Paginas (reusando los componentes del Sitio 1)

1. Hub
   - Mismo hero + stat pills nuevas (n municipios, ICC promedio, % municipios "desabastecidos", n marcas en la red).
   - Tarjetas con histograma a cada analisis (como index.html actual).

2. Complejidad del consumo  (scatter, como analisis.html)
   - Punto = MUNICIPIO. X = ICC; Y = poblacion/tamano (log); color = lean politico.
   - Pregunta: la canasta mas compleja es la del centro/derecha?
   - Chips por region. Nivel 1.

3. El espacio de marcas  (scatter de marcas, ejes nuevos)
   - Punto = MARCA. X = ubicuidad (comun<->rara); Y = PCI (sofisticacion); color = politico.
   - Espejo estructural del scatter actual. Nivel 1.

4. Mapa de complejidad  (coropleta + listas, como regiones.html)
   - ICC por municipio; rankings de mas/menos complejos; cruce con voto. Nivel 1-2.

5. Oportunidad de mercado  (mapa interactivo + ranking - PAGINA NUEVA)
   - Eliges una marca -> coropleta de densidad de relatedness (donde "deberia" entrar).
   - Por municipio -> que marcas faltan. Pieza PREDICTIVA que el Sitio 1 no tiene. Nivel 1.

6. Clusters y anomalias  (coropleta LISA, como el mapa)
   - Hotspots/coldspots; lista de ANOMALIAS voto x consumo (consumo no "cuadra" con la politica local). Nivel 2.

7. Red de marcas  (grafo force-directed - visualizacion NUEVA pero coherente)
   - Comunidades coloreadas por su lean; hover = marca y su barrio. Nivel 2.

8. Acceso y desiertos  (coropleta + bivariado 3x3, como centro-periferia.html)
   - 2SFCA; bivariado acceso x voto; lista de "desiertos" (bajo acceso, alta poblacion).
   - Upgrade formal del centro-periferia. Nivel 3.

9. Incertidumbre  (coropleta con toggle)
   - Indice suavizado BYM con intervalos; toggle "estimacion / incertidumbre".
   - Honestidad estadistica que el Sitio 1 no muestra. Nivel 2.

10. Metodologia y referencias
    - Misma estructura; documenta complejidad economica, relatedness, 2SFCA, LISA, BYM, redes + bibliografia (seccion 7).

---

## 3. Niveles de esfuerzo / insumo (caracterizacion)

1) YA (datos que ya tengo + librerias instaladas - minutos)
   - C1 Complejidad del consumo (ICC/PCI/relatedness) - solo numpy.
   - Diversidad/entropia de canasta.
   - Recalcular correlaciones voto x {comercio, internet, educacion} con significancia.

2) RAPIDO, pero necesito algo (mismos datos + un pip install o una decision de modelado - horas)
   - A1 LISA + Moran global/local/bivariado (libpysal/esda).
   - A2 GWR/MGWR (mgwr).
   - A3 Regresion espacial SAR/SEM corte transversal (spreg).
   - C2 Red de marcas + comunidades (networkx + louvain).
   - D1-lite Suavizado bayesiano BYM/CAR (PyMC) - lo mas pesado de este nivel.
   - D2 Inferencia ecologica, intento simple (cotas).
   - B1-aprox 2SFCA borrador (votantes=demanda, distancia recta).

3) RAPIDO, pero necesito descargar y trabajar datos (bajar con Chrome; luego rapido)
   - B1 completo 2SFCA: WorldPop/GHSL (poblacion) + OSM red vial / OSRM (tiempos).
   - A3 panel espacial: resultados electorales 2018 y 2022 (Registraduria).
   - E1 luces nocturnas: VIIRS (NASA Black Marble / EOG) + zonal stats.
   - Enriquecer huella: mas categorias OSM / popular times de Google Places.

4) DEMORADO y necesito datos (descarga + modelado/orquestacion pesada - dias)
   - D1 MRP completo: encuesta (LAPOP/Latinobarometro) + marco censal de postestratificacion + multinivel bayesiano + validacion del indice.
   - D3 causal: RDD espacial en fronteras o DiD por aperturas/cierres de tiendas (armar fechas, identificacion, robustez).
   - EI bayesiana completa con validacion.
   - 2SFCA multimodal a escala fina con ruteo masivo.
   - Validacion con encuesta propia (trabajo de campo).

---

## 4. Catalogo de datos

Locales (ya en el repo): muni_index.csv, stores_geo.csv, muni_polygons.pkl, internet/educacion/voto, trends.

A descargar (con Chrome / scripts):
- Poblacion: WorldPop (worldpop.org), GHSL (Global Human Settlement Layer, JRC).
- Red vial / ruteo: OSM (Overpass) + OSRM o OpenRouteService (matrices de tiempo).
- Luces nocturnas: NASA Black Marble (VNP46), EOG VIIRS (eogdata.mines.edu).
- Elecciones historicas: Registraduria 2018, 2022 (mismo metodo de scraping del Sitio 1; ver scripts/NOTES.md).
- Encuestas individuales: LAPOP AmericasBarometer, Latinobarometro, World Values Survey (para MRP/validacion).
- Socioeconomico: DANE (censo CNPV 2018, GEIH, pobreza IPM), MGN shapefiles.
- Aperturas de tiendas: prensa / sitios corporativos (D1, Ara, Exito) para disenos causales.

---

## 5. Reuso del sistema de diseno

Se reutiliza tal cual:
- styles.css (Swiss), app.js (drawScatter, drawMap/choropleth, drawHistogram, bivariado, tooltips),
  escala politica azul/rojo (como CAPA TRANSVERSAL), listas de bastiones, numeros mono tabulares.

Se agrega:
- Un visual nuevo: grafo force-directed (red de marcas) - usar d3-force, manteniendo hairlines/mono.
- Una pagina interactiva nueva: Oportunidad (selector de marca -> coropleta de probabilidad).

Diferenciacion visual entre sitios:
- Cambiar SOLO el acento (p. ej. de naranja #ec4413 a un verde/teal) manteniendo el mismo sistema.

---

## 6. Roadmap / orden de construccion

MVP (todo nivel 1, solo datos actuales, maxima originalidad):  [HECHO - 2026-06-25]
  Construido y verificado en site2/: index.html (hub) + complejidad.html + marcas.html + oportunidad.html.
  Pipeline: scripts/06_complejidad.py -> site2/complex.js. Reusa styles.css/app.js/geo.js (acento teal).
  Servir: cd site2 && python -m http.server.
  Hub + p2 Complejidad del consumo + p3 Espacio de marcas + p5 Oportunidad de mercado.
  ACTUALIZACION: universo de marcas ampliado (02b_brands_v2.py) -> matriz 521 municipios x 145 marcas.
  oportunidad.html incluye panel "Vinculo con las elecciones": inclinacion del espacio de oportunidad
  (ponderada por densidad x votos) vs huella actual de la marca + distribucion Cepeda/50-50/De La Espriella.
  Pipeline nuevo: scripts/06_complejidad.py
    - construir matriz municipio x marca (presencia/RCA) desde stores_geo.csv
    - calcular RCA, diversidad, ubicuidad, ECI/PCI (metodo de reflexiones / eigenvector)
    - proximidad entre marcas + densidad de relatedness por (municipio, marca)
    - exportar site2/complex.js (window.CX = {munis:[...], brands:[...], opportunity:[...]})

FRICCION POLITICA DE LA EXPANSION [HECHO - 2026-07-21]:
  scripts/11_friccion.py -> site2/friccion.js; seccion nueva en oportunidad.html (bilingue).
  Test: LPM presencia ~ densidad + |lean_muni - lean_marca| + dist geografica + log votval,
  75.545 pares; IC bootstrap 200 reps por municipio. HALLAZGO: -0.22 pp de presencia por +10 pts
  de distancia politica [IC -0.34, -0.12]; curva monotona +0.8 -> -0.45 pp. Mayor friccion:
  Ara, D1, Davivienda; "ciegas": Banco Agrario, La Rebaja, Exito. Correlacional (sin fechas
  de apertura OSM). Anclas: McConnell et al. 2017 AJPS; Panagopoulos et al. 2020 JoP.
INTEGRACION DEL MERCADO (A+B) [HECHO - 2026-07-21]:
  scripts/12_integracion.py -> site2/integracion.js; pagina nueva site2/integracion.html (bilingue)
  + entrada en nav + 5a tarjeta del hub. Indice de segregacion razon de varianza (eta2,
  Massey & Denton 1988): S_electorado=0.082 (municipios, votos) vs S_consumo=0.003 (cadenas,
  locales) -> RATIO 4%: el consumo esta un 4% tan segregado como el electorado (replica
  territorial de Davis et al. 2019 JPE). Marcas puente: Kokoriko, D1, Bancolombia, Dollarcity;
  burbuja (n>=15): Mercaldas, Mercacentro, Megatiendas, Comfandi (caveat: burbuja ~ regionalidad).
  32 municipios de encuentro (|lean|<5pts con comercio; top: Bogota, Barranquilla, Tulua).
  Mapa: encuentro en teal x densidad, resto tinte por campo.
RIESGO DE TOMAR PARTIDO (C) [HECHO - 2026-07-21]:
  scripts/13_riesgo.py -> site2/riesgo.js; pagina nueva site2/riesgo.html (bilingue) + nav (v3)
  + 6a tarjeta del hub. Simulador por marca (114 marcas >=10 locales): composicion politica de la
  huella (Cepeda/50-50/DLE), exposicion extrema (|lean|>30 pts), share del dominio (por locales),
  toggle de postura. Veredicto: exposicion hostil + escenario ilustrativo Hou-Poliquin (-5% visitas
  en red extrema opuesta, disipa ~10 sem) + logica Hydock (share alto = mas por perder). Scatter
  interactivo lean x share con seleccion por clic. Caveats declarados: efectos US, share por
  locales (no ventas), huella != clientes. Anclas: Hydock et al. 2020 JMR; Hou & Poliquin 2022
  SMJ; Neureiter & Bhattacharya 2021; Panagopoulos et al. 2020 JoP.
  AGENDA DE POLARIZACION COMPLETA: D (friccion) + A/B (integracion) + C (riesgo). Queda E
  (Trends temporal, requiere re-descarga) como opcional.

METODOLOGIA (p10 del plan) [HECHO - 2026-07-21]:
  site2/metodologia.html (bilingue) + nav (v4). Secciones: idea (complejidad economica +
  Liaukonyte, independiente de site 1), tabla de datos/fuentes, metodos pagina por pagina
  (ECI, PCI, relatedness, friccion, acceso, integracion, riesgo), limitaciones (ecologico,
  cobertura OSM, proxies, correlacional, preconteo) y bibliografia en 3 grupos: metodos
  estructurales (Balassa, Hidalgo-Hausmann, Hidalgo et al 2007, Massey-Denton, Luo-Wang),
  polarizacion y consumo (Liaukonyte, McConnell, Panagopoulos, Hydock, Hou-Poliquin,
  Neureiter, Schoenmueller, Weber, DellaPosta, Jost) y segregacion (Davis, Brown-Enos,
  Nilforoshan, Athey, Tonin). SITE 2 COMPLETO: 8 paginas.

Fase 2 (nivel 2):
  p6 CLUSTERS Y ANOMALIAS [HECHO - 2026-07-21]: scripts/14_clusters.py -> site2/clusters.js +
    clusters.html (bilingue, nav v5+). LISA de Anselin (1995) implementado en numpy (sin libpysal,
    incompatible con Py3.14): pesos kNN(6) fila-estandarizados, permutacion condicional (199).
    Univariado ECI + bivariado voto->lag(ECI). HALLAZGOS: Moran voto=0.68, ECI=0.20,
    bivariado=-0.16 (voto DLE convive con entornos de consumo simples). 61 anomalias: cinturon
    Caribe (Soledad, Malambo, Galapa, Bogota) vota Cepeda en entorno complejo; Antioquia/Boyaca
    rural vota DLE en entorno simple. Mapa con toggle bivariado/ECI + listas de anomalias.
  p7 RED DE MARCAS [HECHO - 2026-07-21]: scripts/15_red.py (networkx 3.6.1) -> site2/red.js +
    red.html (bilingue, nav v6). Grafo phi min-condicional, poda phi>=0.35 + top-3 por nodo
    (145 nodos, 716 aristas); comunidades por modularidad voraz (CNM): 6 barrios, leans -0..+7
    (motos +7 el mas a la derecha; los barrios NO estan fuertemente sorteados). Force-directed
    d3 con drag, toggle color comunidad/voto, busqueda, panel de barrios.
  p9 INCERTIDUMBRE (BYM COMPLETO) [HECHO - 2026-07-21]: PyMC 6.1.0 (Py3.14, backend Python
    sin g++). scripts/16_bym.py: y_m ~ Binomial(n_m, p_m); logit(p) = b0 + s_t*theta +
    s_s*ICAR_centrado(W); W = kNN(6) simetrizado + componente unica (union-find); 1.061
    municipios (>=50 votos, con centroide); NUTS 4 cadenas x 800 draws (tune 1200, ta 0.93).
    Iteraciones de convergencia: (1) 2x600 rhat(b0,s)=1.21; (2) 4 cadenas rhat=2.06 por
    no-identificabilidad del ICAR (impropio) con b0; (3) FIX: centrar phi -> rhat sobre p
    = 1.29 max, concentrado en municipios diminutos; p estable entre corridas (<0.005).
    HALLAZGOS: ancho mediano IC95 = 2.3 pts; mayores shrinkages e IC mas anchos en la
    Amazonia/Orinoquia rala (La Guadalupe 63 votos: 49.2->44.7%; Miriti-Parana, Yavarate,
    San Felipe). Pagina site2/incertidumbre.html (bilingue, nav v7): 3 vistas (suavizado /
    ancho IC95 / correccion vs crudo), stats de convergencia declarados, listas.
    FASE 2 COMPLETA (p6 LISA + p7 Red + p9 BYM; p4 cubierto por clusters).
    PROPAGACION A MARCAS/CATEGORIAS [2026-07-21]: 16_bym.py propaga los draws posteriores a la
    huella de cada marca (lean con IC creible 95%, n>=10 locales) y a las 5 categorias.
    HALLAZGO: 113/114 marcas con color politico afirmable (IC no cruza 0); fragiles = cadenas
    regionales chicas (Brio, Zeuss, Mercaldas, ~0.8 pts de ancho). Seccion nueva en
    incertidumbre.html: grafico de intervalos (28 cadenas mayores) + categorias con IC.
    Declarado: el rango refleja incertidumbre electoral, no de cobertura OSM. Cabecera de la
    pagina reescrita en clave intuitiva (que hace / que busca / para que sirve).
  p4 Mapa de complejidad: parcialmente cubierto por clusters.html (vista ECI); coropleta simple
    de ECI queda opcional.

Fase 3 (nivel 3, requiere descargas):
  p8 Acceso y desiertos [HECHO - 2026-06-26]: descargada poblacion municipal DANE (CNPV 2018, proy. 2025;
    data/raw/poblacion_municipal_dane.xlsx -> data/processed/poblacion_municipio.csv, 1.122 munis, 53.06M hab).
    scripts/10_acceso.py -> site2/acceso.js; pagina site2/acceso.html (coropleta acceso + bivariado acceso x voto +
    ranking de desiertos + cobertura). Acceso = locales/10k hab (1-paso, no 2SFCA completo: falta OSRM).
    Hallazgo: OSM cubre 522/1.085 munis = 84% de la poblacion (brecha rural); acceso~voto Spearman +0.12,
    acceso~urbanizacion +0.26; mayores desiertos = Valledupar, Bello, Soledad, Soacha, Tumaco.
  Pendiente fase 3: 2SFCA real con tiempos OSRM, luces nocturnas (VIIRS), panel espacial 2018/2022.

Fase 4 (nivel 4):
  MRP + validacion individual, disenos causales, EI completa.

Estructura de carpetas sugerida:
  site2/  (index.html, complejidad.html, marcas.html, oportunidad.html, clusters.html, red.html, acceso.html, incertidumbre.html, metodologia.html, app2.js, styles.css [reuso], complex.js, geo.js [reuso])
  scripts/ 06_complejidad.py, 07_espacial.py, 08_red.py, 09_bym.py, 10_acceso.py

---

## 7. Referencias (bibliografia de trabajo - VERIFICAR DOIs antes de publicar)

NB: titulos/autores provienen de buscadores academicos (Consensus/alphaXiv). Verificar con Scholar Sidekick / DOI.

### 7.1 Tema (polarizacion/politizacion del consumo + adyacentes)
- Liaukonyte, Tuchman & Zhu (2022/2023). Spilling the Beans on Political Consumerism. Marketing Science. [base del Sitio 1]
- Schoenmueller, Netzer & Stahl (2022). Polarized America: From Political to Preference Polarization. Marketing Science.
- Rogers (2022). Politicultural Sorting. American Politics Research.
- Weber et al. (2021). Political Polarization: ... Consumer Welfare, Marketers, Public Policy. J. Public Policy & Marketing.
- Ruch et al. (2022). Millions of Co-purchases ... Lifestyle Politics across Online Markets. (arXiv/working).
- Tornberg (2022). How digital media drive affective polarization through partisan sorting. PNAS.
- DellaPosta, Shi & Macy (2015). Why Do Liberals Drink Lattes? American Journal of Sociology. [canonico]
- Panagopoulos et al. (2020). Partisan Consumerism. The Journal of Politics.
- Hydock, Paharia & Blair (2020). Should Your Brand Pick a Side? (CPA x market share). J. Marketing Research.
- Endres & Panagopoulos (2017). Boycotts, buycotts, and political consumerism. Research & Politics.
- Copeland & Boulianne (2020). Political consumerism: a meta-analysis. Int. Political Science Review.
- Hou & Poliquin (2026). Values and visibility: CEO activism ... Strategic Management Journal.
- Garg & Saluja (2022). A Tale of Two Ideologies (brand activism). J. Assoc. for Consumer Research.
- Neureiter & Bhattacharya (2021). Why Do Boycotts Sometimes Increase Sales? Business Horizons.
- Narayanan et al. (2024). Consumer activism: SLR (S-O-R-Om). J. Consumer Behaviour.
- Bhagwat et al. (2020). Corporate Sociopolitical Activism and Firm Value. J. Marketing.
- Vredenburg et al. (2020). Brands Taking a Stand: Authentic ... or Woke Washing? J. Public Policy & Marketing.
- Melloni et al. (2023). Cashing in on the culture wars? CEO activism, wokewashing, firm value. SMJ.
- Mirzaei et al. (2022). Woke brand activism authenticity. J. Business Research.
- Luna-Amador et al. (2025). Brand activism: research trends and cluster analysis.

### 7.2 Fundamentos (polarizacion afectiva / ideologia y consumo)
- Iyengar et al. (2019). Origins and Consequences of Affective Polarization in the US. Annual Review of Pol. Science.
- Iyengar et al. (2015). Fear and Loathing across Party Lines. AJPS.
- McConnell et al. (2017). The Economic Consequences of Partisanship in a Polarized Era. AJPS.
- McCartney & Shah (2021). Political Polarization Affects Households' Financial Decisions (home sales).
- Druckman et al. (2020). Affective polarization, local contexts and public opinion. Nature Human Behaviour.
- Jost (2017). The marketplace of ideology: elective affinities. J. Consumer Psychology.
- Kivikangas et al. (2020). Moral foundations and political orientation: meta-analysis. Psychological Bulletin.
- Ordabayeva & Fernandes (2018). How Political Ideology Shapes Preferences for Differentiation. JCR.
- Ordabayeva et al. (2023). How Political Ideology Shapes Consumption Decisions (review). SSRN.
- Adaval & Wyer (2022). Political Ideology and Consumption (special issue). J. Assoc. Consumer Research.
- Fernandes (2020). Politics at the Mall: The Moral Foundations of Boycotts. JPPM.
- Ketron et al. (2022). The "company politics" of social stances. J. Business Research.
- Keller et al. (2026). Value congruence ... conservatives' preference for cute products. JAMS.
- Tiganis et al. (2025). Political ideology and consumer preferences for CSR. J. Retailing & Consumer Services.

### 7.3 Metodos (geoespacial, acceso, complejidad, bayesiano, redes)
- Bivand & Wong (2018). Comparing implementations of global and local indicators of spatial association. TEST.
- Ruttenauer (2024). Spatial data analysis / spatial econometrics (handbook chapter).
- Kang et al. (2025). Scale and correlation in MGWR. J. Geographical Systems.
- Wang et al. (2021). Local Statistics for Spatial Panel Models ... US Electorate.
- Ma et al. (2020). Geographically Weighted Regression: A Bayesian Recourse. Int. Regional Science Review.
- Chen (2019). A comparative analysis of accessibility measures by 2SFCA. IJGIS.
- Stacherl et al. (2023). Gravity models for spatial healthcare access: systematic review. Int. J. Health Geographics.
- Bryant & Delamater (2019). E2SFCA at micro/macro levels (MAUP). Annals of GIS.
- Lin et al. (2021). A narrative analysis of the 2SFCA and i2SFCA methods (market potential). IJGIS.
- Hidalgo et al. (2022, arXiv:2205.02942). Evaluating the principle of relatedness.
- (arXiv:2601.19814). Abundance and Economic diversity as descriptor of cities' economic complexity.
- (arXiv:2407.19762). Redefining Urban Centrality: Economic Complexity + Central Place Theory.
- (arXiv:2503.05915). Evaluating MRP with Spatial Priors with a Big Data Behavioural Survey.
- (arXiv:2306.11302). A Two-Stage Bayesian Small Area Estimation Approach for Proportions.
- (arXiv:2504.14752). Monotone Ecological Inference.
- (arXiv:2601.07668). The Role of Confounders and Linearity in Ecological Inference: A Reassessment.

Canonicas de metodo (verificar): Hidalgo & Hausmann (2009, PNAS, product space);
King (1997, A Solution to the Ecological Inference Problem); Anselin (1995, LISA, Geographical Analysis);
Fotheringham, Brunsdon & Charlton (2002, GWR); Henderson, Storeygard & Weil (2012, AER, nightlights);
Jean et al. (2016, Science, satellite+ML poverty); Chen & Nordhaus (2011, PNAS, luces);
Christaller (Central Place Theory); Paul & Rosado-Serrano (2019, Int. Marketing Review, marco TCCM).

---

## 8. Notas / pendientes

- Calibracion epistemica: el sitio es ecologico (nivel lugar). Declarar falacia ecologica y MAUP;
  por eso D1 (incertidumbre) y D2 (EI) son importantes para credibilidad.
- Validar la matriz municipio x marca: cobertura desigual de OSM; documentar sesgo (subregistro rural).
- ICC/PCI: usar marcas (no subcategorias) para mayor resolucion; probar robustez con/ sin marcas raras.
- Oportunidad: la "densidad de relatedness" predice presencia esperada; el residuo (esperado - observado)
  es la oportunidad/anomalia; cruzar el residuo con el voto (anomalia politica).
- Antes de cualquier publicacion: verificar DOIs y estado (retraccion/OA) de toda la bibliografia (sec. 7).
  NOTA: Scholar Sidekick (MCP) requiere suscripcion de RapidAPI - no disponible en esta cuenta (2026-06-25).
  Alternativas: verificar a mano via Chrome (arxiv.org/abs/<id>, doi.org/<doi>, Google Scholar), o
  agregar una RAPIDAPI_KEY para Scholar Sidekick.
