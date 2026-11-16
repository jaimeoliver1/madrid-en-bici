# Solicitud de acceso a Strava Metro

Borrador para pedir los datos de [Strava Metro](https://metro.strava.com) a través de una asociación ciclista de Madrid. Las referencias (§) remiten a los [términos de Strava Metro](https://metro.strava.com/terms), versión del 4 de septiembre de 2026; conviene releerlos antes de enviar nada.

## Qué es y para qué lo queremos

Strava Metro da, gratis a las organizaciones que aprueba, el número de recorridos en bici registrados con Strava en cada tramo de calle de OpenStreetMap ("edge counts"). Separa los trayectos al trabajo de los de ocio, y los cuenta por hora y por día de la semana. Los datos están agregados y anonimizados.

Nos serviría para dos cosas que hoy no podemos hacer:

1. **Ver por dónde va la gente de verdad**, también con bici propia. Hoy solo tenemos las rutas *estimadas* de BiciMAD (ver [DATA_SOURCES.md](DATA_SOURCES.md), "Routes").
2. **Saber cuántos ciclistas pasan por cada tipo de calle.** Para pasar de BiciMAD a todos los ciclistas usamos un único factor de 2,7, sacado de los aforos ([METHOD_LANES.md](METHOD_LANES.md) §2). Sin esta exposición no podemos medir si una calle con carril separado es más segura por km que una calle normal, y por eso el análisis deja fuera ese efecto (§4).

Strava sobrerrepresenta las salidas deportivas. Los aforos municipales siguen siendo la referencia, y los datos de Strava se calibrarían con ellos.

El [mapa de calor público de Strava](https://www.strava.com/maps/global-heatmap?sport=Ride) no sirve como fuente: sus condiciones prohíben descargarlo o reutilizarlo. La web solo enlaza a él.

## Por qué tiene que pedirlo una asociación

- **Solo organizaciones.** Metro se concede a entidades que planifican o mantienen infraestructura ciclista, o que buscan influir en esa planificación. Además, Strava tiene que aprobar el tipo de proyecto, a su criterio (§2.1.1). Madrid en bici es un proyecto ciudadano sin personalidad jurídica, así que no puede pedirlo por sí mismo.
- **Las cuentas son de empleados de la entidad.** Solo pueden entrar empleados de la organización que tiene la licencia (§1.2). Cada acceso es personal y no se puede compartir (§2.1.2).
- **Los colaboradores voluntarios no cuentan.** Una persona externa solo puede acceder como consultora, con contrato escrito y un correo de su propia organización. Los términos excluyen de forma expresa las colaboraciones informales y el voluntariado (§2.4).

**Cómo encaja:**
- La asociación hace la solicitud.
- Una persona empleada por ella guarda el acceso, descarga los datos y ejecuta en su ordenador nuestro script de análisis, que es público.
- Madrid en bici recibe solo los resultados agregados, que son el "informe" que Strava revisa antes de publicarlo.
- Los datos brutos no salen nunca de la asociación.

**Preguntas para Strava antes de solicitar** (al contacto de metro.strava.com):
1. ¿Puede un socio voluntario de la asociación ser usuario autorizado, o tiene que ser empleado?
2. ¿Podemos publicar en un repositorio abierto los resultados agregados? Serían ratios por tipo de calle y un mapa en cinco franjas relativas, sin conteos.
3. ¿Hay datos para el municipio de Madrid? ¿Desde qué fecha (nos interesa enero–febrero de 2023)?

## Correo a la asociación (borrador)

> **Asunto:** Datos de Strava Metro para Madrid: ¿los pedimos juntos?
>
> Hola:
>
> Soy [nombre], de Madrid en bici (madrid-en-bici.vercel.app). Es una web ciudadana que analiza con datos abiertos cómo se mueve la gente en bici por Madrid y dónde convendría poner los próximos carriles protegidos.
>
> Strava ofrece gratis a las asociaciones ciclistas su servicio Strava Metro: cuántos ciclistas pasan por cada calle, separando los trayectos al trabajo de los de ocio. Con esos datos podríamos mostrar por dónde va de verdad la gente con bici propia, no solo con BiciMAD, y reforzar la propuesta de carriles con cifras de uso reales.
>
> Strava solo se lo concede a organizaciones, y el acceso tiene que tenerlo alguien de la propia entidad. Por eso os proponemos:
> - que lo solicitéis vosotros;
> - que una persona de la asociación ejecute nuestro análisis, que es público, en su ordenador;
> - que publiquemos juntos los resultados, con la mención de Strava y después de su revisión.
>
> Nosotros preparamos la solicitud y el análisis.
>
> ¿Os interesa? Os cuento los detalles cuando queráis.
>
> Un saludo,
> [nombre]

**A quién escribir:** a Pedalibre; a ConBici, a través de sus grupos en Madrid; o a otra asociación ciclista de la ciudad. Hace falta que sea una entidad legal, con correo propio, y que tenga a alguien empleado o pueda firmar un contrato de consultoría.

## Respuestas para la solicitud (en inglés)

La solicitud se hace en [metroview.strava.com/application](https://metroview.strava.com/application).
- **Primero se crea una cuenta:** nombre, correo de la organización y contraseña.
- **Las preguntas del proyecto vienen después**, y no se ven sin cuenta. Estas respuestas son para adaptar:

- **Organization:** [Association name], a non-profit cycling advocacy association in Madrid, Spain.
- **Project title:** Where people cycle in Madrid: evidence for the next protected bike lanes.
- **Project description:** We work with Madrid en bici, an open, non-commercial analysis of cycling in Madrid. It already models BiciMAD bike-share routes on OpenStreetMap and ranks protected-lane candidates by cost and benefit. Strava Metro edge counts would show where all cyclists ride, not only bike-share users. We would compare them with the city's automatic bike counters, to estimate cyclist volumes by street type. That improves the safety and demand estimates behind our protected-lane proposals, which we share with the City Council.
- **Project type:** Active transportation advocacy and planning analysis.
- **Area of interest:** Municipality of Madrid (Comunidad de Madrid, Spain). If the county is the finest level available, choose the one that contains the city of Madrid.
- **Data requested:** Cycling edge counts (rides, and e-bike rides if available), commute and leisure separately, by hour of day and day of week. Periods:
  - the last 12 months;
  - 1 January – 18 February 2023, to match the last published bike-share trip data and the 2023 counters.
- **How results will be shared:**
  - On a public website and in its open-source repository, as aggregated results only: ratios by street type, and maps in relative bands.
  - Raw counts are never published.
  - Each report goes to Strava 30 days before publication and carries the required attribution.

## Datos que pedimos

| Qué | Detalle |
|---|---|
| Conteos por tramo (edge counts) | Bici y, si existe, bici eléctrica |
| Propósito | Trabajo y ocio por separado |
| Tiempo | Por hora del día y día de la semana |
| Periodos | Últimos 12 meses, y 1 de enero – 18 de febrero de 2023 |
| Zona | Municipio de Madrid |
| Formato | Shapefile o el formato SIG que dé Metro, ligado a OpenStreetMap |

## A qué nos comprometemos

- **Los datos brutos no se publican nunca** (§2.2.3):
  - Se quedan en el ordenador de la persona autorizada, en `.cache/strava_metro/`, fuera de git.
  - En `pipeline/historical/inputs.json` solo se anota su huella SHA-256, como entrada privada.
  - Ningún conteo por calle va a `data/`, `site/data.js` ni `site/route-graph.json`.
- **Solo se publican resultados agregados:** ratios por tipo de calle, comparación con los aforos y mapas en franjas relativas, sin cifras por calle.
- **Mención obligatoria en cada panel, documento o publicación** (§2.2.1(d)), con este texto exacto: "This report includes aggregated and de-identified data from Strava Metro." En español la acompañamos de: "Este análisis incluye datos agregados y anonimizados de Strava Metro."
- **Revisión previa** (§2.2.2):
  - Cada pieza se envía a Strava 30 días antes de publicarla.
  - Si no contesta en ese plazo, se puede publicar.
  - Aun así, puede pedir cambios después.
- **Sin aprendizaje automático:** los datos no se usan para entrenar ni validar modelos de inteligencia artificial, ni para crear conjuntos de datos derivados (§2.3(viii), §2.8).
- **Solo para el proyecto aprobado.** El acceso dura un año y Strava decide si lo renueva.
- **Al terminar el acceso:**
  - Se borran los datos brutos (§6.2(b)).
  - Lo ya publicado puede seguir en línea si conserva la mención y se siguen cumpliendo las condiciones (§6.2).

## Después de la aprobación

1. **Entrada privada:** la descarga se fija por su SHA-256 en una sección `private` de `pipeline/historical/inputs.json`. `fetch_inputs.py` solo lee `downloads` y `vendored`, así que la salta.
2. **Script nuevo `pipeline/historical/17_strava_metro.py`:**
   - Empareja los tramos de Metro con las calles del grafo (`bikegraph.py`).
   - Los compara con los aforos y con los flujos modelados de BiciMAD.
   - Solo escribe agregados, en `data/strava_metro_summary.json`.
3. **Web:** un panel "¿Por dónde va quien no usa BiciMAD?", junto al mapa de rutas, que solo aparece si existe ese resumen. Lleva la mención en el propio panel.
4. **Análisis de carriles:** el factor único de 2,7 se sustituye por factores por tipo de calle, y se recalculan los planes ([METHOD_LANES.md](METHOD_LANES.md)).
