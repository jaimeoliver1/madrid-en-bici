# Where to build protected bike lanes: method

> **Results on the website:** "¿Dónde poner los próximos carriles protegidos?" in *Para el Ayuntamiento*, and the route planner's switch *Con los carriles protegidos propuestos*. Routing itself is explained in [ROUTING.md](ROUTING.md).

This note explains how `pipeline/historical/15_lane_network.py` decides which streets should get a protected bike lane, and in what order. Every value comes from a published source or from Madrid's own data; the code keeps them in one place, `pipeline/historical/appraisal.py`.

**Reproducing it.** Every input is pinned to the exact file used, with its link, SHA-256 and licence, in `pipeline/historical/inputs.json` (street network: OpenStreetMap, Geofabrik's Madrid snapshot of 1 January 2026); `pipeline/historical/fetch_inputs.py` downloads and checks them. Each run writes the SHA-256 of its inputs and the git commit into `data/lane_network_plans.json`. Steps in [ROUTING.md](ROUTING.md#rebuilding).

## The question

For each candidate street corridor, what is it worth to society each year to give it a protected (separated) lane, compared with what it costs? All effects are measured in the same unit, **2025 euros per year**, so there are no arbitrary weights between "bikes" and "safety".

## 1. How riders choose a route

Each street segment has a *perceived distance*: its length times a multiplier that depends on what it is like to ride. Riders take the route with the least perceived distance.

The multipliers come from **Broach, Dill & Gliebe (2012)**, a route-choice model estimated from 1,449 GPS-tracked bike trips in Portland, Oregon. We use the non-commute values of their Table 3 ("distance value" of each attribute). Because their model is linear in the logarithm of route length, a feature on a share *p* of the route multiplies perceived length by exp(*k p*), with *k* = ln(1 + published %). For a single segment this is an extra *k* per km.

| Feature of a segment | Published value (non-commute) | Extra perceived km per km ridden |
|---|---|---|
| Motor traffic 10,000–20,000 vehicles/day, no bike lane | +22.3% | +0.20 |
| 20,000–30,000 vehicles/day, no bike lane | +137.3% | +0.86 |
| 30,000+ vehicles/day, no bike lane | +619.4% | +1.97 |
| Painted bike lane | offsets the traffic penalty | 0 |
| Separated bike path | −26.0% | −0.30 |
| Uphill 2–4% | +72.3% | +0.54 |
| Uphill 4–6% | +290.4% | +1.36 |
| Uphill 6% or more | +1,106.6% | +2.49 |

Inputs for Madrid:
- **Motor traffic**: the city's 2019 average daily traffic per road section, *Tráfico. Intensidad media diaria anual por tramos* (datos.madrid.es). 2019 is the last full year before the pandemic. Counts measured at the same place are summed over directions and matched to OpenStreetMap streets by name, then spread along the street to the nearest count within 1 km. 1,057 of 1,537 count locations match; about 35,000 street segments get a measured value. Main roads with no count nearby take the median of their road class; residential streets, which the city does not count, take zero.
- **Slopes**: Copernicus DEM GLO-30 (30 m). Each street's elevation profile is smoothed over about 50 m so DEM noise does not create fake hills; bridges and tunnels take a straight line between their ends.
- **Bike lanes**: OpenStreetMap tags (painted lanes, tracks) plus the city's exclusive bike-lane layer.
- Footways, steps and tracks are not covered by Broach et al.; they keep the weights in `bike_costs.py` (walking a bike is slow), plus the slope penalty.

## 2. Trips and re-routing

Demand is every station-to-station BiciMAD trip of 1 January – 18 February 2023 (about 324,000 trips), the last trip-by-trip data EMT has published. Each trip is routed on the OpenStreetMap street network with Dijkstra's algorithm (SciPy), one run per origin station.

When a corridor is protected, its segments become separated paths, usable in **both directions** even where the street is one-way for cars (a two-way protected lane, or one on each side), and **every trip is routed again**. Riders who now find the protected street cheaper switch to it. Routing is all-or-nothing: each trip takes its single best route.

BiciMAD is only part of Madrid's cycling. To value effects for all cyclists, modelled BiciMAD flows are compared with the city's automatic bike counters (2023 average daily bikes) at the 35 counters on streets with modelled BiciMAD traffic: the median ratio is **2.7**.

## 3. Comfort and time, in euros

The drop in total perceived km is turned into hours at the riding speed, then into euros with the value of time.

- **Riding speed**: the BiciMAD median straight-line speed (10.7 km/h, from the 2023 trips) times the ratio of routed to straight-line length (1.20): about **12.8 km/h**.
- **Value of time**: **HEATCO (2006)**, Deliverable 5, Table 0.4, Spain, non-work "other" short-distance trips: €7.15 per hour in 2002 euros (factor prices), **€11.94 in 2025 euros**. The commute value, €8.52 (€14.22 in 2025), is kept for sensitivity.

## 4. Safety, in euros

**Injuries recorded.** Police records of accidents involving a bicycle, 2019 – August 2026 (6,988 located accidents). Each person involved is classified with the DGT injury codes: died, admitted to hospital for more than 24 hours (serious), treated without a stay over 24 hours (slight), or not hurt. That gives 5,530 slight, 248 serious and 10 fatal injuries; 1,395 accidents had nobody hurt.

**What an injury costs.** HEATCO (2006), Spain, factor prices, 2002 euros, updated to 2025:

| Victim | 2002 € | 2025 € |
|---|---|---|
| Death | 1,122,000 | 1,873,000 |
| Serious injury | 138,900 | 231,900 |
| Slight injury | 10,500 | 17,500 |

That is about **€24,800 per recorded bike accident** on average. For comparison, the DGT-funded study by Abellán Perpiñán et al. (2011) values a serious injury at €224,411 and a slight one at €6,100 (2011 euros), and a statistical life at €1.3 million.

**How risky each street is.** Each accident is attached to the nearest street segment within 25 m. Risk per bike-km is estimated by road class (and whether the segment is already separated) and then adjusted segment by segment with the **empirical Bayes** method (Hauer et al.): a segment's rate is a weighted mix of its class rate and its own record, with more weight on its own record when exposure is high. The weight comes from a negative binomial model fitted to each class.

**What a protected lane does.** A newly protected segment's injury rate is multiplied by **0.72**, the relative risk of injury on cycle tracks against comparable streets found by **Lusk et al. (2011)** in Montreal (95% CI 0.60–0.85). **Teschke et al. (2012)** found a much larger effect (odds ratio 0.11 against major streets with parked cars); we use the more conservative value.

**What is counted: protection only.** The safety benefit is the injury cost avoided by riders on the newly protected streets: their bike-km × the street's injury rate × (1 − 0.72) × cost per accident. Changes in risk when riders switch route are **not** counted. Comparing risk between street types needs exposure for all cyclists by street type, and with BiciMAD-only exposure Madrid's existing separated lanes come out at 160 accidents per million BiciMAD-km, above residential streets (131): accidents at junctions get attached to the lane, and private cyclists use these lanes in different proportions. Until this can be measured properly, the route-switching part is left out rather than counted with a biased rate.

## 5. Cost of building

- **Normal streets**: €480,000 per km, the average tender cost in Madrid's *Plan Director de Movilidad Ciclista* (2008 euros), **€658,000 in 2025**.
- **Big avenues** (trunk, primary, secondary): the Paseo de la Castellana contract (Plaza de Castilla – Raimundo Fernández Villaverde), 4.25 km awarded for €4.0 million (around 2022): **€1.03 million per km in 2025**.
- Build costs are spread over **25 years at a 3% real discount rate**, the European Commission's reference period for urban transport and its social discount rate outside Cohesion countries (*Guide to Cost-Benefit Analysis of Investment Projects*, 2014). That is 5.74% of the build cost per year.

All prices are moved to 2025 euros with Eurostat's harmonised consumer price index for Spain (annual averages: 2002 75.86, 2008 92.41, 2022 115.95, 2025 126.65).

## 6. Choosing the network

1. **Streets, not carriageways.** OpenStreetMap stores each side of a boulevard as a separate one-way road. Road segments with the same street name that touch or lie within 150 m of each other (both carriageways and the side roads of Castellana, for example) are merged into one street.
2. **One lane line per street.** A street gets one protected lane, not one on every carriageway: Castellana has four carriageways side by side, and protecting all four would count four lanes' worth of riders and safety for the price of one. The lane follows a single line, the shortest path between the street's two ends along its own segments (crossing to another street costs 10 times its length, running across the street between carriageways up to 3 times, and stretches already protected count half, so a new lane continues an existing one). It is usable in both directions, which stands for a two-way track or a lane on each side. Only a branch of the same name more than 250 m from that line and at least 300 m long gets a line of its own. The line is then cut into pieces of about 1 km. A piece costs the length of its line not yet protected, at the avenue price if any carriageway of the street there is a trunk, primary or secondary road (so the side road of a big avenue is priced as the avenue).
3. **Three kinds of candidates.** The most promising pieces (ranked by stress-weighted bike-km and accidents, per km and in total), whole streets (when two or more of their pieces are promising), and three axes that cross several street names: Atocha – Prado – Recoletos – Castellana (to Nuevos Ministerios), Bailén – Plaza de España – Princesa, and the southern Rondas. An option only pays for the pieces not yet built.
4. Each candidate is valued on its own (re-routing everything).
5. Options are added one at a time, always the one with the highest **benefit-cost ratio** for the network built so far. After each addition, options that touch it are re-valued at once, because connections can make them worth more; others are re-valued lazily when they reach the top.
6. It stops when the budget is spent or when no addition returns more than it costs (benefit-cost ratio below 1).
7. **Two plans are built and compared**: best-first from an empty network, and the same procedure starting with the Atocha – Castellana axis. A step-by-step method depends on its first choices, so comparing whole plans checks whether a network built around the main axis does better. The headline plan is the one with the larger **net benefit** (yearly benefit minus yearly cost).

## 7. Results

With a budget of €20 million (`data/lane_network_plan.csv`, `data/lane_network_plans.json`; inputs and commit in that file's `provenance` block):

| | Best value first (headline) | Atocha – Castellana axis first |
|---|---|---|
| New protected lane | 23.0 km | 16.4 km |
| Build cost | €19.8M | €15.6M |
| Benefit a year | €3.00M (comfort €1.74M, safety €1.26M) | €1.70M |
| Yearly build cost (3%, 25 years) | €1.14M | €0.90M |
| Net benefit a year | **€1.86M** | €0.80M |
| Benefit per euro | **2.64** | 1.89 |

- **First steps:** Paseo del Prado (€6.74 per euro) and the Atocha roundabout (Plaza del Emperador Carlos V, €6.47); then Alcalá, Paseo de las Delicias, Plaza de la Independencia, Alberto Aguilera, Luchana, Génova, Concepción Jerónima and Villanueva, all above €2.80 per euro.
- **The main axis:** valued on its own, the whole Atocha – Prado – Recoletos – Castellana axis returns €2.87 per euro, but the best-value plan never takes it as a whole. It builds its southern half piece by piece (the Atocha roundabout, Prado, and Recoletos at step 22) and leaves Castellana out: with one lane instead of every carriageway, Castellana's pieces return less than the streets that feed the centre.
- **Then** feeders and crossings: Ciudad de Barcelona, Calle de Atocha, Toledo, Martínez Campos, Fuencarral, Conde de Peñalver, Menéndez Pelayo, Gran Vía, Bailén.
- **The budget binds:** the last addition (Francisco Silvela) still returns €1.72 per euro, so more lanes would pay off.
- **Two plans:** growing outwards from the best-value pieces gives more than twice the net benefit of starting with the whole axis. The axis-first plan then adds Bailén – Princesa (€1.35 per euro) and the whole of Bravo Murillo (€1.06) and stops at €15.6M.

### How the method got here

1. **First ranking (approach A, `14_lane_priority.py`)**: corridors scored by bikes and accidents, 50/50, per km. Found that Castellana, Recoletos and Prado were missing because OSM tags them `trunk` and that road type was left out of the network; fixed in every routing script.
2. **Step by step with hand-picked weights**: added corridors by stress-weighted bike-km avoided after re-routing.
3. **In euros** (published sources, this note): comfort plus safety against cost.
4. **Version 2**: avenues were candidates one carriageway at a time (one direction only, charged as a whole street), so Prado never paid off and the plan left a gap between Atocha and Recoletos. Candidates became whole streets with two-way protected lanes, whole streets and axes were added as options, safety was limited to the protection effect, and two plans were compared.
5. **Version 3**: version 2 protected every carriageway of a street at once. On Recoletos that was 2.8 km of lane (two central carriageways and two side roads) charged as 0.8 km of street, and on the Atocha – Castellana axis 13.4 km charged as 4.9 km, so boulevards got the riders and safety of four lanes for the price of one. Each street now gets one lane line. Wide boulevards were also split into several streets where their carriageways were more than 60 m apart (Prado around its central promenade, Castellana at big junctions); touching segments of the same name are now merged, and the distance is 150 m. The map draws only the stretches each step builds, not the parts of a street that already have a protected lane. At the same time every input was pinned (OpenStreetMap moved from a weekly BBBike extract to Geofabrik's 1 January 2026 snapshot, and the existing lanes are read from the copy of the city's layer in git). Result: 23.0 km for €19.8M at €2.64 per euro (was 21.3 km at €2.95), and Castellana drops out of the best-value plan.

## What this leaves out

- **New riders.** Better lanes attract people who do not cycle today; their health and time gains are not counted, so benefits are understated.
- **Route choice in Portland, not Madrid.** The weights are transferred from Portland. They could be fitted to Madrid with the 2017–2018 BiciMAD GPS tracks.
- **All-or-nothing routing.** Real riders spread over several similar routes, so flows on the best street are overstated.
- **2023 BiciMAD trips and 2019 traffic counts.** The pattern changes slowly, but both are a few years old.
- **Only recorded accidents.** Many minor cycling injuries never reach the police.
- **Width and feasibility.** The model does not know whether a street has room for a lane without removing parking or a traffic lane.
- **Turns and junction design**, which Broach et al. also model, are not in our network yet.
- **The other route maps** on the site (`10_film_routes.py`, `11_all_routes.py`) and the first ranking (`14_lane_priority.py`) still use the simpler street-type weights in `bike_costs.py`.

## References

- Broach, J., Dill, J. & Gliebe, J. (2012). Where do cyclists ride? A route choice model developed with revealed preference GPS data. *Transportation Research Part A* 46(10), 1730–1740. Values from Table 3 of the TRB 2011 working paper of the same model.
- HEATCO (2006). *Developing Harmonised European Approaches for Transport Costing and Project Assessment*, Deliverable 5: Proposal for harmonised guidelines. EU 6th Framework Programme.
- Abellán Perpiñán, J. M. et al. (2011). *El valor monetario de una víctima no mortal y del año de vida ajustado por la calidad en España*. Dirección General de Tráfico.
- Lusk, A. C. et al. (2011). Risk of injury for bicycling on cycle tracks versus in the street. *Injury Prevention* 17(2), 131–135.
- Teschke, K. et al. (2012). Route infrastructure and the risk of injuries to bicyclists: a case-crossover study. *American Journal of Public Health* 102(12), 2336–2343.
- Hauer, E., Harwood, D. W., Council, F. M. & Griffith, M. S. (2002). Estimating safety by the empirical Bayes method: a tutorial. *Transportation Research Record* 1784, 126–131.
- European Commission (2014). *Guide to Cost-Benefit Analysis of Investment Projects: Economic appraisal tool for Cohesion Policy 2014–2020*.
- Ayuntamiento de Madrid. *Plan Director de Movilidad Ciclista*, chapter 8.1.2.1 (costs).
- Ayuntamiento de Madrid (diario.madrid.es). Bike lane on Paseo de la Castellana, Plaza de Castilla – Raimundo Fernández Villaverde.
- Ayuntamiento de Madrid, datos.madrid.es: *Tráfico. Intensidad media diaria anual por tramos* (2019); bicycle accidents (2019–2026); bike counters (2023); cycling infrastructure.
- European Space Agency (2021). Copernicus DEM GLO-30.
- Eurostat. HICP annual average index, Spain (prc_hicp_aind).
- EMT Madrid. BiciMAD trip records, January–February 2023.
