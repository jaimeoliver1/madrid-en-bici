/* Madrid en bici: renders every section from window.MC (built by pipeline/build_site_data.py). */
(() => {
  const M = window.MC, K = M.k;

  // ---------- benchmarks from planning guides, studies and other cities (see Sources) ----------
  const BENCH = {
    usesPerBike: [4, 8],          // ITDP Bikeshare Planning Guide: daily uses per bike
    stationsKm2: [10, 16],        // ITDP: stations per km2 in the service area
    bikesPer1000: [10, 30],       // ITDP: bikes per 1,000 residents
    peersUses: [["París (Vélib')", 6.7], ["Barcelona (Bicing)", 6.7], ["Valencia (Valenbisi)", 4.3], ["Lisboa (Gira)", 4.0], ["Londres (Santander)", 2.1]],
    modal: [["Madrid", 0.5], ["Barcelona", 3.8], ["París", 11.2], ["Copenhague", 21]],
    barcelonaBikes1000: 4.7,
  };

  // ---------- language ----------
  const T = {
    es: {
      zoom_exitfull: "Salir de pantalla completa",
      zoom_full: "Pantalla completa",
      theme_light: "Modo claro",
      theme_dark: "Modo oscuro",
      b_pick: "Elige tu barrio",
      v_hill: " Sus estaciones están altas ({e} m de media), así que <b>a menudo se vacían</b>.",
      v_ok: "<b>Buena cobertura</b>: tienes estaciones cerca de casa.",
      v_mid: "Cobertura <b>aceptable</b>, aunque por debajo de lo recomendado.",
      v_low: "Hay estaciones, pero <b>pocas</b>: muchas veces tendrás que andar más de 300 m.",
      v_none: "Tu barrio <b>aún no tiene ninguna estación</b> de BiciMAD. Te tocará andar hasta un barrio vecino.",
      f_acc: "accidentes con bici desde 2019",
      f_lane: "hasta el carril protegido más cercano (mediana desde sus estaciones)",
      f_empty: "estaciones vacías ahora",
      f_bikes: "bicis en sus estaciones ahora",
      f_dens: "estaciones por km² (lo ideal: 10–16)",
      f_st: "estaciones BiciMAD",
      b_sub: "{d} · {p} vecinos",
      b_dist: "Distrito de {d}",
      b_noloc: "No hemos podido saber dónde estás",
      b_far: "Parece que estás fuera de Madrid",
      b_locate: "Usar mi ubicación",
      cov_h: "Dónde faltan estaciones",
      fix_h: "Seis cambios concretos",
      pl_lede: "Cada punto es una persona en una BiciMAD real, un jueves de enero. Dale al play y mira cómo la ciudad se despierta, va a trabajar y vuelve a casa.",
      pl_h: "Así se mueve Madrid en bici en 24 horas",
      pl_k: "Un día cualquiera",
      tab_ir: "Ir en bici", tab_mejorar: "Mejorar Madrid",
      hl_k: "Lo esencial", hl_h: "Tres cosas que hay que saber", hl_lede: "Tres cifras con su fuente. Cada una lleva su cálculo, el fichero de datos y la página original del dato.", hl_how: "Cómo lo sabemos →",
      hl_cobertura: "Cobertura", hl_crecimiento: "Uso", hl_accidentes: "Seguridad",
      fg_h: "Cada cifra, con su fuente", fg_lede: "Cada número que citamos, con la fórmula para repetirlo en una hoja de cálculo, el fichero de datos, el código y la página original.", fg_calc: "Cómo se calcula", fg_files: "Datos", fg_script: "Código", fg_src: "Fuente original", fg_caveat: "Ojo", fg_all: "Registro completo en GitHub", fg_err: "¿Ves un error? Abre un issue",
      sh_btn: "Compartir la nota de mi barrio", sh_kicker: "La nota de mi barrio", sh_rank: "Puesto {r} de {n} barrios en estaciones BiciMAD por km²", sh_st: "estaciones BiciMAD", sh_dens: "estaciones por km² · ideal 10–16", sh_lane: "al carril protegido más cercano", sh_acc: "accidentes con bici desde 2019",
      sh_foot: "Datos abiertos: EMT Madrid · Ayuntamiento de Madrid · OpenStreetMap", sh_text: "{b} es el barrio {r} de {n} en estaciones de BiciMAD por km². ¿Y el tuyo?", sh_saved: "Imagen guardada y texto copiado: pégalo donde quieras compartirla.", sh_err: "No hemos podido crear la imagen.",
      j_ruta: "Planea tu ruta", j_barrio: "¿Hay BiciMAD cerca?", j_tips: "Antes de salir",
      tips_k: "Antes de salir", tips_h: "Cuatro cosas que conviene saber", tips_lede: "Lo esencial de los datos, en corto. Abre cada tarjeta si quieres ver los gráficos.",
      more_data: "Ver datos", less_data: "Ocultar datos",
      to_city_h: "¿Qué haría falta para que fuera más fácil?", to_city_p: "La nota de Madrid, un plan de carriles protegidos con su coste y su beneficio, y seis cambios concretos.",
      to_ride_h: "¿Vas en bici?", to_ride_p: "Planea tu ruta por las calles más cómodas, mira las bicis de tu barrio en directo y lo que conviene saber antes de salir.",
      j_lanes: "Los carriles hoy", j_plan: "El plan de carriles", j_fixes: "Seis cambios", j_safety: "Accidentes", j_cov: "Estaciones", j_use: "Uso",
      ln_h: "La red de carriles, hoy", plan_k: "El plan", fix_k: "Qué hacer",
      sf_h: "Los accidentes crecen con los viajes",
      sf_lede: "Los accidentes con bici <b>crecen casi tanto como los viajes</b>: más bicis en la calle aún no han traído calles más seguras. Se concentran en unos pocos cruces (los tienes en <a href=\"#seguridad\">Ir en bici</a>), y arreglarlos es el segundo de los seis cambios.",
      cov_k: "BiciMAD", cov_lede: "Lo recomendado es una estación cada 300 m. Hoy solo el centro llega; en el resto de barrios hay que andar demasiado.",
      use_k: "Uso", use_h: "¿Cuánta gente va en bici?",
      use_lede: "BiciMAD bate un récord cada septiembre y por las calles más ciclistas pasan hasta {ctop} bicis al día. <b>Hay demanda; lo que falta es una red que la acompañe.</b>",
      hero_kicker: "BiciMAD y la bici en Madrid", pl_date: "Jueves 12 de enero de 2023", pl_moving: "bicis circulando", pl_flow: "El rastro azul se acumula: al final del día, las calles más usadas brillan más", pl_day: "Ver el día completo", pl_scrub: "Arrastra para moverte por el día", pl_play: "Reproducir", pl_pause: "Pausa", pl_note: "Recorridos estimados: la ruta en bici más probable entre las dos estaciones. <a href=\"https://claude.ai/artifact/GJbZpaqHckxf79TpvRCdbR\" target=\"_blank\" rel=\"noopener\">Ver el vídeo</a>.", pl_hour_trips: "viajes que empiezan cada hora", zoom_hint: "Usa Ctrl + rueda (o pellizca) para hacer zoom", zoom_in: "Acercar", zoom_out: "Alejar", zoom_reset: "Ver todo", hero_h1: "¿Cómo es moverse en bici por Madrid?",
      hero_lede: "Cada día, decenas de miles de personas cogen una BiciMAD. Aquí verás <b>dónde hay bicis, por dónde ir y qué falta</b>, con datos abiertos y en directo.",
      score_h: "La nota de Madrid", score_sub: "Cada tarjeta compara Madrid con lo que recomiendan las guías de planificación o con otras ciudades. La franja verde es el objetivo.",
      good: "Bien", mid: "A medias", bad: "Mal", target: "objetivo",
      t_use_q: "¿Se usan las bicis de BiciMAD?", t_use_u: "viajes por bici al día. Lo sano es entre 4 y 8. París y Barcelona: 6,7.",
      t_cov_q: "¿Hay estaciones cerca de casa?", t_cov_u: "estaciones por km² en el barrio de un madrileño medio. Lo recomendado: 10 a 16.",
      t_fleet_q: "¿Hay bicis suficientes?", t_fleet_u: "bicis por cada 1.000 vecinos. Lo recomendado: 10 a 30. Barcelona: 4,7.",
      t_modal_q: "¿Cuánta gente va en bici?", t_modal_u: "de los viajes en Madrid se hacen en bici. Así está frente a otras ciudades:",
      t_route_q: "¿Van protegidos los viajes?", t_route_u: "del recorrido de los viajes de BiciMAD va por carril separado del tráfico.",
      t_route_u2: "de las estaciones de BiciMAD tienen un carril separado a menos de 50 m.",
      t_safe_q: "¿Es seguro pedalear?", t_safe_u: "accidentes con bici en {y1}, un {p} más que en {y0}. Crecen casi tanto como los viajes.",
      s1_k: "Cuándo", s1_h: "¿Cuándo se usa más la bici?", s1_lede: "Los picos son a las 8 y entre las 18 y las 19 h, cuando la gente va y vuelve del trabajo: es cuando <b>más cuesta encontrar bici o hueco</b>. Y cada septiembre se bate un récord.",
      n_trips: "viajes en los últimos 12 meses", n_users: "personas la usaron en {m}", n_record: "viajes el {d}, el día récord", n_ebike: "bicis, todas eléctricas",
      s1_c1: "Cada año, más viajes", s1_c1n: "Media de viajes al día, mes a mes. Septiembre es el mes estrella; agosto, el más tranquilo.",
      s1_c2: "Viajes que empiezan cada hora", s1_c2n: "Entre semana hay dos picos: ir y volver del trabajo (datos de 2023).",
      weekday: "Laborable", weekend: "Fin de semana", trips_day: "viajes al día", trips_hour: "viajes por hora",
      s2_k: "Tu barrio", s2_h: "¿Tienes BiciMAD cerca de casa?",
      s2_lede: "Elige tu barrio, o tócalo en el mapa, y mira cuántas estaciones tienes, cuántas bicis hay ahora mismo y lo lejos que queda el carril bici.",
      s2_c1: "Estaciones por km², barrio a barrio", s2_c1n: "Cuanto más oscuro, más estaciones por km². Lo ideal son 10 a 16: una estación a menos de 300 m de cualquier portal.",
      s2_c2: "¿Dónde vive la gente?", s2_c2n: "Porcentaje de madrileños según cuántas estaciones hay en su barrio.",
      s2_c3: "Distrito a distrito", s2_c3n: "Anclajes de BiciMAD por cada 1.000 vecinos.",
      cov_none: "Sin estación", cov_low: "Menos de 4 por km²", cov_mid: "De 4 a 10", cov_ok: "10 o más (lo recomendado)",
      people: "vecinos", stations: "estaciones", per_km2: "por km²", docks_1000: "anclajes por 1.000 vecinos",
      s3_k: "Cuestas", s3_h: "¿Por qué mi estación siempre está vacía?",
      s3_lede: "Madrid tiene cuestas. La gente baja en bici hacia el río y vuelve en metro, así que <b>las estaciones de arriba se vacían y las de abajo se llenan</b>. Entre la estación más alta y la más baja hay 175 m de desnivel.",
      s3_c1: "Las de arriba pierden bicis, las de abajo ganan", s3_c1n: "Bicis que gana o pierde al día cada estación, según su altura (enero–febrero 2023).",
      s3_c2: "Estaciones vacías ahora mismo", s3_c2n: "Actualizado el {snap}. En rojo, sin ninguna bici.",
      empty: "Vacía", hasbikes: "Con bicis", gains: "gana", loses: "pierde", bikes_day: "bicis al día", m: "m",
      cuestas_callout: "<b>{e} de las {t} estaciones vacías</b> estaban por encima de 680 m de altura. Las estaciones altas tenían de media un {ho}% de sus anclajes con bici; las bajas, un {lo}%.",
      s4_k: "Carriles bici", s4_h: "¿Hay carril bici en mi camino?",
      s4_lede: "Probablemente sí, pero <b>casi nunca separado del tráfico</b>. La mitad de la red son ciclocarriles: una bici pintada en el suelo y 30 km/h, compartiendo la calle con los coches.",
      ln_x: "km de carril bici separado", ln_v: "km del Anillo Verde, en el borde de la ciudad", ln_s: "km de ciclocarril compartido con coches",
      s4_c1: "La red ciclista de Madrid", lane_x: "Carril separado", lane_v: "Anillo Verde", lane_p: "Calle preferente bici", lane_s: "Ciclocarril (compartido)", lane_st: "Estación BiciMAD",
      s4_c2: "¿Cuánto de tu viaje va protegido?", s4_c2n: "Calculamos la ruta en bici más probable de cada viaje de BiciMAD. El mapa muestra los 300 trayectos más repetidos, coloreados según la parte que va por carril separado.",
      routes_pending: "Calculando rutas…", route_share_h: "Viajes según la parte del camino que va protegida",
      s5_k: "Seguridad", s5_h: "¿Es seguro ir en bici?",
      s5_lede: "Casi todos los viajes acaban sin problema, pero la Policía Municipal registró <b id=\"acc-total\">{n}</b> accidentes con bici entre 2019 y {accend}. Se concentran en unos pocos cruces: conviene conocerlos.",
      s5_c1: "Dónde ocurren", s5_c1n: "Cada punto es un accidente. En rojo, heridos graves o fallecidos. Los círculos marcan los cruces con más accidentes.",
      s5_c2: "Accidentes por año", s5_c2n: "{partial}", s5_c3: "Los cruces donde más cuidado hay que tener", accidents: "accidentes", ebike_share: "en bici eléctrica",
      s6_k: "Tiempo", s6_h: "¿Y si llueve?",
      s6_lede: "Con lluvia fuerte se queda en casa <b>uno de cada cuatro viajes</b>. El calor, en cambio, apenas frena: Madrid pedalea a 35 grados.",
      s6_c1: "Viajes de BiciMAD frente a un día normal", s6_c1n: "100 = un día normal de esa época. Lluvia medida en El Retiro.",
      rain_dry: "Seco", rain_lt1: "Llovizna", rain_1to5: "1–5 mm", rain_5to10: "5–10 mm", rain_gt10: "Más de 10 mm", rain_t: "Según la lluvia", heat_t: "Según la temperatura máxima (días secos)",
      days: "días", normal: "de lo normal",
      s6_c2: "Las calles con más bicis", s6_c2n: "Bicis al día que cuentan los contadores automáticos del Ayuntamiento (media de 2023).",
      s7_k: "Para el Ayuntamiento", s7_h: "Lo que haría Madrid más fácil para ir en bici", s7_lede: "Esta parte es para quien decide: cómo está Madrid frente a lo que recomiendan las guías y otras ciudades, y seis cambios concretos basados en la investigación y en lo que ya funciona fuera.",
      lever_lanes: "Palanca: carriles bici", lever_bicimad: "Palanca: BiciMAD", lever_both: "Palanca: datos y gestión", now: "Hoy:", goal: "Objetivo:",
      m_h: "Cómo lo hemos calculado", src_h: "Fuentes",
      live_k: "Ahora mismo en BiciMAD", live_ago: "actualizado a las {t} · se refresca cada minuto", live_off: "sin conexión con BiciMAD: mostrando la foto del {snap}",
      lv_bikes: "bicis esperándote en las estaciones (de {fleet})", lv_empty: "estaciones sin ninguna bici", lv_full: "estaciones llenas, sin hueco para dejarla",
      lv_out: "bicis han salido de su estación desde que abriste esta página<sup><a href=\"#datos\">1</a></sup>",
      fr_h: "¿Cada cuánto se actualizan los datos?", fr_what: "Dato", fr_when: "Frecuencia", fr_upto: "Datos hasta", fr_src: "Fuente",
      fr_live: "En directo", fr_month: "Cada mes", fr_frozen: "Congelado",
      fr_r_live: "Bicis y anclajes libres en cada estación", fr_c_live: "Cada minuto, directamente desde tu navegador", fr_u_live: "Ahora",
      fr_r_trips: "Viajes diarios y usuarios de BiciMAD", fr_c_trips: "La EMT publica el mes anterior hacia el día 10",
      fr_r_acc: "Accidentes con bicicleta", fr_c_acc: "Registros de la Policía Municipal",
      fr_r_city: "Carriles bici, aparcabicis, población y barrios", fr_c_city: "Cuando el Ayuntamiento los cambia; lo revisamos cada mes", fr_u_city: "Revisado el {refreshed}",
      fr_r_wx: "Lluvia y temperatura (El Retiro)", fr_c_wx: "Diaria; la incorporamos cada mes",
      fr_r_2023: "Viajes uno a uno: rutas, cuestas, horas y la animación de 24 h", fr_c_2023: "La EMT no publica viajes individuales desde febrero de 2023. Los hemos pedido: solicitud al Portal de Transparencia y correo a la EMT (octubre de 2026).", fr_u_2023: "18 feb 2023",
      fr_r_cnt: "Contadores automáticos de bicis", fr_c_cnt: "Último año completo publicado", fr_u_cnt: "2023",
      fr_auto: "La web se actualiza sola el día 10 de cada mes. Última actualización: {refreshed}.",
      fr_fn1: "Contamos cuántas bicis desaparecen de cada estación entre una lectura y la siguiente (cada minuto). Es una estimación: si alguien coge y deja una bici en la misma estación en ese minuto no se ve, y las furgonetas que redistribuyen bicis también cuentan.",
      fc_bicimad: "Se actualiza cada mes · datos hasta {dlast}", fc_barrios: "Bicis en directo · estaciones revisadas cada mes", fc_cuestas: "Mapa en directo · flujos de 2023", fc_carriles: "Carriles revisados cada mes · rutas de 2023", fc_seguridad: "Se actualiza cada mes · datos hasta {accend}", fc_tiempo: "Se actualiza cada mes",
    },
    en: {
      zoom_exitfull: "Exit full screen",
      zoom_full: "Full screen",
      theme_light: "Light mode",
      theme_dark: "Dark mode",
      b_pick: "Pick your barrio",
      v_hill: " Its stations sit high ({e} m on average), so <b>they often run empty</b>.",
      v_ok: "<b>Good coverage</b>: there are stations close to home.",
      v_mid: "<b>Decent</b> coverage, though below the recommended level.",
      v_low: "There are stations, but <b>not many</b>: you'll often walk more than 300 m.",
      v_none: "Your barrio <b>has no BiciMAD station yet</b>. You'll have to walk to a neighbouring one.",
      f_acc: "bike accidents since 2019",
      f_lane: "to the nearest protected lane (median from its stations)",
      f_empty: "empty stations now",
      f_bikes: "bikes at its stations now",
      f_dens: "stations per km² (goal: 10–16)",
      f_st: "BiciMAD stations",
      b_sub: "{d} · {p} residents",
      b_dist: "{d} district",
      b_noloc: "We couldn't get your location",
      b_far: "Looks like you're outside Madrid",
      b_locate: "Use my location",
      cov_h: "Where stations are missing",
      fix_h: "Six concrete changes",
      pl_lede: "Each dot is a person on a real BiciMAD, one Thursday in January. Press play and watch the city wake up, go to work and head home.",
      pl_h: "How Madrid moves by bike in 24 hours",
      pl_k: "An ordinary day",
      tab_ir: "Ride", tab_mejorar: "Improve Madrid",
      hl_k: "The essentials", hl_h: "Three things worth knowing", hl_lede: "Three figures with their sources. Each links to its calculation, the data file and the original publisher's page.", hl_how: "How we know →",
      hl_cobertura: "Coverage", hl_crecimiento: "Use", hl_accidentes: "Safety",
      fg_h: "Every figure, with its source", fg_lede: "Every number we quote, with a formula to repeat it in a spreadsheet, the data file, the code and the original page.", fg_calc: "How it's calculated", fg_files: "Data", fg_script: "Code", fg_src: "Original source", fg_caveat: "Mind the gap", fg_all: "Full register on GitHub", fg_err: "Spotted a mistake? Open an issue",
      sh_btn: "Share my barrio's score", sh_kicker: "My barrio's score", sh_rank: "Number {r} of {n} barrios for BiciMAD stations per km²", sh_st: "BiciMAD stations", sh_dens: "stations per km² · ideal 10–16", sh_lane: "to the nearest protected lane", sh_acc: "bike accidents since 2019",
      sh_foot: "Open data: EMT Madrid · Madrid City Council · OpenStreetMap", sh_text: "{b} ranks {r} of {n} barrios for BiciMAD stations per km². What about yours?", sh_saved: "Image saved and text copied: paste it wherever you share it.", sh_err: "We couldn't create the image.",
      j_ruta: "Plan your route", j_barrio: "BiciMAD near you", j_tips: "Before you ride",
      tips_k: "Before you ride", tips_h: "Four things worth knowing", tips_lede: "The gist of the data, in short. Open a card if you want to see the charts.",
      more_data: "Show the data", less_data: "Hide the data",
      to_city_h: "What would make it easier?", to_city_p: "Madrid's report card, a protected-lane plan with its costs and benefits, and six concrete changes.",
      to_ride_h: "Do you ride?", to_ride_p: "Plan your route on the most comfortable streets, see live bikes in your barrio and what's worth knowing before you set off.",
      j_lanes: "Lanes today", j_plan: "The lane plan", j_fixes: "Six changes", j_safety: "Accidents", j_cov: "Stations", j_use: "Usage",
      ln_h: "The bike network today", plan_k: "The plan", fix_k: "What to do",
      sf_h: "Accidents grow with trips",
      sf_lede: "Bike accidents <b>are growing almost as fast as trips</b>: more bikes on the street haven't made the streets safer yet. They cluster at a few junctions (see them under <a href=\"#seguridad\">Ride</a>), and fixing those is the second of the six changes.",
      cov_k: "BiciMAD", cov_lede: "The goal is one station every 300 m. Today only the centre gets there; elsewhere the walk is too long.",
      use_k: "Usage", use_h: "How many people ride?",
      use_lede: "BiciMAD sets a record every September, and up to {ctop} bikes a day pass along the busiest cycling streets. <b>The demand is there; what's missing is a network to match it.</b>",
      hero_kicker: "BiciMAD and cycling in Madrid", pl_date: "Thursday 12 January 2023", pl_moving: "bikes on the move", pl_flow: "The blue trail builds up: by midnight, the busiest streets glow brightest", pl_day: "Show the whole day", pl_scrub: "Drag to move through the day", pl_play: "Play", pl_pause: "Pause", pl_note: "Estimated paths: the most likely bike route between the two stations. <a href=\"https://claude.ai/artifact/GJbZpaqHckxf79TpvRCdbR\" target=\"_blank\" rel=\"noopener\">Watch the video</a>.", pl_hour_trips: "trips starting each hour", zoom_hint: "Use Ctrl + scroll (or pinch) to zoom", zoom_in: "Zoom in", zoom_out: "Zoom out", zoom_reset: "Show all", hero_h1: "What's it like to get around Madrid by bike?",
      hero_lede: "Every day, tens of thousands of people take a BiciMAD. Here you'll see <b>where the bikes are, which way to go and what's missing</b>, with open, live data.",
      score_h: "Madrid's report card", score_sub: "Each card compares Madrid with what planning guides recommend or with other cities. The green band is the target.",
      good: "Good", mid: "So-so", bad: "Poor", target: "target",
      t_use_q: "Are BiciMAD bikes being used?", t_use_u: "trips per bike per day. Healthy is 4 to 8. Paris and Barcelona: 6.7.",
      t_cov_q: "Is there a station near home?", t_cov_u: "stations per km² in the average resident's neighbourhood. Recommended: 10 to 16.",
      t_fleet_q: "Are there enough bikes?", t_fleet_u: "bikes per 1,000 residents. Recommended: 10 to 30. Barcelona: 4.7.",
      t_modal_q: "How many people ride?", t_modal_u: "of trips in Madrid are by bike. Compared with other cities:",
      t_route_q: "Are trips protected?", t_route_u: "of the distance ridden on BiciMAD trips runs on a lane separated from traffic.",
      t_route_u2: "of BiciMAD stations have a separated lane within 50 m.",
      t_safe_q: "Is it safe to ride?", t_safe_u: "bike accidents in {y1}, {p} more than in {y0}. They grow almost as fast as trips.",
      s1_k: "When", s1_h: "When do people ride?", s1_lede: "The peaks are at 8 am and between 6 and 7 pm, when people go to and from work: that's when <b>it's hardest to find a bike or a free dock</b>. And every September sets a new record.",
      n_trips: "trips in the last 12 months", n_users: "people used it in {m}", n_record: "trips on {d}, the record day", n_ebike: "bikes, all electric",
      s1_c1: "More trips every year", s1_c1n: "Average trips per day, month by month. September is the busiest month; August the quietest.",
      s1_c2: "Trips starting each hour", s1_c2n: "Weekdays have two peaks: going to and coming back from work (2023 data).",
      weekday: "Weekday", weekend: "Weekend", trips_day: "trips a day", trips_hour: "trips an hour",
      s2_k: "Your barrio", s2_h: "Is there a BiciMAD near you?",
      s2_lede: "Pick your barrio, or tap it on the map, and see how many stations you have, how many bikes there are right now and how far the nearest bike lane is.",
      s2_c1: "Stations per km², neighbourhood by neighbourhood", s2_c1n: "Darker means more stations per km². The goal is 10 to 16: a station within 300 m of every front door.",
      s2_c2: "Where do people live?", s2_c2n: "Share of residents by how many stations their neighbourhood has.",
      s2_c3: "District by district", s2_c3n: "BiciMAD docks per 1,000 residents.",
      cov_none: "No station", cov_low: "Under 4 per km²", cov_mid: "4 to 10", cov_ok: "10 or more (recommended)",
      people: "residents", stations: "stations", per_km2: "per km²", docks_1000: "docks per 1,000 residents",
      s3_k: "Hills", s3_h: "Why is my station always empty?",
      s3_lede: "Madrid is hilly. People ride down towards the river and come back by metro, so <b>stations up the hill empty out and those at the bottom fill up</b>. There are 175 m between the highest and the lowest station.",
      s3_c1: "Uphill stations lose bikes, downhill ones gain", s3_c1n: "Bikes each station gains or loses per day, by its height (January–February 2023).",
      s3_c2: "Empty stations right now", s3_c2n: "Updated {snap}. Red: no bikes at all.",
      empty: "Empty", hasbikes: "Has bikes", gains: "gains", loses: "loses", bikes_day: "bikes a day", m: "m",
      cuestas_callout: "<b>{e} of the {t} empty stations</b> were above 680 m. High stations had on average {ho}% of their docks holding a bike; low ones, {lo}%.",
      s4_k: "Bike lanes", s4_h: "Is there a bike lane on my way?",
      s4_lede: "Probably, but <b>rarely separated from traffic</b>. Half the network is shared lanes: a bike painted on the road and a 30 km/h limit, sharing the street with cars.",
      ln_x: "km of separated bike lane", ln_v: "km of the Anillo Verde ring, at the city's edge", ln_s: "km of shared lane with cars",
      s4_c1: "Madrid's cycling network", lane_x: "Separated lane", lane_v: "Anillo Verde ring", lane_p: "Bike-priority street", lane_s: "Shared lane", lane_st: "BiciMAD station",
      s4_c2: "How much of your ride is protected?", s4_c2n: "We worked out the most likely bike route of every BiciMAD trip. The map shows the 300 most common trips, coloured by how much of the way runs on a separated lane.",
      routes_pending: "Routing trips…", route_share_h: "Trips by how much of the route is protected",
      s5_k: "Safety", s5_h: "Is it safe to ride?",
      s5_lede: "Almost every ride ends fine, but the municipal police recorded <b id=\"acc-total\">{n}</b> bike accidents between 2019 and {accend}. They cluster at a few junctions worth knowing.",
      s5_c1: "Where they happen", s5_c1n: "Each dot is one accident. Red: serious injury or death. Circles mark the junctions with the most accidents.",
      s5_c2: "Accidents per year", s5_c2n: "{partial}", s5_c3: "The junctions to take most care at", accidents: "accidents", ebike_share: "on an e-bike",
      s6_k: "Weather", s6_h: "What if it rains?",
      s6_lede: "Heavy rain keeps <b>one in four trips</b> at home. Heat barely matters: Madrid rides at 35 °C.",
      s6_c1: "BiciMAD trips against a normal day", s6_c1n: "100 = a normal day for that time of year. Rain measured at El Retiro.",
      rain_dry: "Dry", rain_lt1: "Drizzle", rain_1to5: "1–5 mm", rain_5to10: "5–10 mm", rain_gt10: "Over 10 mm", rain_t: "By rain", heat_t: "By top temperature (dry days)",
      days: "days", normal: "of normal",
      s6_c2: "The streets with the most bikes", s6_c2n: "Bikes per day counted by the city's automatic counters (2023 average).",
      s7_k: "For the City Council", s7_h: "What would make Madrid easier to ride", s7_lede: "This part is for decision makers: how Madrid compares with planning guides and other cities, and six concrete changes based on research and on what already works elsewhere.",
      lever_lanes: "Lever: bike lanes", lever_bicimad: "Lever: BiciMAD", lever_both: "Lever: data and management", now: "Today:", goal: "Goal:",
      m_h: "How we worked it out", src_h: "Sources",
      live_k: "BiciMAD right now", live_ago: "updated at {t} · refreshes every minute", live_off: "can't reach BiciMAD: showing the snapshot from {snap}",
      lv_bikes: "bikes waiting at stations (out of {fleet})", lv_empty: "stations with no bikes", lv_full: "stations full, nowhere to drop yours",
      lv_out: "bikes have left their station since you opened this page<sup><a href=\"#datos\">1</a></sup>",
      fr_h: "How often is the data updated?", fr_what: "Data", fr_when: "How often", fr_upto: "Data up to", fr_src: "Source",
      fr_live: "Live", fr_month: "Monthly", fr_frozen: "Frozen",
      fr_r_live: "Bikes and free docks at every station", fr_c_live: "Every minute, straight from your browser", fr_u_live: "Now",
      fr_r_trips: "BiciMAD daily trips and users", fr_c_trips: "EMT publishes the previous month around the 10th",
      fr_r_acc: "Bike accidents", fr_c_acc: "Municipal police records",
      fr_r_city: "Bike lanes, bike racks, population and barrios", fr_c_city: "When the City Council changes them; we check every month", fr_u_city: "Checked on {refreshed}",
      fr_r_wx: "Rain and temperature (El Retiro)", fr_c_wx: "Daily; we add it every month",
      fr_r_2023: "Trip-by-trip data: routes, hills, hours and the 24-hour animation", fr_c_2023: "EMT has not published individual trips since February 2023. We have asked for them: a request through the Transparency Portal and an email to EMT (October 2026).", fr_u_2023: "18 Feb 2023",
      fr_r_cnt: "Automatic bike counters", fr_c_cnt: "Latest full year published", fr_u_cnt: "2023",
      fr_auto: "The site updates itself on the 10th of every month. Last update: {refreshed}.",
      fr_fn1: "We count how many bikes disappear from each station between one reading and the next (every minute). It's an estimate: a bike taken and returned to the same station within that minute isn't seen, and the vans that rebalance bikes are counted too.",
      fc_bicimad: "Updated monthly · data up to {dlast}", fc_barrios: "Live bikes · stations checked monthly", fc_cuestas: "Live map · 2023 flows", fc_carriles: "Lanes checked monthly · 2023 routes", fc_seguridad: "Updated monthly · data up to {accend}", fc_tiempo: "Updated monthly",
    },
  };
  let L = "es";
  try { const s = localStorage.getItem("mc-lang"); if (s === "en" || s === "es") L = s; } catch (e) {}
  const t = (k, v = {}) => (T[L][k] || T.es[k] || k).replace(/\{(\w+)\}/g, (_, x) => v[x] ?? "");
  const loc = () => d3.formatLocale(L === "es" ? { decimal: ",", thousands: ".", grouping: [3], currency: ["", " €"] } : { decimal: ".", thousands: ",", grouping: [3], currency: ["€", ""] });
  const nf = (v, s = ",") => loc().format(s)(v);
  const n1 = v => loc().format(",.1f")(v);
  const pct = v => (L === "es" ? n1(v).replace(/,0$/, "") + " %" : n1(v).replace(/\.0$/, "") + "%");
  const big = v => v >= 1e6 ? (L === "es" ? n1(v / 1e6) + " M" : n1(v / 1e6) + "M") : nf(v);
  const fdate = s => new Date(s + "T12:00:00Z").toLocaleDateString(L === "es" ? "es-ES" : "en-GB", { day: "numeric", month: "long", year: "numeric" });
  const fmonth = s => new Date(s + "-15T12:00:00Z").toLocaleDateString(L === "es" ? "es-ES" : "en-GB", { month: "long", year: "numeric" });
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

  // ---------- shared chart helpers ----------
  function svgIn(box, h) {
    box.replaceChildren();
    const W = Math.max(280, box.clientWidth);
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${h}`).attr("width", W).attr("height", h);
    return { svg, W };
  }
  function tip(box) {
    const d = el("div", "tip"); d.hidden = true; box.append(d);
    return {
      show(x, y, title, lines) {
        d.replaceChildren(el("b", null, title), ...lines.map(l => el("div", null, l)));
        d.hidden = false;
        const W = box.clientWidth; let lx = x + 12; if (lx + d.offsetWidth > W) lx = Math.max(0, x - d.offsetWidth - 12);
        let ly = y - d.offsetHeight - 10; if (ly < 0) ly = y + 14;
        d.style.left = lx + "px"; d.style.top = ly + "px";
      },
      hide() { d.hidden = true; },
    };
  }
  function textW(svg, s, size = 11) { const tt = svg.append("text").style("font-size", size + "px").text(s); const w = tt.node().getComputedTextLength(); tt.remove(); return w; }

  // vertical bars: rows [{label, value, color?, title, lines}]
  function vbars(box, rows, o = {}) {
    const h = o.h || 220, { svg, W } = svgIn(box, h);
    const max = o.max || d3.max(rows, r => r.value) * 1.08, min = Math.min(0, d3.min(rows, r => r.value));
    const y = d3.scaleLinear([min, max], [h - 26, 18]).nice();
    const ticks = y.ticks(4), ml = Math.max(...ticks.map(v => textW(svg, o.fmt ? o.fmt(v) : nf(v)))) + 8;
    const x = d3.scaleBand(rows.map((_, i) => i), [ml, W]).padding(0.22);
    ticks.forEach(v => { svg.append("line").attr("x1", ml).attr("x2", W).attr("y1", y(v)).attr("y2", y(v)).attr("stroke", css("--line")); svg.append("text").attr("x", ml - 6).attr("y", y(v)).attr("dy", ".32em").attr("text-anchor", "end").text(o.fmt ? o.fmt(v) : nf(v)); });
    if (o.ref != null) { svg.append("line").attr("x1", ml).attr("x2", W).attr("y1", y(o.ref)).attr("y2", y(o.ref)).attr("stroke", css("--ink")).attr("stroke-dasharray", "4 4"); }
    const tp = tip(box), bw = Math.min(40, x.bandwidth());
    svg.append("g").selectAll("rect").data(rows).join("rect")
      .attr("x", (r, i) => x(i) + (x.bandwidth() - bw) / 2).attr("width", bw)
      .attr("y", r => y(Math.max(0, r.value))).attr("height", r => Math.max(1, Math.abs(y(r.value) - y(0)))).attr("rx", Math.min(4, bw / 2)).attr("data-anim", "v").attr("data-base", y(0))
      .attr("fill", r => r.color || css("--sky"))
      .on("pointermove", (ev, r) => { const [a, b] = d3.pointer(ev, box); tp.show(a, b, r.title || r.label, r.lines || []); }).on("pointerleave", () => tp.hide());
    const every = Math.ceil(rows.length / Math.max(1, Math.floor((W - ml) / (o.labelW || 46))));
    rows.forEach((r, i) => { if (i % every === 0 || o.allLabels) svg.append("text").attr("x", x(i) + x.bandwidth() / 2).attr("y", h - 8).attr("text-anchor", "middle").text(r.label); });
    if (o.valueLabels) rows.forEach((r, i) => svg.append("text").attr("class", "lbl").attr("x", x(i) + x.bandwidth() / 2).attr("y", y(Math.max(0, r.value)) - 5).attr("text-anchor", "middle").text(o.valueLabels(r)));
  }
  // horizontal bars: rows [{label, value, color?, text}]
  function hbars(box, rows, o = {}) {
    const rh = o.rh || 30, h = rows.length * rh + 6, { svg, W } = svgIn(box, h);
    const lw = Math.min(W * 0.48, Math.max(...rows.map(r => textW(svg, r.label, 12))) + 10);
    const ext = d3.extent([0, ...rows.map(r => r.value)]), x = d3.scaleLinear(o.domain || ext, [lw, W - (o.mr || 70)]);
    const tp = tip(box);
    const g = svg.selectAll("g.r").data(rows).join("g").attr("transform", (r, i) => `translate(0,${i * rh})`);
    g.append("text").attr("class", "lbl").attr("x", lw - 8).attr("y", rh / 2).attr("dy", ".32em").attr("text-anchor", "end").style("font-weight", 600).text(r => r.label);
    g.append("rect").attr("x", r => Math.min(x(0), x(r.value))).attr("width", r => Math.max(2, Math.abs(x(r.value) - x(0)))).attr("y", 6).attr("height", rh - 12).attr("rx", 4).attr("data-anim", "h").attr("data-base", x(0))
      .attr("fill", r => r.color || css("--sky")).on("pointermove", (ev, r) => { const [a, b] = d3.pointer(ev, box); if (r.title) tp.show(a, b, r.title, r.lines || []); }).on("pointerleave", () => tp.hide());
    g.append("text").attr("x", r => r.value >= 0 ? x(r.value) + 6 : x(0) + 6).attr("text-anchor", "start").attr("y", rh / 2).attr("dy", ".32em").style("fill", css("--ink")).text(r => r.text);
    if (o.zero) svg.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 0).attr("y2", h).attr("stroke", css("--muted"));
  }
  // planar map projection fitted to the urban area (BiciMAD stations)
  function mapFrame(W, padFrac = 0.04, maxH = 640) {
    const lat0 = 40.43, k = Math.cos(lat0 * Math.PI / 180);
    const lats = M.stations.map(s => s[0]), lons = M.stations.map(s => s[1] * k);
    let [x0, x1] = d3.extent(lons), [y0, y1] = d3.extent(lats);
    const px = (x1 - x0) * padFrac, py = (y1 - y0) * padFrac; x0 -= px; x1 += px; y0 -= py; y1 += py;
    const h = Math.min(maxH, Math.max(340, W * (y1 - y0) / (x1 - x0)));
    const s = Math.min(W / (x1 - x0), h / (y1 - y0)), ox = (W - (x1 - x0) * s) / 2, oy = (h - (y1 - y0) * s) / 2;
    const P = (lon, lat) => [ox + (lon * k - x0) * s, h - oy - (lat - y0) * s];
    const path = str => "M" + str.split(" ").map(p => { const [a, b] = p.split(","); const q = P(+a, +b); return q[0].toFixed(1) + " " + q[1].toFixed(1); }).join("L");
    const inv = (x, y) => [((x - ox) / s + x0) / k, (h - oy - y) / s + y0];  // map point -> lon, lat
    return { h, P, path, inv };
  }
  function mapBase(box, maxH) {
    const W = Math.max(280, box.clientWidth), F = mapFrame(W, 0.04, maxH);
    const { svg } = svgIn(box, F.h);
    const id = box.id + "-clip";
    svg.append("clipPath").attr("id", id).append("rect").attr("width", W).attr("height", F.h).attr("rx", 10);
    const g = svg.append("g").attr("clip-path", `url(#${id})`).append("g");
    zoomable(box, svg, g, W, F.h);
    return { svg, g, W, F };
  }
  // wheel zoom needs Ctrl/Cmd (so the page still scrolls), touch needs two fingers; dots shrink back as you zoom in
  function zoomable(box, svg, g, W, H) {
    let hintT = null;
    const showHint = () => {
      let h = box.querySelector(".zoomhint");
      if (!h) { h = el("div", "zoomhint", t("zoom_hint")); box.append(h); }
      h.hidden = false; clearTimeout(hintT); hintT = setTimeout(() => { h.hidden = true; }, 1400);
    };
    const zoom = d3.zoom().scaleExtent([1, 14]).extent([[0, 0], [W, H]]).translateExtent([[0, 0], [W, H]])
      .filter(ev => ev.type === "wheel" ? (ev.ctrlKey || ev.metaKey) : ev.type === "touchstart" ? ev.touches.length > 1 : !ev.button)
      .on("zoom", ev => {
        g.attr("transform", ev.transform);
        const k = ev.transform.k;
        g.selectAll("circle").each(function () { if (this.__r0 == null) this.__r0 = +this.getAttribute("r"); this.setAttribute("r", this.__r0 / Math.pow(k, 0.7)); });
        g.selectAll("text").each(function () { if (this.__f0 == null) this.__f0 = 12; this.style.fontSize = (this.__f0 / k) + "px"; });
        g.selectAll("text.t2").attr("display", k < 1.8 ? "none" : null);
        g.selectAll("text.place").style("stroke-width", (3 / k) + "px");  // keep the label halo thin when zoomed
      });
    svg.call(zoom).on("dblclick.zoom", null).style("touch-action", "pan-y");
    svg.on("wheel.hint", ev => { if (!ev.ctrlKey && !ev.metaKey) showHint(); });
    const ui = el("div", "zoomui");
    [["+", "zoom_in", () => svg.transition().duration(350).call(zoom.scaleBy, 1.8)], ["−", "zoom_out", () => svg.transition().duration(350).call(zoom.scaleBy, 1 / 1.8)],
     ["⟲", "zoom_reset", () => svg.transition().duration(450).call(zoom.transform, d3.zoomIdentity)]].forEach(([s, k, f]) => {
      const b = el("button", null, s); b.type = "button"; b.title = t(k); b.setAttribute("aria-label", t(k)); b.addEventListener("click", f); ui.append(b);
    });
    ui.append(fullButton(box));
    box.append(ui);
    svg.node().__zoomer = zoom;  // so other scripts (routing.js) can zoom to a route
  }
  // ---------- full screen for any map: the browser's Fullscreen API, or a fixed overlay where it is missing (iPhone) ----------
  const ICON_FULL = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const ICON_EXIT = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><path d="M6 2v4H2M14 6h-4V2M10 14v-4h4M2 10h4v4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const fullTarget = box => box.closest(".planner") || box.closest(".player") || box.closest(".panel") || box;
  const isFull = el_ => document.fullscreenElement === el_ || el_.classList.contains("mapfull");
  function setFullLabel(b, on) { b.innerHTML = on ? ICON_EXIT : ICON_FULL; b.title = t(on ? "zoom_exitfull" : "zoom_full"); b.setAttribute("aria-label", b.title); }
  function toggleFull(target) {
    if (isFull(target)) {
      if (document.fullscreenElement) document.exitFullscreen();
      else { target.classList.remove("mapfull"); document.body.classList.remove("noscroll"); fullChanged(); }
      return;
    }
    const css = () => { target.classList.add("mapfull"); document.body.classList.add("noscroll"); fullChanged(); };
    if (target.requestFullscreen && document.fullscreenEnabled) target.requestFullscreen().catch(css); else css();
  }
  function fullChanged() {
    document.querySelectorAll(".fullbtn").forEach(b => setFullLabel(b, isFull(fullTarget(b.closest(".mapbox, .stage")))));
    window.dispatchEvent(new Event("mc-full"));
  }
  document.addEventListener("fullscreenchange", fullChanged);
  document.addEventListener("keydown", ev => { if (ev.key === "Escape") document.querySelectorAll(".mapfull").forEach(x => toggleFull(x)); });
  function fullButton(box) {
    const b = el("button", "fullbtn"); b.type = "button"; setFullLabel(b, false);
    b.addEventListener("click", () => toggleFull(fullTarget(box)));
    return b;
  }
  const ringsPath = (F, rings) => rings.split("|").map(r => F.path(r) + "Z").join("");
  // context from OpenStreetMap (basemap.js): parks, the Manzanares and main roads over the barrio fill; landmark names go on top of the data
  function context(g, F, o = {}) {
    const B = window.BASE; if (!B) return;
    const c = g.append("g").attr("class", "ctx").style("pointer-events", "none");
    if (!o.faint) c.selectAll("path.pk").data(B.parks).join("path").attr("class", "pk").attr("d", r => F.path(r) + "Z").attr("fill", css("--park"));
    c.selectAll("path.w").data(B.water).join("path").attr("class", "w").attr("d", r => F.path(r)).attr("fill", "none").attr("stroke", css("--water")).attr("stroke-width", 2.6).attr("vector-effect", "non-scaling-stroke");
    if (o.roads === false) return;
    const W_ = { m: 1.8, p: 1, s: 0.55 };
    c.selectAll("path.rd").data(B.roads).join("path").attr("class", "rd").attr("d", r => F.path(r[1])).attr("fill", "none").attr("stroke", o.faint ? css("--card") : css("--road"))
      .attr("stroke-opacity", o.faint ? 0.6 : 1).attr("stroke-width", r => W_[r[0]]).attr("stroke-linecap", "round").attr("vector-effect", "non-scaling-stroke");
  }
  function places(g, F) {
    const B = window.BASE; if (!B) return;
    g.append("g").attr("class", "places").style("pointer-events", "none").selectAll("text").data(B.places).join("text")
      .attr("class", p => "place" + (p[4] > 1 ? " t2" : "")).attr("x", p => F.P(p[3], p[2])[0]).attr("y", p => F.P(p[3], p[2])[1]).attr("text-anchor", "middle").attr("dy", ".35em")
      .attr("display", p => p[4] > 1 ? "none" : null).text(p => L === "es" ? p[0] : p[1])
      .each(function (p) { this.__f0 = p[4] > 1 ? 10.5 : 11.5; this.style.fontSize = this.__f0 + "px"; });
  }

  // ---------- your barrio: pick one (or use your location) and get a card with its stations, live bikes, lanes and accidents ----------
  let covMap = null, myBarrio = null;
  try { myBarrio = localStorage.getItem("mc-barrio"); } catch (e) {}
  const RINGS = new Map(M.barrios.map(b => [b[0], b[5].split("|").map(r => r.split(" ").map(q => q.split(",").map(Number)))]));
  function inBarrio(name, lon, lat) {
    let inside = false;
    for (const ring of RINGS.get(name)) for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i], [xj, yj] = ring[j];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  }
  const BOX = new Map([...RINGS].map(([n, rs]) => { const a = rs.flat(); return [n, [d3.min(a, p => p[0]), d3.min(a, p => p[1]), d3.max(a, p => p[0]), d3.max(a, p => p[1])]]; }));
  const within = (n, lon, lat) => { const b = BOX.get(n); return lon >= b[0] && lon <= b[2] && lat >= b[1] && lat <= b[3] && inBarrio(n, lon, lat); };
  const accBy = new Map();
  function pickBarrio(name) {
    if (!RINGS.has(name)) return;
    myBarrio = name; try { localStorage.setItem("mc-barrio", name); } catch (e) {}
    try { history.replaceState(null, "", "?barrio=" + encodeURIComponent(name) + location.hash); } catch (e) {}  // the address bar is the link to share
    const sel = document.getElementById("b-select"); if (sel.value !== name) sel.value = name;
    document.getElementById("b-msg").textContent = "";
    barrioCard();
  }
  function barrio() {
    const sel = document.getElementById("b-select");
    const byD = d3.groups(M.barrios.slice().sort((a, b) => a[0].localeCompare(b[0], "es")), b => b[1]).sort((a, b) => a[0].localeCompare(b[0], "es"));
    sel.replaceChildren(el("option", null, t("b_pick")), ...byD.map(([d, bs]) => { const og = el("optgroup"); og.label = t("b_dist", { d }); bs.forEach(b => { const o = el("option", null, b[0]); o.value = b[0]; og.append(o); }); return og; }));
    sel.firstChild.disabled = true; sel.firstChild.value = "";
    sel.onchange = () => pickBarrio(sel.value);
    const loc = document.getElementById("b-locate"); loc.textContent = "◎ " + t("b_locate");
    loc.hidden = !("geolocation" in navigator);
    loc.onclick = () => navigator.geolocation.getCurrentPosition(pos => {
      const { longitude: lon, latitude: lat } = pos.coords, hit = M.barrios.find(b => within(b[0], lon, lat));
      if (hit) pickBarrio(hit[0]); else document.getElementById("b-msg").textContent = t("b_far");
    }, () => { document.getElementById("b-msg").textContent = t("b_noloc"); }, { timeout: 10000, maximumAge: 300000 });
    const asked = new URLSearchParams(location.search).get("barrio"); if (asked && RINGS.has(asked)) myBarrio = asked;  // a shared link wins over the saved choice
    if (!myBarrio || !RINGS.has(myBarrio)) myBarrio = RINGS.has("Sol") ? "Sol" : M.barrios[0][0];
    sel.value = myBarrio;
    barrioCard();
  }
  function barrioCard() {
    const b = M.barrios.find(x => x[0] === myBarrio), box = document.getElementById("b-card"); if (!b || !box) return;
    const st = M.stations.filter(s => within(b[0], s[1], s[0]));
    if (!accBy.has(b[0])) accBy.set(b[0], M.acc_points.filter(a => within(b[0], a[1], a[0])).length);
    const dens = b[4] / b[3], bikes = d3.sum(st, s => s[2]), empty = st.filter(s => s[2] === 0).length;
    const lane = st.length ? d3.median(st, s => s[5]) : null, elev = d3.mean(st.filter(s => s[4] != null), s => s[4]);
    const fact = (v, l, cls) => { const d = el("div", "fact" + (cls ? " " + cls : "")); d.append(el("span", "v", v), el("span", "l", l)); return d; };
    const h = el("div"); h.append(el("h3", null, b[0]), el("p", "sub", t("b_sub", { d: b[1], p: nf(b[2]) })));
    const v = el("p", "verdict"); v.innerHTML = t(b[4] === 0 ? "v_none" : dens < 4 ? "v_low" : dens < 10 ? "v_mid" : "v_ok") + (elev > 680 && st.length ? t("v_hill", { e: nf(Math.round(elev)) }) : "");
    const f = el("div", "facts");
    f.append(fact(nf(b[4]), t("f_st")), fact(n1(dens), t("f_dens"), dens >= 10 ? "ok" : "warn"),
      fact(st.length ? nf(bikes) : "–", t("f_bikes")), fact(st.length ? nf(empty) : "–", t("f_empty"), empty ? "warn" : null),
      fact(lane == null ? "–" : (lane < 1000 ? nf(Math.round(lane / 10) * 10) + " m" : n1(lane / 1000) + " km"), t("f_lane"), lane != null && lane <= 300 ? "ok" : "warn"),
      fact(nf(accBy.get(b[0])), t("f_acc")));
    const sh = el("div", "sharerow"), btn = el("button", "btn", t("sh_btn")); btn.type = "button";
    const note = el("span", "small muted"); note.id = "b-share-msg"; note.setAttribute("role", "status");
    btn.onclick = () => shareBarrio(b, st, lane, dens, note);
    sh.append(btn, note);
    box.replaceChildren(h, v, f, sh);
    if (covMap) covMap.g.select("path.sel").attr("d", ringsPath(covMap.F, b[5])).raise();
    if (covMap) covMap.g.select("g.places").raise();
  }

  // the shareable image: rank among the barrios, the four facts and the outline with its stations (drawn by share.js)
  const SITE = /^(localhost|127\.|\[::1\])/.test(location.hostname) || location.protocol === "file:" ? "https://madrid-en-bici.vercel.app" : location.origin;
  async function shareBarrio(b, st, lane, dens, note) {
    note.textContent = "";
    try {
      const rank = 1 + M.barrios.filter(x => x[4] / x[3] > dens).length, n = M.barrios.length;
      const link = SITE + "/?barrio=" + encodeURIComponent(b[0]) + "#barrio", text = t("sh_text", { b: b[0], r: rank, n }) + " " + link;
      const cv = await window.MCShare.barrio({
        name: b[0], district: b[1], pop: t("b_sub", { d: "", p: nf(b[2]) }).replace(/^ · /, ""), rings: b[5], pts: st.map(s => [s[1], s[0]]), stations: b[4], dens, lane, acc: accBy.get(b[0]), verdict: t("v_none").replace(/<[^>]+>/g, ""),
        url: SITE.replace(/^https?:\/\//, ""), nf, n1,
        t: { kicker: t("sh_kicker"), rank: t("sh_rank", { r: rank, n }), st: t("sh_st"), dens: t("sh_dens"), lane: t("sh_lane"), acc: t("sh_acc"), foot: t("sh_foot") },
      });
      const bl = await window.MCShare.blob(cv), slug = b[0].normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      const file = new File([bl], `madrid-en-bici-${slug}.png`, { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        try { await navigator.share({ files: [file], text }); return; } catch (e) { if (e.name === "AbortError") return; }
      }
      const a = el("a"); a.href = URL.createObjectURL(bl); a.download = file.name; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      try { await navigator.clipboard.writeText(text); } catch (e) {}
      note.textContent = t("sh_saved");
    } catch (e) { console.error("share", e); note.textContent = t("sh_err"); }
  }

  // ---------- three headlines and the register of figures (data.js "figures", built by pipeline/figures.py; the same list is docs/CIFRAS.md) ----------
  const REPO = "https://github.com/jaimeoliver1/madrid-en-bici/";
  function headlines() {
    const box = document.getElementById("headlines"); if (!box) return; box.replaceChildren();
    for (const f of M.figures.filter(x => x.headline)) {
      const a = el("a", "hl-how", t("hl_how")); a.href = "#cifra-" + f.id;
      const d = el("article", "tile hl"); d.append(el("div", "q", t("hl_" + f.id)), el("div", "v", (f.id === "cobertura" ? "" : "+") + pct(f.value)), el("p", "u", f[L]), a);
      box.append(d);
    }
  }
  function cifras() {
    const box = document.getElementById("cifras"); if (!box) return; box.replaceChildren();
    const link = (txt, href) => { const a = el("a", null, txt); a.href = href; a.target = "_blank"; a.rel = "noopener"; return a; };
    const row = (k, ...nodes) => { const d = el("div", "fg-row"); d.append(el("b", null, t(k)), ...nodes); return d; };
    const list = els => { const s = el("span"); els.forEach((e, i) => { if (i) s.append("; "); s.append(e); }); return s; };
    for (const f of M.figures) {
      const d = el("details", "fg"); d.id = "cifra-" + f.id;
      const sm = el("summary"); sm.append(el("span", null, f[L])); d.append(sm);
      d.append(row("fg_calc", el("span", null, f["calc_" + L])), row("fg_files", f.files.length ? list(f.files.map(p => link(p, REPO + "blob/main/" + p))) : el("span", null, "–")),
        row("fg_script", el("span", null, f.script)), row("fg_src", list(f.upstream.map(([n, u]) => link(n, u)))));
      if (f["caveat_" + L]) d.append(row("fg_caveat", el("span", null, f["caveat_" + L])));
      box.append(d);
    }
    const foot = el("p", "small"); foot.append(link(t("fg_all"), REPO + "blob/main/docs/CIFRAS.md"), " · ", link(t("fg_err"), REPO + "issues/new?template=dato-incorrecto.yml"));
    box.append(foot);
  }
  function openFigure() { const e = location.hash.startsWith("#cifra-") ? document.getElementById(decodeURIComponent(location.hash.slice(1))) : null; if (e && e.tagName === "DETAILS") e.open = true; }
  window.addEventListener("hashchange", openFigure);

  // ---------- 0 · report card ----------
  function scorecard() {
    const box = document.getElementById("score"); box.replaceChildren();
    const bar = M.barrios, P = d3.sum(bar, b => b[2]);
    const covDensity = d3.sum(bar, b => b[2] * (b[4] / b[3])) / P;
    const accY = Object.fromEntries(M.acc_year.map(r => [r[0], r[1]]));
    const y1 = M.acc_year.filter(r => r[3] === 12).at(-1)[0], y0 = y1 - 2;
    const accUp = (accY[y1] / accY[y0] - 1) * 100;
    const R = M.routes;
    const tiles = [
      { q: t("t_use_q"), v: n1(K.trips_per_bike_day), u: t("t_use_u"), g: K.trips_per_bike_day >= 4 ? "good" : "mid", meter: { max: 10, tgt: BENCH.usesPerBike, me: K.trips_per_bike_day } },
      { q: t("t_cov_q"), v: n1(covDensity), u: t("t_cov_u"), g: covDensity >= 10 ? "good" : covDensity >= 5 ? "mid" : "bad", meter: { max: 20, tgt: BENCH.stationsKm2, me: covDensity } },
      { q: t("t_fleet_q"), v: n1(K.bikes_per_1000), u: t("t_fleet_u"), g: K.bikes_per_1000 >= 10 ? "good" : K.bikes_per_1000 >= 5 ? "mid" : "bad", meter: { max: 30, tgt: BENCH.bikesPer1000, me: K.bikes_per_1000 } },
      { q: t("t_modal_q"), v: pct(0.5), u: t("t_modal_u"), g: "bad", modal: true },
      R ? { q: t("t_route_q"), v: pct(R.share_excl), u: t("t_route_u"), g: R.share_excl >= 60 ? "good" : R.share_excl >= 30 ? "mid" : "bad", meter: { max: 100, me: R.share_excl, unit: "%" } }
        : { q: t("t_route_q"), v: pct(K.stations_near_excl_pct), u: t("t_route_u2"), g: "bad", meter: { max: 100, me: K.stations_near_excl_pct, unit: "%" } },
      { q: t("t_safe_q"), v: nf(accY[y1]), u: t("t_safe_u", { p: pct(accUp), y1, y0 }), g: "mid", spark: M.acc_year.filter(r => r[3] === 12).map(r => [r[0], r[1]]) },
    ];
    for (const tl of tiles) {
      const d = el("div", "tile");
      d.append(el("div", "q", tl.q), el("span", `grade g-${tl.g}`, t(tl.g)), el("div", "v", tl.v), el("div", "u", tl.u));
      if (tl.meter) {
        const m = el("div", "meter");
        if (tl.meter.tgt) { const g = el("i", "tgt"); g.style.left = (tl.meter.tgt[0] / tl.meter.max * 100) + "%"; g.style.width = ((Math.min(tl.meter.tgt[1], tl.meter.max) - tl.meter.tgt[0]) / tl.meter.max * 100) + "%"; m.append(g); }
        const me = el("i", "me"); me.style.left = `calc(${Math.min(100, tl.meter.me / tl.meter.max * 100)}% - 2px)`; m.append(me);
        const lab = el("div", "meter-l"); lab.append(el("span", null, "0"), el("span", null, tl.meter.tgt ? `${t("target")} ${tl.meter.tgt[0]}–${tl.meter.tgt[1]}${tl.meter.unit || ""}` : ""), el("span", null, String(tl.meter.max) + (tl.meter.unit || "")));
        d.append(m, lab);
      }
      if (tl.modal) {
        const c = el("div", "chart"); d.append(c);
        requestAnimationFrame(() => hbars(c, BENCH.modal.map(([n, v]) => ({ label: n, value: v, text: pct(v), color: n === "Madrid" ? css("--brick") : css("--lane") })), { rh: 22, mr: 44 }));
      }
      if (tl.spark) {
        const c = el("div", "chart"); d.append(c);
        requestAnimationFrame(() => vbars(c, tl.spark.map(([y, v]) => ({ label: String(y).slice(2), value: v, color: y >= 2024 ? css("--brick") : css("--muted"), title: String(y), lines: [`${nf(v)} ${t("accidents")}`] })), { h: 90, labelW: 20, allLabels: true }));
      }
      box.append(d);
    }
  }

  // ---------- 1 · BiciMAD ----------
  function bicimad() {
    const box = document.getElementById("bicimad-nums"); box.replaceChildren();
    const add = (v, l, n, f) => { const d = el("div", "bign"); const s = el("span", "v", v); if (n != null) { s.dataset.count = n; s.dataset.fmt = f; } d.append(s, el("span", "l", l)); box.append(d); };
    add(big(K.trips_last12), t("n_trips"), K.trips_last12, "big");
    add(nf(K.users_last), t("n_users", { m: fmonth(K.users_last_month) }), K.users_last, "nf");
    add(nf(K.record_day[1]), t("n_record", { d: fdate(K.record_day[0]) }), K.record_day[1], "nf");
    add(nf(K.fleet), t("n_ebike"), K.fleet, "nf");
    vbars(document.getElementById("ch-monthly"), M.monthly.map(([m, , avg]) => ({ label: m.slice(5) === "01" ? m.slice(0, 4) : "", value: avg, color: m.slice(5) === "09" ? css("--lane") : css("--sky"), title: fmonth(m), lines: [`${nf(avg)} ${t("trips_day")}`] })), { h: 240, labelW: 4, allLabels: true, fmt: v => big(v) });
    const box2 = document.getElementById("ch-hourly"), h = 240, { svg, W } = svgIn(box2, h);
    const all = [...M.hourly.weekday, ...M.hourly.weekend], y = d3.scaleLinear([0, d3.max(all)], [h - 26, 14]).nice(), ml = 36;
    const x = d3.scaleLinear([0, 23], [ml, W - 70]);
    y.ticks(4).forEach(v => { svg.append("line").attr("x1", ml).attr("x2", W - 70).attr("y1", y(v)).attr("y2", y(v)).attr("stroke", css("--line")); svg.append("text").attr("x", ml - 6).attr("y", y(v)).attr("dy", ".32em").attr("text-anchor", "end").text(nf(v)); });
    [0, 6, 12, 18, 23].forEach(v => svg.append("text").attr("x", x(v)).attr("y", h - 8).attr("text-anchor", "middle").text(v + "h"));
    const ln = d3.line().x((v, i) => x(i)).y(v => y(v));
    [[M.hourly.weekday, css("--sky"), t("weekday")], [M.hourly.weekend, css("--muted"), t("weekend")]].forEach(([s, c, name]) => {
      svg.append("path").attr("data-anim", "draw").attr("d", ln(s)).attr("fill", "none").attr("stroke", c).attr("stroke-width", 3).attr("stroke-linejoin", "round").attr("stroke-linecap", "round");
      svg.append("text").attr("class", "lbl").attr("x", x(23) + 6).attr("y", y(s[23])).attr("dy", ".32em").text(name);
    });
    const pk = M.hourly.weekday.indexOf(d3.max(M.hourly.weekday));
    svg.append("circle").attr("cx", x(pk)).attr("cy", y(M.hourly.weekday[pk])).attr("r", 5).attr("fill", css("--sky"));
    const tp = tip(box2);
    svg.append("rect").attr("x", ml).attr("width", W - 70 - ml).attr("height", h).attr("fill", "transparent").on("pointermove", ev => { const [a] = d3.pointer(ev); const i = Math.round(x.invert(a)); if (i < 0 || i > 23) return; const [px, py] = d3.pointer(ev, box2); tp.show(px, py, `${i}:00–${i}:59`, [`${t("weekday")}: ${nf(M.hourly.weekday[i])}`, `${t("weekend")}: ${nf(M.hourly.weekend[i])}`]); }).on("pointerleave", () => tp.hide());
  }

  // ---------- 2 · coverage ----------
  function coverage() {
    const box = document.getElementById("ch-barrios"), { g, F } = mapBase(box, 560);
    const ramp = d3.scaleThreshold([0.01, 1, 4, 10], [css("--grey-map"), css("--lane-soft"), d3.interpolateRgb(css("--lane-soft"), css("--lane"))(0.45), d3.interpolateRgb(css("--lane-soft"), css("--lane"))(0.75), css("--lane")]);
    const tp = tip(box);
    g.selectAll("path").data(M.barrios).join("path").attr("class", "bar").attr("d", b => ringsPath(F, b[5])).attr("fill", b => ramp(b[4] / b[3])).attr("stroke", css("--card")).attr("stroke-width", 0.8)
      .style("cursor", "pointer").on("click", (ev, b) => pickBarrio(b[0]))
      .on("pointermove", (ev, b) => { const [a, c] = d3.pointer(ev, box); tp.show(a, c, `${b[0]} (${b[1]})`, [`${b[4]} ${t("stations")} · ${n1(b[4] / b[3])} ${t("per_km2")}`, `${nf(b[2])} ${t("people")}`]); }).on("pointerleave", () => tp.hide());
    context(g, F, { faint: true });
    g.append("path").attr("class", "sel").attr("fill", "none").attr("stroke", css("--ink")).attr("stroke-width", 2.5).attr("stroke-linejoin", "round").style("pointer-events", "none");
    places(g, F); covMap = { g, F };
    const lg = document.getElementById("lg-barrios"); lg.replaceChildren();
    [[0, t("cov_none")], [0.5, t("cov_low")], [5, t("cov_mid")], [12, t("cov_ok")]].forEach(([v, l]) => { const s = el("span"); const i = el("i", "sw"); i.style.background = ramp(v); i.style.height = "10px"; s.append(i, document.createTextNode(l)); lg.append(s); });
    const P = d3.sum(M.barrios, b => b[2]), share = f => d3.sum(M.barrios.filter(f), b => b[2]) / P * 100;
    const rows = [
      { label: t("cov_none"), value: share(b => b[4] === 0), color: ramp(0) },
      { label: t("cov_low"), value: share(b => b[4] > 0 && b[4] / b[3] < 4), color: ramp(0.5) },
      { label: t("cov_mid"), value: share(b => b[4] / b[3] >= 4 && b[4] / b[3] < 10), color: ramp(5) },
      { label: t("cov_ok"), value: share(b => b[4] / b[3] >= 10), color: ramp(12) },
    ].map(r => ({ ...r, text: pct(r.value) }));
    hbars(document.getElementById("ch-coverage"), rows, { domain: [0, 100], mr: 56 });
    const ds = M.districts.map(d => ({ label: d.name, value: d.docks / d.pop * 1000, pop: d.pop })).sort((a, b) => b.value - a.value);
    hbars(document.getElementById("ch-districts"), ds.map(d => ({ label: d.label, value: d.value, text: n1(d.value), color: d.value < 7 ? css("--brick") : css("--sky"), title: d.label, lines: [`${n1(d.value)} ${t("docks_1000")}`, `${nf(d.pop)} ${t("people")}`] })), { rh: 22, mr: 40 });
  }

  // ---------- 3 · hills ----------
  function hills() {
    const rows = M.elev_bands_2023.slice().reverse().map(([lo, hi, v]) => ({ label: lo === 0 ? `< 600 ${t("m")}` : hi > 800 ? `> 680 ${t("m")}` : `${lo}–${hi} ${t("m")}`, value: v, color: v >= 0 ? css("--lane") : css("--brick"), text: (v > 0 ? "+" : "") + n1(v), title: `${lo}–${hi} m`, lines: [`${v > 0 ? t("gains") : t("loses")} ${n1(Math.abs(v))} ${t("bikes_day")}`] }));
    hbars(document.getElementById("ch-slope"), rows, { zero: true, rh: 40, mr: 50 });
    const box = document.getElementById("ch-empty"), { g, F } = mapBase(box, 520);
    g.selectAll("path").data(M.barrios).join("path").attr("d", b => ringsPath(F, b[5])).attr("fill", css("--grey-map")).attr("stroke", css("--card")).attr("stroke-width", 0.8);
    context(g, F);
    const st = M.stations.slice().sort((a, b) => (a[2] === 0) - (b[2] === 0));
    const tp = tip(box);
    g.selectAll("circle").data(st).join("circle").attr("cx", s => F.P(s[1], s[0])[0]).attr("cy", s => F.P(s[1], s[0])[1]).attr("r", s => s[2] === 0 ? 4.6 : 2.6)
      .attr("fill", s => s[2] === 0 ? css("--bad") : css("--sky")).attr("fill-opacity", s => s[2] === 0 ? 1 : 0.55).attr("stroke", css("--card")).attr("stroke-width", s => s[2] === 0 ? 1 : 0)
      .on("pointermove", (ev, s) => { const [a, c] = d3.pointer(ev, box); tp.show(a, c, `${s[2]} ${L === "es" ? "bicis" : "bikes"} · ${s[3]} ${L === "es" ? "anclajes libres" : "free docks"}`, [`${s[4]} m`]); }).on("pointerleave", () => tp.hide());
    g.selectAll("circle.pulse").data(st.filter(s => s[2] === 0)).join("circle").attr("class", "pulse").attr("cx", s => F.P(s[1], s[0])[0]).attr("cy", s => F.P(s[1], s[0])[1]).attr("r", 4.6)
      .attr("fill", "none").attr("stroke", css("--bad")).attr("stroke-width", 1.5).style("animation-delay", (s, i) => (i % 12) * 0.2 + "s").style("pointer-events", "none");
    places(g, F);
    const hi = M.elev_live[M.elev_live.length - 1], lo = M.elev_live[0], tot = d3.sum(M.elev_live, r => r[4]);
    document.getElementById("cuestas-callout").innerHTML = t("cuestas_callout", { e: hi[4], t: tot, ho: n1(hi[3]), lo: n1(lo[3]) });
  }

  // ---------- 4 · lanes ----------
  function lanes() {
    const box0 = document.getElementById("lane-nums"); box0.replaceChildren();
    [["x", "ln_x"], ["v", "ln_v"], ["s", "ln_s"]].forEach(([k, l]) => { const d = el("div", "bign"); const v = el("span", "v", nf(M.lane_km[k] || 0)); v.dataset.count = M.lane_km[k] || 0; v.dataset.fmt = "nf"; d.append(v, el("span", "l", t(l))); box0.append(d); });
    const C = { x: css("--lane"), v: d3.interpolateRgb(css("--sky"), css("--paper"))(0.5), p: css("--mid"), s: css("--muted") };
    const box = document.getElementById("ch-lanes"), { g, F } = mapBase(box, 600);
    g.selectAll("path.b").data(M.barrios).join("path").attr("d", b => ringsPath(F, b[5])).attr("fill", css("--grey-map")).attr("stroke", css("--card")).attr("stroke-width", 0.8);
    context(g, F, { roads: false });
    const order = { s: 0, p: 1, v: 2, x: 3 };
    g.selectAll("path.l").data(M.lanes.slice().sort((a, b) => order[a[0]] - order[b[0]])).join("path").attr("d", r => F.path(r[1])).attr("fill", "none").attr("stroke", r => C[r[0]]).attr("stroke-width", r => r[0] === "s" ? 1.3 : 2.4).attr("stroke-linecap", "round").attr("stroke-opacity", r => r[0] === "s" ? 0.7 : 1);
    g.selectAll("circle").data(M.stations).join("circle").attr("cx", s => F.P(s[1], s[0])[0]).attr("cy", s => F.P(s[1], s[0])[1]).attr("r", 1.8).attr("fill", css("--ink")).attr("fill-opacity", 0.7);
    places(g, F);
    const lg = document.getElementById("lg-lanes"); lg.replaceChildren();
    [["x", "lane_x"], ["v", "lane_v"], ["p", "lane_p"], ["s", "lane_s"]].forEach(([k, l]) => { const s = el("span"); const i = el("i", "sw"); i.style.background = C[k]; s.append(i, document.createTextNode(t(l))); lg.append(s); });
    { const s = el("span"); const i = el("i", "dot"); i.style.background = css("--ink"); s.append(i, document.createTextNode(t("lane_st"))); lg.append(s); }
    const rb = document.getElementById("ch-routes"), rs = document.getElementById("ch-routeshare");
    if (!M.routes) { rb.replaceChildren(el("p", "muted", t("routes_pending"))); rs.replaceChildren(); return; }
    const { g: g2, F: F2 } = mapBase(rb, 460);
    g2.selectAll("path.b").data(M.barrios).join("path").attr("d", b => ringsPath(F2, b[5])).attr("fill", css("--grey-map")).attr("stroke", css("--card")).attr("stroke-width", 0.8);
    context(g2, F2);
    const col = d3.scaleLinear([0, 50, 100], [css("--brick"), css("--mid"), css("--lane")]);
    const wmax = d3.max(M.routes.paths, p => p[0]);
    g2.selectAll("path.r").data(M.routes.paths.slice().sort((a, b) => a[0] - b[0])).join("path").attr("d", p => F2.path(p[2])).attr("fill", "none")
      .attr("stroke", p => col(p[1])).attr("stroke-width", p => 1 + 4 * p[0] / wmax).attr("stroke-opacity", 0.8).attr("stroke-linecap", "round");
    places(g2, F2);
    const labels = L === "es" ? ["Menos del 10 %", "10–25 %", "25–50 %", "50–75 %", "Más del 75 %"] : ["Under 10%", "10–25%", "25–50%", "50–75%", "Over 75%"];
    const tot = d3.sum(M.routes.hist);
    rs.replaceChildren(el("p", "small muted", t("route_share_h")));
    const c = el("div", "chart"); rs.append(c);
    hbars(c, M.routes.hist.map((v, i) => ({ label: labels[i], value: v / tot * 100, text: pct(v / tot * 100), color: col([5, 17, 37, 62, 90][i]) })), { domain: [0, 100], rh: 26, mr: 56 });
  }

  // ---------- 5 · safety ----------
  function safety() {
    const at = document.getElementById("acc-total"); if (at) at.textContent = nf(M.acc_points.length);
    const box = document.getElementById("ch-accmap"), { g, F } = mapBase(box, 640);
    g.selectAll("path.b").data(M.barrios).join("path").attr("d", b => ringsPath(F, b[5])).attr("fill", css("--grey-map")).attr("stroke", css("--card")).attr("stroke-width", 0.8);
    context(g, F);
    const pts = M.acc_points.slice().sort((a, b) => a[2] - b[2]);
    g.selectAll("circle.a").data(pts).join("circle").attr("cx", p => F.P(p[1], p[0])[0]).attr("cy", p => F.P(p[1], p[0])[1]).attr("r", p => p[2] ? 3.2 : 1.5)
      .attr("fill", p => p[2] ? css("--bad") : css("--brick")).attr("fill-opacity", p => p[2] ? 0.95 : 0.35);
    const hs = M.hotspots.slice(0, 5);
    g.selectAll("circle.hp").data(hs).join("circle").attr("class", "pulse").attr("cx", h => F.P(h[3], h[2])[0]).attr("cy", h => F.P(h[3], h[2])[1]).attr("r", 8).attr("fill", "none").attr("stroke", css("--bad")).attr("stroke-width", 2).style("animation-delay", (h, i) => i * 0.35 + "s").style("pointer-events", "none");
    g.selectAll("circle.h").data(hs).join("circle").attr("cx", h => F.P(h[3], h[2])[0]).attr("cy", h => F.P(h[3], h[2])[1]).attr("r", 15).attr("fill", "none").attr("stroke", css("--ink")).attr("stroke-width", 2);
    g.selectAll("text.h").data(hs).join("text").attr("class", "lbl").attr("x", h => F.P(h[3], h[2])[0] + 18).attr("y", h => F.P(h[3], h[2])[1] + 4).text((h, i) => i + 1);
    places(g, F);
    const yrs = M.acc_year;
    vbars(document.getElementById("ch-accyear"), yrs.map(r => ({ label: String(r[0]), value: r[1], color: r[3] < 12 ? css("--muted") : r[0] >= 2024 ? css("--brick") : css("--sky"), title: String(r[0]) + (r[3] < 12 ? ` (${r[3]} ${L === "es" ? "meses" : "months"})` : ""), lines: [`${nf(r[1])} ${t("accidents")}`, `${pct(r[2])} ${t("ebike_share")}`] })), { h: 200, allLabels: true, labelW: 30, valueLabels: r => nf(r.value) });
    hbars(document.getElementById("ch-hotspots"), M.hotspots.slice(0, 5).map((h, i) => ({ label: `${i + 1}. ${h[0].replace(/^(Call|Calle|Paseo|Plaza|Gta|Avda|Custa|Ronda)\.?\s*/i, "")}`.slice(0, 34), value: h[1], text: `${h[1]}`, color: css("--brick") })), { rh: 28, mr: 30 });
  }

  // ---------- 6 · weather & counters ----------
  function weather() {
    vbars(document.getElementById("ch-rain"), M.rain.map(([k, n, v]) => ({ label: t("rain_" + k), value: v, color: v < 95 ? css("--brick") : css("--sky"), title: t("rain_" + k), lines: [`${n1(v)} % ${t("normal")}`, `${n} ${t("days")}`] })), { h: 200, max: 110, ref: 100, allLabels: true, labelW: 60, valueLabels: r => nf(Math.round(r.value)) });
    vbars(document.getElementById("ch-heat"), M.heat.filter(r => r[2] > 0).map(([lo, hi, n, v]) => ({ label: lo < 0 ? "<10°" : hi > 40 ? "35°+" : `${lo}–${hi}°`, value: v, color: css("--sky"), title: `${lo}–${hi} °C`, lines: [`${n1(v)} % ${t("normal")}`, `${n} ${t("days")}`] })), { h: 170, max: 110, ref: 100, allLabels: true, labelW: 40, valueLabels: r => nf(Math.round(r.value)) });
    const h1 = el("p", "small muted", t("rain_t")); document.getElementById("ch-rain").prepend(h1);
    const h2 = el("p", "small muted", t("heat_t")); document.getElementById("ch-heat").prepend(h2);
    hbars(document.getElementById("ch-counters"), M.counters.slice(0, 8).map(c => ({ label: c[0].slice(0, 30), value: c[1], text: nf(c[1]), color: css("--lane") })), { rh: 34, mr: 50 });
  }

  // ---------- 7 · fixes ----------
  function fixes() {
    const R = M.routes, es = L === "es";
    const bar = M.barrios, P = d3.sum(bar, b => b[2]), cov10 = d3.sum(bar.filter(b => b[4] / b[3] >= 10), b => b[2]) / P * 100;
    const hi = M.elev_live[M.elev_live.length - 1], totEmpty = d3.sum(M.elev_live, r => r[4]);
    const F = [
      { lever: "lever_lanes", h: es ? "Unir los carriles protegidos en una red continua" : "Join protected lanes into one continuous network",
        p: es ? "La gente se anima cuando puede ir de casa al trabajo sin compartir carril con coches. Hay que priorizar los ejes que ya usan más ciclistas." : "People start riding when they can get from home to work without sharing a lane with cars. Start with the routes cyclists already use most.",
        now: R ? `${pct(R.share_excl)} ${es ? "del recorrido de los viajes va protegido" : "of the distance ridden is protected"}` : `${pct(K.stations_near_excl_pct)} ${es ? "de estaciones junto a carril separado" : "of stations next to a separated lane"}`,
        goal: es ? "Rutas de bajo estrés entre todos los barrios" : "Low-stress routes between all neighbourhoods",
        src: "Mekuria, Furth & Nixon (2012); Buehler & Dill (2016); Plan Director de Movilidad Ciclista (2008): 575 km" },
      { lever: "lever_lanes", h: es ? "Arreglar primero los cruces más peligrosos" : "Fix the most dangerous junctions first",
        p: es ? "Atocha, Puente de Segovia y Gran Vía con San Bernardo acumulan decenas de accidentes. Cruces protegidos y semáforos para bicis reducen los choques." : "Atocha, Puente de Segovia and Gran Vía at San Bernardo each have dozens of crashes. Protected junctions and bike signals cut collisions.",
        now: (r => `${nf(r[1])} ${es ? "accidentes en" : "accidents in"} ${r[0]}`)(M.acc_year.filter(r => r[3] === 12).at(-1)),
        goal: es ? "Bajar los accidentes aunque suba el uso" : "Fewer crashes even as riding grows",
        src: "Marshall & Ferenchak (2019): −44 % muertes en ciudades con carriles protegidos" },
      { lever: "lever_bicimad", h: es ? "Más estaciones, más juntas, fuera del centro" : "More stations, closer together, beyond the centre",
        p: es ? "Una estación cada 300 m. Hoy solo el centro llega; en el resto de barrios hay que andar demasiado." : "One station every 300 m. Today only the centre gets there; elsewhere the walk is too long.",
        now: `${pct(cov10)} ${es ? "de vecinos con la densidad recomendada" : "of residents at the recommended density"}`,
        goal: es ? "10–16 estaciones por km²" : "10–16 stations per km²", src: "ITDP, Bikeshare Planning Guide" },
      { lever: "lever_bicimad", h: es ? "Más bicis en la calle" : "More bikes on the street",
        p: es ? "Con tan pocas bicis por vecino, muchas estaciones se quedan vacías justo cuando se necesitan." : "With so few bikes per resident, many stations run empty right when people need them.",
        now: `${n1(K.bikes_per_1000)} ${es ? "bicis por 1.000 vecinos" : "bikes per 1,000 residents"}`, goal: es ? "10 a 30 (Barcelona: 4,7)" : "10 to 30 (Barcelona: 4.7)", src: "ITDP, Bikeshare Planning Guide" },
      { lever: "lever_bicimad", h: es ? "Premiar a quien sube la cuesta" : "Reward riders who go uphill",
        p: es ? "París premió con minutos extra a quien dejaba la bici en estaciones altas. Unido a un reequilibrio más inteligente, ayudaría a que las estaciones altas no se vacíen." : "Paris gave extra minutes to riders who docked at hilltop stations. Together with smarter rebalancing, it would stop high stations running dry.",
        now: `${hi[4]} ${es ? "de" : "of"} ${totEmpty} ${es ? "estaciones vacías estaban por encima de 680 m" : "empty stations were above 680 m"}`,
        goal: es ? "Ninguna estación vacía en hora punta" : "No empty stations at rush hour", src: es ? "Datos GBFS de BiciMAD; altitud EU-DEM" : "BiciMAD GBFS data; EU-DEM elevation" },
      { lever: "lever_both", h: es ? "Medir y publicar, con objetivos" : "Measure, publish and set targets",
        p: es ? "Los viajes de BiciMAD uno a uno no se publican desde 2023 y los contadores tienen huecos. Sin datos no se puede saber qué funciona." : "Trip-by-trip BiciMAD data hasn't been published since 2023 and the counters have gaps. Without data no one can tell what works.",
        now: es ? "0,5 % de los viajes en bici" : "0.5% of trips by bike", goal: es ? "Un objetivo anual, como Barcelona (3,8 %) o París (11 %)" : "A yearly target, like Barcelona (3.8%) or Paris (11%)",
        src: "EDM 2018 (CRTM); Ayuntamiento de Barcelona; Ville de Paris" },
    ];
    const box = document.getElementById("fixes"); box.replaceChildren();
    F.forEach((f, i) => {
      const d = el("div", "fix");
      const now = el("div", "now"); now.append(el("span", "muted", t("now")), el("b", null, f.now));
      const goal = el("div", "now"); goal.append(el("span", "muted", t("goal")), el("b", null, f.goal));
      d.append(el("span", "lever", t(f.lever)), el("h3", null, f.h), el("p", null, f.p), now, goal, el("div", "src", f.src));
      box.append(d);
    });
  }

  // ---------- method & sources ----------
  function method() {
    const es = L === "es";
    const ps = es ? [
      `Viajes diarios y usuarios activos: EMT Madrid, de ${fmonth(K.daily_first.slice(0, 7))} a ${fmonth(K.daily_last.slice(0, 7))}. Los patrones por hora y por estación vienen de los últimos viajes publicados uno a uno (enero y febrero de 2023).`,
      `Viajes por bici y día: media de los últimos 12 meses dividida entre las ${nf(K.fleet)} bicis que declara el sistema en tiempo real (GBFS). Cobertura: estaciones en servicio dentro de cada barrio, con la población del padrón a 1 de enero de 2026. ${K.stations_outside} estaciones están en Pozuelo de Alarcón y no cuentan.`,
      `Cuestas: altitud de cada estación con el modelo EU-DEM de 25 m. Carriles: capa oficial de infraestructura ciclista; "separado" incluye carril bici, acera bici, pista y senda ciclable, y el Anillo Verde se muestra aparte.`,
      `Rutas: calculamos la ruta ciclista más probable de los ${nf(M.routes ? M.routes.trips : 0)} viajes de estación a estación de enero y febrero de 2023 sobre las calles de OpenStreetMap (prefiriendo carriles bici y calles tranquilas y respetando sentidos únicos), y medimos qué parte pasa a menos de 15 m de un carril separado. Accidentes: registros de la Policía Municipal con implicación de bicicletas. Tiempo: estación de El Retiro (NOAA GHCN-Daily).`,
    ] : [
      `Daily trips and active users: EMT Madrid, ${fmonth(K.daily_first.slice(0, 7))} to ${fmonth(K.daily_last.slice(0, 7))}. Hourly and station patterns come from the last trip-by-trip release (January–February 2023).`,
      `Trips per bike per day: last-12-month average divided by the ${nf(K.fleet)} bikes the live feed (GBFS) reports. Coverage: stations in service inside each neighbourhood, with population on 1 January 2026. ${K.stations_outside} stations are in Pozuelo de Alarcón and are not counted.`,
      `Hills: each station's elevation from the EU-DEM 25 m model. Lanes: the city's official cycling layer; "separated" includes bike lanes, bike pavements, tracks and paths, with the Anillo Verde ring shown separately.`,
      `Routes: we worked out the most likely bike route of all ${nf(M.routes ? M.routes.trips : 0)} station-to-station trips of January and February 2023 on OpenStreetMap streets (preferring bike lanes and quiet streets, respecting one-way streets), and measured how much runs within 15 m of a separated lane. Accidents: municipal police records involving bicycles. Weather: El Retiro station (NOAA GHCN-Daily).`,
    ];
    const m = document.getElementById("method"); m.replaceChildren(...ps.map(p => el("p", null, p)));
    const src = [
      ["EMT Madrid · datos abiertos (BiciMAD)", "https://datos.emtmadrid.es"],
      ["Ayuntamiento de Madrid · Portal de datos abiertos (accidentes, infraestructura ciclista, aforos, aparcabicis, padrón, límites)", "https://datos.madrid.es"],
      ["ITDP · The Bikeshare Planning Guide", "https://bikeshare.itdp.org/guide/goal-setting-initial-planning/examine-feasibility-choose-a-system-type/"],
      ["Mekuria, Furth & Nixon (2012) · Low-Stress Bicycling and Network Connectivity", "https://transweb.sjsu.edu/research/Low-Stress-Bicycling-and-Network-Connectivity"],
      ["Marshall & Ferenchak (2019) · Journal of Transport & Health", "https://doi.org/10.1016/j.jth.2019.03.004"],
      ["Buehler & Dill (2016) · Transport Reviews", "https://ideas.repec.org/a/taf/transr/v36y2016i1p9-27.html"],
      ["CRTM · Encuesta Domiciliaria de Movilidad 2018", "https://crtm.es/media/ml2ertro/jornada_presentacion_edm2018_resultados.pdf"],
      ["Ville de Paris · le vélo surpasse la voiture (2024)", "https://www.paris.fr/pages/inedit-le-velo-surpasse-la-voiture-a-paris-et-en-petite-couronne-et-de-loin-26832"],
      ["Copenhagenize Index 2025", "https://copenhagenizeindex.eu/"],
      ["OpenStreetMap · routing.openstreetmap.de (bike)", "https://routing.openstreetmap.de"],
      ["NOAA GHCN-Daily · Madrid Retiro", "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily"],
      ["EU-DEM 25 m via OpenTopoData", "https://www.opentopodata.org/datasets/eudem/"],
    ];
    const ul = document.getElementById("sources"); ul.replaceChildren(...src.map(([n, u]) => { const li = el("li"); const a = el("a", null, n); a.href = u; a.target = "_blank"; a.rel = "noopener"; li.append(a); return li; }));
  }

  // ---------- render ----------
  function texts() {
    document.documentElement.lang = L;
    const loc_ = L === "es" ? "es-ES" : "en-GB", snapD = new Date(K.snapshot.replace(" ", "T") + ":00");
    const part = M.acc_year.filter(r => r[3] < 12).at(-1);
    const V = {
      n: nf(M.acc_points.length),
      snap: snapD.toLocaleString(loc_, { weekday: "long", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" }),
      accend: fmonth(K.acc_last.slice(0, 7)),
      dlast: fdate(K.daily_last), ctop: nf(M.counters[0][1]), refreshed: K.refreshed ? fdate(K.refreshed) : "", fleet: nf(K.fleet),
      partial: part ? (L === "es" ? `${part[0]} solo incluye enero a ${new Date(K.acc_last + "T12:00:00Z").toLocaleDateString(loc_, { month: "long" })}.` : `${part[0]} covers January to ${new Date(K.acc_last + "T12:00:00Z").toLocaleDateString(loc_, { month: "long" })} only.`) : "",
    };
    document.querySelectorAll("[data-i18n]").forEach(e => { e.textContent = t(e.dataset.i18n, V); });
    document.querySelectorAll("[data-i18n-html]").forEach(e => { e.innerHTML = t(e.dataset.i18nHtml, V); });
    freshness(V); liveShow();
    document.getElementById("lang-es").setAttribute("aria-pressed", String(L === "es"));
    document.getElementById("lang-en").setAttribute("aria-pressed", String(L === "en"));
  }
  // ---------- motion: charts build up the first time they scroll into view ----------
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches, played = new Set(), pending = new Map();
  const io = "IntersectionObserver" in window ? new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add("inview");
    const f = pending.get(e.target); if (f) { pending.delete(e.target); f(); }
    io.unobserve(e.target);
  }), { threshold: 0.2 }) : null;
  function onView(node, fn) {
    if (!io || reduce || played.has(node.id)) { node.classList?.add("inview"); return; }
    played.add(node.id); pending.set(node, fn); io.observe(node);
  }
  const FMT = { big: v => big(Math.round(v)), nf: v => nf(Math.round(v)), n1: v => n1(v), pct: v => pct(v) };
  function animate(box) {
    const ease = d3.easeCubicOut;
    d3.select(box).selectAll("rect[data-anim=v]").each(function (_, i) {
      const r = d3.select(this), y = +r.attr("y"), h = +r.attr("height"), b = +r.attr("data-base");
      r.attr("y", b).attr("height", 0).transition().delay(Math.min(i, 40) * 22).duration(750).ease(ease).attr("y", y).attr("height", h);
    });
    d3.select(box).selectAll("rect[data-anim=h]").each(function (_, i) {
      const r = d3.select(this), x = +r.attr("x"), w = +r.attr("width"), b = +r.attr("data-base");
      r.attr("x", b).attr("width", 0).transition().delay(i * 45).duration(800).ease(ease).attr("x", x).attr("width", w);
    });
    d3.select(box).selectAll("path[data-anim=draw]").each(function () {
      const L = this.getTotalLength(); d3.select(this).attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(1400).ease(d3.easeCubicInOut).attr("stroke-dashoffset", 0).on("end", function () { this.removeAttribute("stroke-dasharray"); });
    });
    box.querySelectorAll("[data-count]").forEach(n => {
      const to = +n.dataset.count, f = FMT[n.dataset.fmt] || FMT.nf, from = to * 0.15;
      d3.select(n).transition().duration(1200).ease(ease).tween("text", () => v => { n.textContent = f(from + (to - from) * v); }).on("end", () => { n.textContent = f(to); });
    });
    box.querySelectorAll(".meter .me").forEach(m => { const left = m.style.left; m.style.left = "0%"; requestAnimationFrame(() => requestAnimationFrame(() => { m.style.left = left; })); });
    const maps = box.querySelectorAll(".mapbox svg > g > g > *");
    if (maps.length) d3.selectAll(maps).style("opacity", 0).transition().delay((_, i) => Math.min(i, 400) * 2).duration(500).style("opacity", null);
  }
  function render() {
    texts();
    const parts = [headlines, cifras, scorecard, bicimad, coverage, barrio, hills, lanes, safety, weather, fixes, method];
    for (const f of parts) { try { f(); } catch (e) { console.error(f.name, e); } }
    document.querySelectorAll("main .chart[id], #score, #bicimad-nums, #lane-nums").forEach(b => onView(b, () => animate(b)));
    document.querySelectorAll(".stop").forEach(s => { if (!s.id) return; onView(s, () => {}); });
    window.MCI = { t, nf, n1, pct, big, css, el, tip, mapBase, context, places, fullButton, lang: () => L };
    window.dispatchEvent(new Event("mc-render"));
  }
  // ---------- data freshness: a chip per section and a table in the footer ----------
  const FRESH = { bicimad: "f-month", barrios: "f-month", cuestas: "f-live", carriles: "f-month", seguridad: "f-month", tiempo: "f-month" };
  function freshness(V) {
    document.querySelectorAll("[data-fresh]").forEach(sec => {
      const k = sec.dataset.fresh, h2 = sec.querySelector("h2, h3"); if (!h2) return;
      let a = sec.querySelector(".fresh"); if (!a) { a = el("a", "fresh " + FRESH[k]); a.href = "#datos"; h2.after(a); }
      a.replaceChildren(el("i"), document.createTextNode(t("fc_" + k, V)));
    });
    const rows = [["live", "f-live", "fr_u_live", "BiciMAD GBFS"], ["trips", "f-month", fdate(K.daily_last), "EMT Madrid"], ["acc", "f-month", fdate(K.acc_last), "datos.madrid.es"],
      ["city", "f-month", "fr_u_city", "datos.madrid.es"], ["wx", "f-month", fdate(K.daily_last), "NOAA GHCN-Daily"], ["2023", "f-frozen", "fr_u_2023", "EMT Madrid"], ["cnt", "f-frozen", "fr_u_cnt", "datos.madrid.es"]];
    const tab = el("table", "freshtab"), th = el("tr");
    ["fr_what", "fr_when", "fr_upto", "fr_src"].forEach(k => th.append(el("th", null, t(k))));
    const thead = el("thead"); thead.append(th); const tb = el("tbody");
    rows.forEach(([k, c, u, src]) => {
      const tr = el("tr"), when = el("td"), chip = el("span", "fresh " + c);
      chip.style.margin = "0 8px 4px 0"; chip.append(el("i"), document.createTextNode(t(c === "f-live" ? "fr_live" : c === "f-month" ? "fr_month" : "fr_frozen")));
      when.append(chip, document.createTextNode(t("fr_c_" + k)));
      tr.append(el("td", null, t("fr_r_" + k)), when, el("td", null, u.startsWith("fr_") ? t(u, V) : u), el("td", null, src)); tb.append(tr);
    });
    tab.append(thead, tb);
    const ol = el("ol", "footnotes"); ol.append(el("li", null, t("fr_fn1")));
    document.getElementById("fresh").replaceChildren(el("p", "small muted", t("fr_auto", V)), tab, ol);
  }
  // ---------- live: station availability straight from BiciMAD's public feed (open to browsers), every minute ----------
  const GBFS = "https://madrid.publicbikesystem.net/customer/gbfs/v2/en/station_status";
  const LV = { ok: false, at: null, bikes: null, empty: null, full: null, out: 0, prev: null, mapAt: 0 };
  function liveShow() {
    const box = document.getElementById("live"); if (!box) return;
    box.classList.toggle("off", !LV.ok);
    document.getElementById("lv-bikes-l").textContent = t("lv_bikes", { fleet: nf(K.fleet) });
    const set = (id, v) => { const e = document.getElementById(id); const s = v == null ? "–" : nf(v); if (e.textContent !== s) { e.textContent = s; e.classList.add("flash"); setTimeout(() => e.classList.remove("flash"), 900); } };
    if (LV.ok) { set("lv-bikes", LV.bikes); set("lv-empty", LV.empty); set("lv-full", LV.full); set("lv-out", LV.out); }
    else { set("lv-bikes", d3.sum(M.stations, s => s[2])); set("lv-empty", K.empty_now); set("lv-full", M.stations.filter(s => s[3] === 0).length); set("lv-out", null); }
    const loc_ = L === "es" ? "es-ES" : "en-GB";
    document.getElementById("live-ago").textContent = LV.ok ? t("live_ago", { t: LV.at.toLocaleTimeString(loc_, { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Madrid" }) })
      : t("live_off", { snap: new Date(K.snapshot.replace(" ", "T") + ":00").toLocaleString(loc_, { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }) });
  }
  async function live() {
    try {
      const r = await fetch(GBFS, { cache: "no-store" }); if (!r.ok) throw 0;
      const j = await r.json(), ss = j.data.stations.filter(s => s.is_installed && s.is_renting);
      const now = new Map(ss.map(s => [s.station_id, s.num_bikes_available]));
      if (LV.prev) for (const [id, b] of now) { const p = LV.prev.get(id); if (p != null && b < p) LV.out += p - b; }
      LV.prev = now; LV.ok = true; LV.at = new Date(j.last_updated * 1000);
      LV.bikes = d3.sum(ss, s => s.num_bikes_available); LV.empty = ss.filter(s => s.num_bikes_available === 0).length; LV.full = ss.filter(s => s.num_docks_available === 0).length;
      liveShow();
      // the empty-stations map and its texts follow the feed every 5 minutes
      if (Date.now() - LV.mapAt < 5 * 60 * 1000) return;
      LV.mapAt = Date.now();
      const byId = new Map(j.data.stations.map(s => [+s.station_id, s]));
      let n = 0;
      for (const s of M.stations) { const x = byId.get(s[6]); if (x) { s[2] = x.num_bikes_available; s[3] = x.num_docks_available; n++; } }
      if (!n) return;
      M.elev_live = M.elev_live.map(([lo, hi]) => {
        const rs = M.stations.filter(s => s[4] != null && s[4] >= lo && s[4] < hi), occ = rs.map(s => (s[2] + s[3]) ? s[2] / (s[2] + s[3]) : 0);
        return [lo, hi, rs.length, Math.round(d3.mean(occ) * 1000) / 10, rs.filter(s => s[2] === 0).length];
      });
      K.empty_now = M.stations.filter(s => s[2] === 0).length;
      K.snapshot = LV.at.toLocaleString("sv-SE", { timeZone: "Europe/Madrid" }).slice(0, 16);
      texts(); hills(); barrioCard();
    } catch (e) { LV.ok = false; liveShow(); /* offline or feed down: keep the last published snapshot */ }
  }
  live();
  setInterval(() => { if (!document.hidden) live(); }, 60 * 1000);
  ["es", "en"].forEach(l => document.getElementById("lang-" + l).addEventListener("click", () => { L = l; try { localStorage.setItem("mc-lang", l); } catch (e) {} render(); }));
  let w = window.innerWidth;
  window.addEventListener("resize", () => { if (Math.abs(window.innerWidth - w) > 40) { w = window.innerWidth; render(); } });
  // light by default; dark only when the visitor picks it (remembered on this device)
  const themeBtn = document.getElementById("theme");
  function themeLabel() {
    const dark = document.documentElement.dataset.theme === "dark";
    themeBtn.textContent = dark ? "☀" : "☾"; themeBtn.setAttribute("aria-pressed", String(dark));
    themeBtn.title = t(dark ? "theme_light" : "theme_dark"); themeBtn.setAttribute("aria-label", themeBtn.title);
    document.querySelector('meta[name="theme-color"]').content = css("--paper");
  }
  themeBtn.addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme !== "dark";
    if (dark) document.documentElement.dataset.theme = "dark"; else delete document.documentElement.dataset.theme;
    try { localStorage.setItem("mc-theme", dark ? "dark" : "light"); } catch (e) {}
    render();
  });
  window.addEventListener("mc-render", themeLabel);
  // ---------- two tabs: "Ir en bici" for riders, "Mejorar Madrid" for decision makers; the hash picks the tab ----------
  // charts size themselves from their box, so a tab is drawn again when it is shown, and a tip card when it is opened
  const PANES = [...document.querySelectorAll(".pane")], PARTS = { hills, bicimad, safety, weather };
  function paneFor(hash) {
    const target = hash.length > 1 ? document.getElementById(decodeURIComponent(hash.slice(1))) : null;
    return { target, pane: target ? target.closest(".pane") : PANES[0] };  // pane is null for anchors outside the tabs (footer)
  }
  function showPane(pane) {
    PANES.forEach(p => { p.hidden = p !== pane; });
    document.querySelectorAll(".tabs a").forEach(a => { if (a.dataset.pane === pane.id) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  }
  function goTo(target, pane) {
    if (target && target !== pane) target.scrollIntoView({ behavior: "instant" }); else window.scrollTo({ top: 0, behavior: "instant" });
  }
  window.addEventListener("hashchange", () => {
    const { target, pane } = paneFor(location.hash);
    if (!pane || !pane.hidden) return;  // a link within the open tab, or to the footer: the browser scrolls
    showPane(pane); render(); goTo(target, pane);
  });
  document.querySelectorAll(".tipcard details").forEach(d => d.addEventListener("toggle", () => {
    const f = PARTS[d.closest(".tipcard").dataset.part];
    if (d.open && f) { try { f(); } catch (e) { console.error(f.name, e); } }
  }));
  const first = paneFor(location.hash);
  setTimeout(openFigure, 0);
  showPane(first.pane || PANES[0]);
  render();
  if (first.target) goTo(first.target, first.pane);
})();
