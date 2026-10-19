# Where to build protected bike lanes: method

This note explains how `pipeline/historical/15_lane_network.py` decides which streets should get a protected bike lane, and in what order. Every value comes from a published source or from Madrid's own data; the code keeps them in one place, `pipeline/historical/appraisal.py`.

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

When a corridor is protected, its segments become separated paths and **every trip is routed again**. Riders who now find the protected street cheaper switch to it. Routing is all-or-nothing: each trip takes its single best route.

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

Expected injury cost on a street = bike-km ridden on it × its injury rate × cost per accident. Because re-routing moves riders between streets, the safety effect includes riders leaving dangerous streets as well as the protected street becoming safer.

## 5. Cost of building

- **Normal streets**: €480,000 per km, the average tender cost in Madrid's *Plan Director de Movilidad Ciclista* (2008 euros), **€658,000 in 2025**.
- **Big avenues** (trunk, primary, secondary): the Paseo de la Castellana contract (Plaza de Castilla – Raimundo Fernández Villaverde), 4.25 km awarded for €4.0 million (around 2022): **€1.03 million per km in 2025**.
- Build costs are spread over **25 years at a 3% real discount rate**, the European Commission's reference period for urban transport and its social discount rate outside Cohesion countries (*Guide to Cost-Benefit Analysis of Investment Projects*, 2014). That is 5.74% of the build cost per year.

All prices are moved to 2025 euros with Eurostat's harmonised consumer price index for Spain (annual averages: 2002 75.86, 2008 92.41, 2022 115.95, 2025 126.65).

## 6. Choosing the network

1. Candidates are the most promising corridors from `14_lane_priority.py`: named street pieces of about 1 km, ranked by bikes, stress and accidents per km, by total score, and by accidents.
2. Each candidate is valued on its own (re-routing everything).
3. Corridors are added one at a time, always the one with the highest **benefit-cost ratio** for the network built so far. After each addition, corridors that touch it are re-valued at once, because connections can make them worth more; others are re-valued lazily when they reach the top.
4. It stops when the budget is spent or when no addition returns more than it costs (benefit-cost ratio below 1).

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
