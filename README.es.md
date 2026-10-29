# Madrid en bici

[Read in English](README.md)

**¿Es fácil moverse en bici por Madrid?** Una web pública que cuenta, con datos abiertos y muchos mapas, cómo van BiciMAD y los carriles bici, y qué haría falta para que la ciudad fuera más fácil de pedalear. Está en español, con interruptor a inglés.

- **Web:** https://madrid-en-bici.vercel.app
- **Qué hay:** dos pestañas. **Ir en bici**, para quien pedalea: BiciMAD en directo, una animación de 24 horas, un planificador de rutas, la cobertura de tu barrio y consejos (cuestas, horas punta, cruces peligrosos, lluvia). **Mejorar Madrid**, para el Ayuntamiento: la nota de la ciudad, la red de carriles, un plan con coste de los próximos carriles protegidos, seis cambios concretos, accidentes, estaciones y demanda.
- **La nota de tu barrio:** elige tu barrio y pulsa *Compartir*: genera una imagen para WhatsApp o redes. El enlace `?barrio=Nombre` lleva directo a cualquier barrio.

## Tres titulares

<!-- titulares:start -->
1. **Cobertura.** Solo el 4,6% de los madrileños vive en un barrio con la densidad de estaciones de BiciMAD que recomienda la guía de la ITDP (8 de 131 barrios). [Cómo lo sabemos](docs/CIFRAS.md#cobertura)
2. **Uso.** BiciMAD casi se ha duplicado en dos años: 11,3 millones de viajes de febrero a septiembre de 2026, un 88% más que en 2024 (6,1 millones). [Cómo lo sabemos](docs/CIFRAS.md#crecimiento)
3. **Seguridad.** Los accidentes con bicicleta atendidos por la Policía Municipal han subido un 52% desde 2019: de 785 a 1.191 al año. [Cómo lo sabemos](docs/CIFRAS.md#accidentes)
<!-- titulares:end -->

## Comprueba cualquier cifra

Todas las cifras que citamos están en [`docs/CIFRAS.md`](docs/CIFRAS.md) (y al pie de la web, en *Cada cifra, con su fuente*). Cada fila trae:

1. la fórmula, para repetirla en una hoja de cálculo;
2. el fichero de [`data/`](data/) de donde sale;
3. el script que lo construyó;
4. la página del organismo que publicó el dato original;
5. los límites del dato (qué no dice).

Los valores los calcula [`pipeline/figures.py`](pipeline/figures.py) desde `data/` cada mes; no se escriben a mano. Qué datos faltan y por qué: [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md). ¿Ves un error? [Abre un issue](https://github.com/jaimeoliver1/madrid-en-bici/issues/new?template=dato-incorrecto.yml): corregimos primero y explicamos después.

## Cómo contribuir

Hay tareas pequeñas y claras con la etiqueta [good first issue](https://github.com/jaimeoliver1/madrid-en-bici/labels/good%20first%20issue): revisar el inglés, probar la accesibilidad, aclarar un dato. Puedes escribir en español o en inglés. Las normas, en [CONTRIBUTING.md](CONTRIBUTING.md) (en inglés).

## Ponerlo en marcha

```bash
python3 -m http.server -d site 8000      # abre http://localhost:8000
pip install -r requirements.txt
python3 pipeline/refresh.py              # actualiza los datos, unos 2 minutos
```

Un GitHub Action ejecuta ese refresco el día 10 de cada mes. El resto de la estructura del repositorio y del despliegue está en [README.md](README.md).

## Licencia y atribución

El código es MIT ([LICENSE](LICENSE)). Los datos pertenecen a quien los publica y se reutilizan bajo sus condiciones de datos abiertos, que exigen atribución: EMT Madrid (BiciMAD, licencia ODC Attribution), Ayuntamiento de Madrid (datos.madrid.es), OpenStreetMap (ODbL), NOAA (GHCN-Daily) y Copernicus (EU-DEM). Si reutilizas la web, mantén la lista de fuentes.
