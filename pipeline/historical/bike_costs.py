"""Shared bike routing weights for every script that routes trips on the OSM street graph
(10_film_routes.py, 11_all_routes.py, 14_lane_priority.py), so they always agree.

A weight multiplies a segment's length: below 1 a rider prefers it, above 1 they avoid it.
Madrid's big boulevards (Castellana, Recoletos, Prado) are tagged "trunk" in OSM: urban, 50 km/h, 3-6 lanes,
open to bikes, so they are in the graph but costly.
"""
COST = {"cycleway": 0.6, "living_street": 0.9, "residential": 1.0, "unclassified": 1.0, "service": 1.15, "busway": 1.1,
        "tertiary": 1.15, "tertiary_link": 1.15, "secondary": 1.35, "secondary_link": 1.35, "primary": 1.6, "primary_link": 1.6,
        "trunk": 1.9, "trunk_link": 1.9, "pedestrian": 1.3, "path": 1.0, "track": 1.2, "footway": 1.6, "steps": 12.0}
INFRA = 0.75  # a road with a painted or separated bike lane (OSM cycleway=lane/track/separate or bicycle=designated)


def factor(t):
    """Weight for an OSM way's tags, or None if bikes can't use it."""
    hw = t.get("highway")
    if hw not in COST or t.get("access") in ("no", "private") or t.get("bicycle") == "no": return None
    f = COST[hw]
    if hw != "cycleway" and (t.get("bicycle") == "designated" or any(t.get(k, "").startswith(("track", "lane", "separate"))
                                                                 for k in ("cycleway", "cycleway:left", "cycleway:right", "cycleway:both"))):
        f = min(f, INFRA)
    return f
