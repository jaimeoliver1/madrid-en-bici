"""Published parameters for the lane-network appraisal (15_lane_network.py): how riders weigh streets,
what a crash costs, what time is worth and what a lane costs to build. Everything is in 2025 euros.

Sources (also listed in docs/METHOD_LANES.md):
[B12] Broach, Dill & Gliebe (2012). Where do cyclists ride? A route choice model developed with revealed preference
      GPS data. Transportation Research Part A 46(10):1730-1740. Values from Table 3 of the TRB 2011 working paper
      (same model): https://ppms.trec.pdx.edu/media/project_files/TRB2011_Bicycle%20route%20choice%20model%20developed%20using%20revealed%20preference%20GPS%20data.pdf
[H06] HEATCO Deliverable 5 (2006). Proposal for harmonised guidelines. EU 6th Framework Programme. Spain:
      Table 0.4 (non-work value of travel time) and the accident cost table (factor prices, 2002 euros).
[L11] Lusk et al. (2011). Risk of injury for bicycling on cycle tracks versus in the street. Injury Prevention 17(2):131-135.
[T12] Teschke et al. (2012). Route infrastructure and the risk of injuries to bicyclists: a case-crossover study.
      American Journal of Public Health 102(12):2336-2343.
[EC14] European Commission (2014). Guide to Cost-Benefit Analysis of Investment Projects 2014-2020. Social discount
      rate (3% outside Cohesion countries) and reference period for urban transport (25-30 years, Table 2.1).
[PD]  Ayuntamiento de Madrid, Plan Director de Movilidad Ciclista, cost chapter 8.1.2.1: average tender cost per km.
[CAS] Ayuntamiento de Madrid (diario.madrid.es): Paseo de la Castellana bike lane, Plaza de Castilla - Raimundo
      Fernandez Villaverde, 4.25 km awarded for 4.0 M EUR (c. 2022).
[ES]  Eurostat HICP, Spain, annual average index (prc_hicp_aind, CP00): 2002 75.86, 2008 92.41, 2022 115.95, 2025 126.65.
[MAD] Ayuntamiento de Madrid open data: "Trafico. Intensidad media diaria anual por tramos" (IMD 2019, per direction).
[DEM] Copernicus DEM GLO-30 (ESA, 2021), tile N40 W004.
"""
import math

HICP = {2002: 75.86, 2008: 92.41, 2011: 96.94, 2022: 115.95, 2025: 126.65}  # [ES]
to2025 = lambda eur, year: eur * HICP[2025] / HICP[year]

# ---------- how riders weigh a street [B12], non-commute column of Table 3 ----------
# Broach's utility is linear in log(route distance), so a share p of the route on a feature multiplies the perceived
# distance by exp(k * p), with k = ln(1 + published % / 100). For one link this is an extra k per km ridden on it.
k = lambda pct: math.log(1 + pct / 100)
TRAFFIC = [(30000, k(619.4)), (20000, k(137.3)), (10000, k(22.3))]   # AADT without a bike lane; a painted lane offsets it
PATH = k(-26.0)                                                         # off-street / separated bike path (negative = attractive)
SLOPE = [(0.06, k(1106.6)), (0.04, k(290.4)), (0.02, k(72.3))]       # average upslope of the link


def perceived(aadt, painted_lane, separated, upslope):
    """Perceived-distance multiplier for riding one link [B12]."""
    f = 1.0
    if separated: f += PATH
    elif not painted_lane:
        for lo, v in TRAFFIC:
            if aadt >= lo: f += v; break
    for lo, v in SLOPE:
        if upslope >= lo: f += v; break
    return f


# ---------- turning perceived distance into money ----------
SPEED_STRAIGHT_KMH = 10.7  # BiciMAD median straight-line speed, our own 2023 data (data/bicimad_2023_summary.csv);
                           # 15_lane_network.py turns it into a riding speed with the median route/straight-line ratio
VOT = to2025(7.15, 2002)  # EUR per hour, Spain, non-work "other" short-distance trips (car/train column) [H06 Table 0.4]
VOT_COMMUTE = to2025(8.52, 2002)  # sensitivity: commute short-distance [H06 Table 0.4]

# ---------- what a crash costs [H06], Spain, factor prices ----------
COST_DEATH = to2025(1_122_000, 2002)
COST_SERIOUS = to2025(138_900, 2002)
COST_SLIGHT = to2025(10_500, 2002)

# ---------- what a protected lane does to injury risk ----------
CMF = 0.72                # relative risk of injury on cycle tracks vs comparable streets [L11] (95% CI 0.60-0.85)
CMF_RANGE = (0.60, 0.85)  # [L11]; [T12] finds 0.11 against major streets with parked cars, an upper bound on benefits

# ---------- what a lane costs ----------
BUILD_STREET = to2025(480_000, 2008)      # EUR per km, average tender cost in the Plan Director [PD]
BUILD_AVENUE = to2025(4_000_000 / 4.25, 2022)  # EUR per km on a big avenue, the Castellana contract [CAS]
DISCOUNT, YEARS = 0.03, 25                # [EC14]
ANNUITY = DISCOUNT / (1 - (1 + DISCOUNT) ** -YEARS)  # share of the build cost charged per year


def build_cost_km(road_class):
    return BUILD_AVENUE if road_class in ("trunk", "primary", "secondary") else BUILD_STREET
