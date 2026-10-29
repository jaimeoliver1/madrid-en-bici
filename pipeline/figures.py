"""The register of figures: every number the site, the press kit and the social posts quote, with how to check it.

Each figure carries its value (computed here from data/), a formula a journalist can repeat in a spreadsheet,
the file in data/ it comes from, the script that built that file, and the original publisher's page.

Usage: python3 pipeline/figures.py [data] [docs/CIFRAS.md]
  -> writes data/figures.json and docs/CIFRAS.md; build_site.py calls compute() and ships the list in site/data.js.
"""
import sys, os, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "https://github.com/jaimeoliver1/madrid-en-bici/blob/main/"
SRC = {
    "emt": ("EMT Madrid · datos abiertos BiciMAD", "https://datos.emtmadrid.es"),
    "padron": ("Ayuntamiento de Madrid · Padrón a 1 de enero (300557)", "https://datos.madrid.es/dataset/300557-0-poblacion-distrito-barrio"),
    "limites": ("Ayuntamiento de Madrid · Límites administrativos (900012)", "https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas"),
    "acc": ("Policía Municipal · Accidentes con bicicleta (300110)", "https://datos.madrid.es/dataset/300110-0-accidentes-bicicleta"),
    "infra": ("Ayuntamiento de Madrid · Infraestructura ciclista (205107)", "https://datos.madrid.es/dataset/205107-0-vias-ciclistas"),
    "gbfs": ("BiciMAD · feed en tiempo real (GBFS)", "https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json"),
    "trips23": ("EMT · Históricos de BiciMAD, viajes 2023 (900034)", "https://datos.madrid.es/dataset/900034-0-bicimad-viajes-estaciones"),
    "itdp": ("ITDP · The Bikeshare Planning Guide", "https://bikeshare.itdp.org/guide/goal-setting-initial-planning/examine-feasibility-choose-a-system-type/"),
    "edm": ("CRTM · Encuesta Domiciliaria de Movilidad 2018", "https://crtm.es/media/ml2ertro/jornada_presentacion_edm2018_resultados.pdf"),
}


def dec(v):
    """Spanish decimal comma"""
    return str(v).replace(".", ",")


def thou(n):
    """Spanish thousands dot"""
    return f"{int(n):,}".replace(",", ".")


def compute(D):
    R = lambda f: pd.read_csv(os.path.join(D, f))
    bar, dist, daily = R("madrid_barrios_bicimad.csv"), R("madrid_districts_cycling.csv"), R("bicimad_daily_trips_weather.csv")
    acc, users = R("madrid_bike_accidents_by_year.csv").set_index("year"), R("bicimad_active_users_monthly.csv")
    st = R("bicimad_station_context.csv"); st = st[st.status == "IN_SERVICE"]
    ra = R("bicimad_2023_routes_all.csv.gz")
    plan = json.load(open(os.path.join(D, "lane_network_plans.json")))
    meta = json.load(open(os.path.join(D, "refresh_meta.json")))
    daily["date"] = pd.to_datetime(daily.date)
    fleet = int(meta["fleet"]); pop = int(dist.population.sum())
    P = bar.population.sum(); ok = bar.stations_per_km2 >= 10; none = bar.stations == 0
    fs = {y: int(daily[(daily.date.dt.year == y) & daily.date.dt.month.between(2, 9)].trips.sum()) for y in (2024, 2026)}
    last12 = daily[daily.date > daily.date.max() - pd.Timedelta(days=365)]
    rec = daily.loc[daily.trips.idxmax()]
    bf = plan["bestfirst"]
    F = {}

    def add(id, value, es, en, calc_es, calc_en, files, script, upstream, caveat_es="", caveat_en="", headline=0, **extra):
        F[id] = dict(id=id, headline=headline, value=value, es=es, en=en, calc_es=calc_es, calc_en=calc_en, files=files, script=script,
                     upstream=[SRC[u] for u in upstream], caveat_es=caveat_es, caveat_en=caveat_en, **extra)

    # ---- the three headlines ----
    p_ok = round(float(bar[ok].population.sum() / P * 100), 1)
    add("cobertura", p_ok,
        f"Solo el {dec(p_ok)}% de los madrileños vive en un barrio con la densidad de estaciones de BiciMAD que recomienda la guía de la ITDP ({int(ok.sum())} de {len(bar)} barrios).",
        f"Only {p_ok}% of Madrid residents live in a barrio with the BiciMAD station density the ITDP guide recommends ({int(ok.sum())} of {len(bar)} barrios).",
        "En data/madrid_barrios_bicimad.csv: suma `population` de los barrios con `stations_per_km2` ≥ 10 y divide entre la suma de `population` de los 131 barrios.",
        "In data/madrid_barrios_bicimad.csv: sum `population` for barrios with `stations_per_km2` ≥ 10 and divide by the sum of `population` over all 131 barrios.",
        ["data/madrid_barrios_bicimad.csv"], "pipeline/historical/08_barrios.py (contorno y primera cuenta) y pipeline/refresh.py (recuento mensual)", ["gbfs", "padron", "limites", "itdp"],
        "Estaciones en servicio dentro de cada barrio (las 32 de Pozuelo no cuentan). 10 estaciones/km² es el mínimo de la guía de la ITDP (10–16): es una densidad, no una distancia medida a pie.",
        "In-service stations inside each barrio (the 32 in Pozuelo are excluded). 10 stations/km² is the low end of the ITDP guide (10–16): a density, not a measured walking distance.",
        headline=1, extra_n=int(ok.sum()), of=len(bar))
    g = round((fs[2026] / fs[2024] - 1) * 100)
    add("crecimiento", g,
        f"BiciMAD casi se ha duplicado en dos años: {dec(round(fs[2026] / 1e6, 1))} millones de viajes de febrero a septiembre de 2026, un {g}% más que en 2024 ({dec(round(fs[2024] / 1e6, 1))} millones).",
        f"BiciMAD has almost doubled in two years: {fs[2026] / 1e6:.1f} million trips from February to September 2026, {g}% more than in 2024 ({fs[2024] / 1e6:.1f} million).",
        "En data/bicimad_daily_trips_weather.csv: suma `trips` entre el 1 de febrero y el 30 de septiembre de 2026 y de 2024; divide y resta 1.",
        "In data/bicimad_daily_trips_weather.csv: sum `trips` from 1 February to 30 September of 2026 and of 2024; divide and subtract 1.",
        ["data/bicimad_daily_trips_weather.csv"], "pipeline/refresh.py (función bicimad_daily)", ["emt"],
        "El sistema también creció: más estaciones y bicis eléctricas. Son viajes, no personas.",
        "The system also grew: more stations and e-bikes. These are trips, not people.", headline=1, y0=fs[2024], y1=fs[2026])
    a0, a1 = int(acc.loc[2019, "accidents"]), int(acc.loc[2025, "accidents"]); ap = round((a1 / a0 - 1) * 100)
    add("accidentes", ap,
        f"Los accidentes con bicicleta atendidos por la Policía Municipal han subido un {ap}% desde 2019: de {a0} a {thou(a1)} al año.",
        f"Bike crashes attended by the municipal police are up {ap}% since 2019: from {a0} to {a1:,} a year.",
        "En data/madrid_bike_accidents_by_year.csv: `accidents` de 2025 entre `accidents` de 2019, menos 1.",
        "In data/madrid_bike_accidents_by_year.csv: `accidents` for 2025 divided by `accidents` for 2019, minus 1.",
        ["data/madrid_bike_accidents_by_year.csv", "data/madrid_bike_accidents.csv"], "pipeline/refresh.py (función accidents)", ["acc"],
        "Cuentan todas las bicis, no solo BiciMAD, y no hay kilómetros recorridos: no se puede calcular el riesgo por viaje. Solo constan los accidentes atendidos por la policía. 2026 está incompleto.",
        "All bikes are counted, not just BiciMAD, and there is no distance ridden: risk per trip can't be calculated. Only police-attended crashes are recorded. 2026 is incomplete.",
        headline=1, y0=a0, y1=a1)

    # ---- supporting figures ----
    add("sin_estacion", round(float(bar[none].population.sum() / P * 100), 1),
        f"{int(none.sum())} barrios no tienen ninguna estación de BiciMAD: {dec(round(float(bar[none].population.sum() / P * 100), 1))}% de la población.",
        f"{int(none.sum())} barrios have no BiciMAD station: {round(float(bar[none].population.sum() / P * 100), 1)}% of the population.",
        "En data/madrid_barrios_bicimad.csv: barrios con `stations` = 0; suma su `population` entre el total.",
        "In data/madrid_barrios_bicimad.csv: barrios with `stations` = 0; sum their `population` over the total.",
        ["data/madrid_barrios_bicimad.csv"], "pipeline/refresh.py (función barrios)", ["gbfs", "padron", "limites"])
    add("viajes_12m", int(last12.trips.sum()),
        f"{thou(last12.trips.sum())} viajes en BiciMAD en los últimos 12 meses con datos.",
        f"{int(last12.trips.sum()):,} BiciMAD trips in the last 12 months of data.",
        "En data/bicimad_daily_trips_weather.csv: suma `trips` de los 365 días anteriores a la última fecha.",
        "In data/bicimad_daily_trips_weather.csv: sum `trips` over the 365 days before the last date.",
        ["data/bicimad_daily_trips_weather.csv"], "pipeline/refresh.py (función bicimad_daily)", ["emt"])
    add("record", int(rec.trips),
        f"Récord de viajes en un día: {thou(rec.trips)} el {rec.date:%Y-%m-%d}.",
        f"Record day: {int(rec.trips):,} trips on {rec.date:%Y-%m-%d}.",
        "En data/bicimad_daily_trips_weather.csv: el máximo de `trips`.", "In data/bicimad_daily_trips_weather.csv: the maximum of `trips`.",
        ["data/bicimad_daily_trips_weather.csv"], "pipeline/refresh.py (función bicimad_daily)", ["emt"])
    add("usuarios", int(users.active_users.iloc[-1]),
        f"{thou(users.active_users.iloc[-1])} usuarios activos en {users.month.iloc[-1]}.",
        f"{int(users.active_users.iloc[-1]):,} active users in {users.month.iloc[-1]}.",
        "En data/bicimad_active_users_monthly.csv: `active_users` del último mes.", "In data/bicimad_active_users_monthly.csv: `active_users` for the last month.",
        ["data/bicimad_active_users_monthly.csv"], "pipeline/refresh.py (función bicimad_users)", ["emt"])
    tpb = round(float(last12.trips.mean() / fleet), 1)
    add("viajes_por_bici", tpb,
        f"Cada bici de BiciMAD hace de media {dec(tpb)} viajes al día (la guía de la ITDP recomienda 4 a 8).",
        f"Each BiciMAD bike makes {tpb} trips a day on average (the ITDP guide recommends 4 to 8).",
        f"En data/bicimad_daily_trips_weather.csv: media diaria de `trips` de los últimos 12 meses entre {thou(fleet)} bicis (data/refresh_meta.json, `fleet`).",
        f"In data/bicimad_daily_trips_weather.csv: last-12-month daily mean of `trips` divided by {fleet:,} bikes (data/refresh_meta.json, `fleet`).",
        ["data/bicimad_daily_trips_weather.csv", "data/refresh_meta.json"], "pipeline/build_site.py", ["emt", "gbfs", "itdp"],
        "La flota viene del feed en tiempo real y no coincide con la de los informes municipales (unas 8.000).", "The fleet comes from the live feed and differs from the city's reports (about 8,000).")
    km = float(dist.exclusive_km.sum())
    add("km_carril", round(km),
        f"{round(km)} km de carril bici segregado en la ciudad, {dec(round(km / pop * 1e5, 1))} por cada 100.000 habitantes.",
        f"{round(km)} km of segregated bike lane in the city, {round(km / pop * 1e5, 1)} per 100,000 residents.",
        "En data/madrid_districts_cycling.csv: suma `exclusive_km` de los 21 distritos.", "In data/madrid_districts_cycling.csv: sum `exclusive_km` over the 21 districts.",
        ["data/madrid_districts_cycling.csv", "data/madrid_bike_infrastructure.csv"], "pipeline/refresh.py (funciones infrastructure y districts)", ["infra"],
        "La prensa cuenta unos 292 km como segregados; el Ayuntamiento, unos 426. Aquí: la capa oficial de carril exclusivo, sin ciclocalles ni Anillo Verde.",
        "The press counts about 292 km as segregated; the city, about 426. Here: the official exclusive-lane layer, without shared streets or the Anillo Verde.")
    near = round(float((st.m_to_exclusive_lane <= 50).mean() * 100))
    add("estaciones_carril", near,
        f"Solo el {near}% de las estaciones de BiciMAD tiene un carril bici segregado a menos de 50 m.",
        f"Only {near}% of BiciMAD stations have a segregated bike lane within 50 m.",
        "En data/bicimad_station_context.csv: porcentaje de estaciones `IN_SERVICE` con `m_to_exclusive_lane` ≤ 50.",
        "In data/bicimad_station_context.csv: share of `IN_SERVICE` stations with `m_to_exclusive_lane` ≤ 50.",
        ["data/bicimad_station_context.csv"], "pipeline/refresh.py (función stations)", ["gbfs", "infra"])
    sh = round(float((ra.share_exclusive * ra.trips).sum() / ra.trips.sum()), 1)
    add("recorrido_protegido", sh,
        f"Solo el {dec(sh)}% del recorrido de los viajes de BiciMAD (enero–febrero de 2023) va por carril separado del tráfico.",
        f"Only {sh}% of the distance of BiciMAD trips (January–February 2023) runs on a lane separated from traffic.",
        "En data/bicimad_2023_routes_all.csv.gz: media de `share_exclusive` ponderada por `trips`.",
        "In data/bicimad_2023_routes_all.csv.gz: mean of `share_exclusive` weighted by `trips`.",
        ["data/bicimad_2023_routes_all.csv.gz"], "pipeline/historical/11_all_routes.py (método en docs/ROUTING.md)", ["trips23", "infra"],
        "Es un modelo: la ruta más probable sobre OpenStreetMap, no trazas GPS. Usa los últimos viajes publicados (49 días de 2023).",
        "A model: the most likely route on OpenStreetMap, not GPS tracks. Uses the last published trips (49 days of 2023).")
    add("plan_carriles", round(bf["km"], 1),
        f"El plan de carriles protegidos suma {dec(round(bf['km'], 1))} km por {dec(round(bf['build_eur'] / 1e6, 1))} millones de euros y devuelve {dec(bf['bcr'])} € por cada euro (relación beneficio-coste).",
        f"The protected-lane plan adds {round(bf['km'], 1)} km for €{bf['build_eur'] / 1e6:.1f} million and returns €{bf['bcr']} per euro (benefit-cost ratio).",
        "En data/lane_network_plans.json: `bestfirst` (`km`, `build_eur`, `bcr`).", "In data/lane_network_plans.json: `bestfirst` (`km`, `build_eur`, `bcr`).",
        ["data/lane_network_plans.json", "data/lane_network_plan.csv"], "pipeline/historical/15_lane_network.py (método en docs/METHOD_LANES.md; entradas fijadas con SHA-256)", ["trips23", "infra"],
        "Es una estimación con parámetros publicados (HEATCO, Broach et al.), no un presupuesto. Los supuestos y la sensibilidad están en docs/METHOD_LANES.md.",
        "An estimate with published parameters (HEATCO, Broach et al.), not a budget. Assumptions and sensitivity are in docs/METHOD_LANES.md.")
    add("reparto_modal", 0.5,
        "La bici es el 0,5% de los viajes en Madrid (Barcelona 3,8%, París 11,2%, Copenhague 21%).",
        "Bikes are 0.5% of trips in Madrid (Barcelona 3.8%, Paris 11.2%, Copenhagen 21%).",
        "Cifra citada tal cual de la fuente; no se calcula aquí.", "Quoted as published; not calculated here.",
        [], "site/app.js (constante BENCH.modal)", ["edm"],
        "Último dato comparable (encuesta de 2018). Las cifras municipales más recientes usan datos de móviles y no son comparables.",
        "Last comparable figure (2018 survey). More recent city figures use mobile-phone data and are not comparable.")
    return list(F.values())


def markdown(figs, updated):
    out = ["# Cifras y cómo comprobarlas", "",
           "Cada número que citamos en la web, en las redes y en la prensa está aquí, con la fórmula para repetirlo en una hoja de cálculo, el fichero de `data/` de donde sale, el script que lo construyó y la página del organismo que publicó el dato original. "
           f"Los valores de esta página los calcula `pipeline/figures.py` desde `data/` (actualizado {updated}); no se escriben a mano.", "",
           "**Comprobar una cifra en dos clics:** de la cifra en la web a su fila aquí (1), y de la fila al fichero o a la fuente original (2).", "",
           "Si encuentras un error, [abre un issue](https://github.com/jaimeoliver1/madrid-en-bici/issues/new?template=dato-incorrecto.yml): corregimos primero y explicamos después.", ""]
    for title, flag in (("Los tres titulares", 1), ("Otras cifras", 0)):
        out += [f"## {title}", ""]
        for f in (x for x in figs if x["headline"] == flag):
            out += [f"### <a id=\"{f['id']}\"></a>{f['es']}", "",
                    f"- **Cómo se calcula:** {f['calc_es']}",
                    f"- **Fichero:** " + (", ".join(f"[`{p}`]({REPO}{p})" for p in f["files"]) or "—"),
                    f"- **Script:** {f['script']}",
                    f"- **Fuente original:** " + "; ".join(f"[{n}]({u})" for n, u in f["upstream"])]
            if f["caveat_es"]:
                out.append(f"- **Ojo:** {f['caveat_es']}")
            out.append("")
    out += ["---", "Qué datos faltan y por qué: [DATA_SOURCES.md](DATA_SOURCES.md). Métodos: [ROUTING.md](ROUTING.md), [METHOD_LANES.md](METHOD_LANES.md).", ""]
    return "\n".join(out)


if __name__ == "__main__":
    D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data")
    OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "docs", "CIFRAS.md")
    figs = compute(D)
    updated = json.load(open(os.path.join(D, "refresh_meta.json")))["refreshed_at"][:10]
    json.dump(figs, open(os.path.join(D, "figures.json"), "w"), ensure_ascii=False, indent=1)
    open(OUT, "w").write(markdown(figs, updated))
    # the three headlines in the Spanish README sit between markers and are rewritten here, so they never go stale
    rd = os.path.join(os.path.dirname(os.path.abspath(OUT)), "..", "README.es.md")
    if os.path.exists(rd):
        txt, a, b = open(rd).read(), "<!-- titulares:start -->", "<!-- titulares:end -->"
        heads = [f for f in figs if f["headline"]]
        block = "\n".join(f"{i}. **{n}.** {f['es']} [Cómo lo sabemos](docs/CIFRAS.md#{f['id']})" for i, (n, f) in enumerate(zip(("Cobertura", "Uso", "Seguridad"), heads), 1))
        open(rd, "w").write(txt[:txt.index(a) + len(a)] + "\n" + block + "\n" + txt[txt.index(b):])
    for f in figs:
        print(f"{f['id']:22} {f['value']}  {f['es']}")
