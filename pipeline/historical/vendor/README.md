# Vendored inputs

Small inputs whose publisher replaces the file in place, kept here so the analysis can be rebuilt from exactly what it used. Links, SHA-256 and the scripts that read each file are in `../inputs.json`.

| File | Source | Licence |
|---|---|---|
| `Distritos.zip` | Ayuntamiento de Madrid, [Límites administrativos](https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas), district boundaries, September 2026 | CC BY 4.0 |
| `Barrios.zip` | Ayuntamiento de Madrid, [Límites administrativos](https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas), barrio boundaries, September 2026 | CC BY 4.0 |
| `poblacion_1_enero.csv` | Ayuntamiento de Madrid, [Población por distrito y barrio a 1 de enero](https://datos.madrid.es/dataset/300557-0-poblacion-distrito-barrio), 2018–2026 | CC BY 4.0 |
| `station_heights_2023_eudem25m.csv` | Height of each 2023 BiciMAD station from [EU-DEM v1.1](https://www.opentopodata.org/datasets/eudem/) (European Environment Agency, Copernicus), via the OpenTopoData API; written by `05_station_elevation.py` | Copernicus data policy, free use with attribution |
