# Cifras y cómo comprobarlas

Cada número que citamos en la web, en las redes y en la prensa está aquí, con la fórmula para repetirlo en una hoja de cálculo, el fichero de `data/` de donde sale, el script que lo construyó y la página del organismo que publicó el dato original. Los valores de esta página los calcula `pipeline/figures.py` desde `data/` (actualizado 2026-10-19); no se escriben a mano.

**Comprobar una cifra en dos clics:** de la cifra en la web a su fila aquí (1), y de la fila al fichero o a la fuente original (2).

Si encuentras un error, [abre un issue](https://github.com/jaimeoliver1/madrid-en-bici/issues/new?template=dato-incorrecto.yml): corregimos primero y explicamos después.

## Los tres titulares

### <a id="cobertura"></a>Solo el 4,6% de los madrileños vive en un barrio con la densidad de estaciones de BiciMAD que recomienda la guía de la ITDP (8 de 131 barrios).

- **Cómo se calcula:** En data/madrid_barrios_bicimad.csv: suma `population` de los barrios con `stations_per_km2` ≥ 10 y divide entre la suma de `population` de los 131 barrios.
- **Fichero:** [`data/madrid_barrios_bicimad.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/madrid_barrios_bicimad.csv)
- **Script:** pipeline/historical/08_barrios.py (contorno y primera cuenta) y pipeline/refresh.py (recuento mensual)
- **Fuente original:** [BiciMAD · feed en tiempo real (GBFS)](https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json); [Ayuntamiento de Madrid · Padrón a 1 de enero (300557)](https://datos.madrid.es/dataset/300557-0-poblacion-distrito-barrio); [Ayuntamiento de Madrid · Límites administrativos (900012)](https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas); [ITDP · The Bikeshare Planning Guide](https://bikeshare.itdp.org/guide/goal-setting-initial-planning/examine-feasibility-choose-a-system-type/)
- **Ojo:** Estaciones en servicio dentro de cada barrio (las 32 de Pozuelo no cuentan). 10 estaciones/km² es el mínimo de la guía de la ITDP (10–16): es una densidad, no una distancia medida a pie.

### <a id="crecimiento"></a>BiciMAD casi se ha duplicado en dos años: 11,3 millones de viajes de febrero a septiembre de 2026, un 88% más que en 2024 (6,1 millones).

- **Cómo se calcula:** En data/bicimad_daily_trips_weather.csv: suma `trips` entre el 1 de febrero y el 30 de septiembre de 2026 y de 2024; divide y resta 1.
- **Fichero:** [`data/bicimad_daily_trips_weather.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_daily_trips_weather.csv)
- **Script:** pipeline/refresh.py (función bicimad_daily)
- **Fuente original:** [EMT Madrid · datos abiertos BiciMAD](https://datos.emtmadrid.es)
- **Ojo:** El sistema también creció: más estaciones y bicis eléctricas. Son viajes, no personas.

### <a id="accidentes"></a>Los accidentes con bicicleta atendidos por la Policía Municipal han subido un 52% desde 2019: de 785 a 1.191 al año.

- **Cómo se calcula:** En data/madrid_bike_accidents_by_year.csv: `accidents` de 2025 entre `accidents` de 2019, menos 1.
- **Fichero:** [`data/madrid_bike_accidents_by_year.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/madrid_bike_accidents_by_year.csv), [`data/madrid_bike_accidents.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/madrid_bike_accidents.csv)
- **Script:** pipeline/refresh.py (función accidents)
- **Fuente original:** [Policía Municipal · Accidentes con bicicleta (300110)](https://datos.madrid.es/dataset/300110-0-accidentes-bicicleta)
- **Ojo:** Cuentan todas las bicis, no solo BiciMAD, y no hay kilómetros recorridos: no se puede calcular el riesgo por viaje. Solo constan los accidentes atendidos por la policía. 2026 está incompleto.

## Otras cifras

### <a id="sin_estacion"></a>7 barrios no tienen ninguna estación de BiciMAD: 1,4% de la población.

- **Cómo se calcula:** En data/madrid_barrios_bicimad.csv: barrios con `stations` = 0; suma su `population` entre el total.
- **Fichero:** [`data/madrid_barrios_bicimad.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/madrid_barrios_bicimad.csv)
- **Script:** pipeline/refresh.py (función barrios)
- **Fuente original:** [BiciMAD · feed en tiempo real (GBFS)](https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json); [Ayuntamiento de Madrid · Padrón a 1 de enero (300557)](https://datos.madrid.es/dataset/300557-0-poblacion-distrito-barrio); [Ayuntamiento de Madrid · Límites administrativos (900012)](https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas)

### <a id="viajes_12m"></a>16.146.211 viajes en BiciMAD en los últimos 12 meses con datos.

- **Cómo se calcula:** En data/bicimad_daily_trips_weather.csv: suma `trips` de los 365 días anteriores a la última fecha.
- **Fichero:** [`data/bicimad_daily_trips_weather.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_daily_trips_weather.csv)
- **Script:** pipeline/refresh.py (función bicimad_daily)
- **Fuente original:** [EMT Madrid · datos abiertos BiciMAD](https://datos.emtmadrid.es)

### <a id="record"></a>Récord de viajes en un día: 85.882 el 2026-09-08.

- **Cómo se calcula:** En data/bicimad_daily_trips_weather.csv: el máximo de `trips`.
- **Fichero:** [`data/bicimad_daily_trips_weather.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_daily_trips_weather.csv)
- **Script:** pipeline/refresh.py (función bicimad_daily)
- **Fuente original:** [EMT Madrid · datos abiertos BiciMAD](https://datos.emtmadrid.es)

### <a id="usuarios"></a>269.393 usuarios activos en 2026-09.

- **Cómo se calcula:** En data/bicimad_active_users_monthly.csv: `active_users` del último mes.
- **Fichero:** [`data/bicimad_active_users_monthly.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_active_users_monthly.csv)
- **Script:** pipeline/refresh.py (función bicimad_users)
- **Fuente original:** [EMT Madrid · datos abiertos BiciMAD](https://datos.emtmadrid.es)

### <a id="viajes_por_bici"></a>Cada bici de BiciMAD hace de media 4,7 viajes al día (la guía de la ITDP recomienda 4 a 8).

- **Cómo se calcula:** En data/bicimad_daily_trips_weather.csv: media diaria de `trips` de los últimos 12 meses entre 9.421 bicis (data/refresh_meta.json, `fleet`).
- **Fichero:** [`data/bicimad_daily_trips_weather.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_daily_trips_weather.csv), [`data/refresh_meta.json`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/refresh_meta.json)
- **Script:** pipeline/build_site.py
- **Fuente original:** [EMT Madrid · datos abiertos BiciMAD](https://datos.emtmadrid.es); [BiciMAD · feed en tiempo real (GBFS)](https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json); [ITDP · The Bikeshare Planning Guide](https://bikeshare.itdp.org/guide/goal-setting-initial-planning/examine-feasibility-choose-a-system-type/)
- **Ojo:** La flota viene del feed en tiempo real y no coincide con la de los informes municipales (unas 8.000).

### <a id="km_carril"></a>412 km de carril bici segregado en la ciudad, 11,8 por cada 100.000 habitantes.

- **Cómo se calcula:** En data/madrid_districts_cycling.csv: suma `exclusive_km` de los 21 distritos.
- **Fichero:** [`data/madrid_districts_cycling.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/madrid_districts_cycling.csv), [`data/madrid_bike_infrastructure.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/madrid_bike_infrastructure.csv)
- **Script:** pipeline/refresh.py (funciones infrastructure y districts)
- **Fuente original:** [Ayuntamiento de Madrid · Infraestructura ciclista (205107)](https://datos.madrid.es/dataset/205107-0-vias-ciclistas)
- **Ojo:** La prensa cuenta unos 292 km como segregados; el Ayuntamiento, unos 426. Aquí: la capa oficial de carril exclusivo, sin ciclocalles ni Anillo Verde.

### <a id="estaciones_carril"></a>Solo el 17% de las estaciones de BiciMAD tiene un carril bici segregado a menos de 50 m.

- **Cómo se calcula:** En data/bicimad_station_context.csv: porcentaje de estaciones `IN_SERVICE` con `m_to_exclusive_lane` ≤ 50.
- **Fichero:** [`data/bicimad_station_context.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_station_context.csv)
- **Script:** pipeline/refresh.py (función stations)
- **Fuente original:** [BiciMAD · feed en tiempo real (GBFS)](https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json); [Ayuntamiento de Madrid · Infraestructura ciclista (205107)](https://datos.madrid.es/dataset/205107-0-vias-ciclistas)

### <a id="recorrido_protegido"></a>Solo el 28,2% del recorrido de los viajes de BiciMAD (enero–febrero de 2023) va por carril separado del tráfico.

- **Cómo se calcula:** En data/bicimad_2023_routes_all.csv.gz: media de `share_exclusive` ponderada por `trips`.
- **Fichero:** [`data/bicimad_2023_routes_all.csv.gz`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/bicimad_2023_routes_all.csv.gz)
- **Script:** pipeline/historical/11_all_routes.py (método en docs/ROUTING.md)
- **Fuente original:** [EMT · Históricos de BiciMAD, viajes 2023 (900034)](https://datos.madrid.es/dataset/900034-0-bicimad-viajes-estaciones); [Ayuntamiento de Madrid · Infraestructura ciclista (205107)](https://datos.madrid.es/dataset/205107-0-vias-ciclistas)
- **Ojo:** Es un modelo: la ruta más probable sobre OpenStreetMap, no trazas GPS. Usa los últimos viajes publicados (49 días de 2023).

### <a id="plan_carriles"></a>El plan de carriles protegidos suma 23,0 km por 19,8 millones de euros y devuelve 2,64 € por cada euro (relación beneficio-coste).

- **Cómo se calcula:** En data/lane_network_plans.json: `bestfirst` (`km`, `build_eur`, `bcr`).
- **Fichero:** [`data/lane_network_plans.json`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/lane_network_plans.json), [`data/lane_network_plan.csv`](https://github.com/jaimeoliver1/madrid-en-bici/blob/main/data/lane_network_plan.csv)
- **Script:** pipeline/historical/15_lane_network.py (método en docs/METHOD_LANES.md; entradas fijadas con SHA-256)
- **Fuente original:** [EMT · Históricos de BiciMAD, viajes 2023 (900034)](https://datos.madrid.es/dataset/900034-0-bicimad-viajes-estaciones); [Ayuntamiento de Madrid · Infraestructura ciclista (205107)](https://datos.madrid.es/dataset/205107-0-vias-ciclistas)
- **Ojo:** Es una estimación con parámetros publicados (HEATCO, Broach et al.), no un presupuesto. Los supuestos y la sensibilidad están en docs/METHOD_LANES.md.

### <a id="reparto_modal"></a>La bici es el 0,5% de los viajes en Madrid (Barcelona 3,8%, París 11,2%, Copenhague 21%).

- **Cómo se calcula:** Cifra citada tal cual de la fuente; no se calcula aquí.
- **Fichero:** —
- **Script:** site/app.js (constante BENCH.modal)
- **Fuente original:** [CRTM · Encuesta Domiciliaria de Movilidad 2018](https://crtm.es/media/ml2ertro/jornada_presentacion_edm2018_resultados.pdf)
- **Ojo:** Último dato comparable (encuesta de 2018). Las cifras municipales más recientes usan datos de móviles y no son comparables.

---
Qué datos faltan y por qué: [DATA_SOURCES.md](DATA_SOURCES.md). Métodos: [ROUTING.md](ROUTING.md), [METHOD_LANES.md](METHOD_LANES.md).
