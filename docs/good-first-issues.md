# Issues listos para abrir

Borradores de las primeras tareas para colaboradores externos. Cada una es concreta, tiene un criterio claro de "hecho" y apunta a los ficheros donde empezar. Los huecos de datos salen de [DATA_SOURCES.md](DATA_SOURCES.md).

Crear las etiquetas y los issues (hace falta `gh` autenticado con la cuenta propietaria del repositorio):

```bash
gh label create "good first issue" --color 7057ff --description "Buena primera contribución" --force
gh label create "help wanted"      --color 008672 --description "Se agradece ayuda" --force
gh label create data               --color 1d76db --force
gh label create needs-triage       --color ededed --force
gh label create docs               --color 0075ca --force
gh label create a11y               --color d93f0b --force
# después, cada bloque de abajo: gh issue create --title "…" --label "…" --body-file -
```

---

## 1. Revisar la traducción al inglés
**Etiquetas:** `good first issue`, `docs`

La web está en español con un interruptor a inglés, pero las traducciones las hemos escrito nosotros. Si el inglés es tu lengua o la dominas, lee la web con el interruptor EN y corrige lo que suene raro o sea incorrecto.

- Dónde: `T.en` en `site/app.js`.
- Hecho cuando: un pull request con las correcciones, sin cambiar el significado de ninguna cifra.

## 2. Una prueba que compruebe que las cifras no se desincronizan
**Etiquetas:** `good first issue`

`pipeline/figures.py` calcula las cifras que citamos y `pipeline/build_site.py` calcula las que pinta la web. Ahora mismo `build_site.py` comprueba seis a mano (`assert`). Queremos una prueba con `pytest` que recalcule todas desde `data/` y falle si `docs/CIFRAS.md` o `data/figures.json` no coinciden con lo que hay en `data/`.

- Dónde: `pipeline/figures.py` (`compute`), nueva carpeta `tests/`.
- Hecho cuando: `pytest` pasa en local y se ejecuta en un workflow de GitHub en cada pull request.

## 3. Auditoría de accesibilidad de teclado y lector de pantalla
**Etiquetas:** `good first issue`, `a11y`

Los mapas de barrios y el planificador de rutas se manejan con ratón o con el dedo. Comprueba si se puede usar el selector de barrio, las pestañas y el botón de compartir solo con teclado, y si un lector de pantalla anuncia algo útil.

- Dónde: `site/index.html`, `site/app.js`.
- Hecho cuando: hay un issue por cada problema encontrado, o un pull request que arregle los más sencillos (foco visible, etiquetas `aria`).

## 4. Contraste y modo oscuro
**Etiquetas:** `good first issue`, `a11y`

Revisa el contraste de texto y de los colores de los mapas en modo claro y oscuro (herramientas del navegador o <https://webaim.org/resources/contrastchecker/>) y a 400 px de ancho.

- Dónde: los colores están al principio del `<style>` de `site/index.html`.
- Hecho cuando: lista de combinaciones que no llegan a 4,5:1 (3:1 en texto grande) o un pull request con la corrección.

## 5. Explorar el histórico de disponibilidad de BiciMAD (dataset 216343)
**Etiquetas:** `data`, `help wanted`

No tenemos historial de bicis disponibles por estación; solo una foto en directo. El dataset 216343 de datos.madrid.es dice contenerlo y no lo hemos explorado.

- Hecho cuando: una nota en `docs/` con qué contiene (periodo, frecuencia, estaciones, calidad) y si sirve para medir cuántas estaciones se vacían y a qué horas.

## 6. Grabar la disponibilidad cada pocos minutos
**Etiquetas:** `data`, `help wanted`

Si el dataset 216343 no sirve, podemos construir nuestro propio historial: un GitHub Action programado que guarde el feed GBFS (`station_status`) cada 10 o 15 minutos.

- Dónde: `.github/workflows/`, el feed está en `GBFS` en `pipeline/refresh.py`.
- Hecho cuando: se acumula un fichero comprimido por día fuera de `site/` y hay una nota con el tamaño estimado por año.

## 7. Aclarar cuántas bicis tiene BiciMAD
**Etiquetas:** `data`, `good first issue`

El feed en tiempo real da 9.421 bicis y los informes municipales unas 8.000 (mayo de 2026). La cifra de «viajes por bici y día» depende de esto (`docs/CIFRAS.md#viajes_por_bici`).

- Hecho cuando: una nota con las fuentes consultadas, la razón probable de la diferencia (¿bicis fuera de servicio?, ¿dos definiciones de flota?) y cuál conviene usar.

## 8. Una página y una imagen de previsualización por barrio
**Etiquetas:** `help wanted`

Hoy la imagen «la nota de mi barrio» se genera en el navegador al pulsar compartir. Pero al pegar un enlace `?barrio=…` en WhatsApp o X la previsualización es la genérica, porque esos servicios no ejecutan JavaScript. Hace falta una página estática por barrio con sus etiquetas `og:` y una imagen prerenderizada (131 en total) que se regeneren con el refresco mensual.

- Dónde: `site/share.js` dibuja la imagen; `pipeline/` para generar las páginas.
- Hecho cuando: pegar el enlace de un barrio en un chat muestra la imagen de ese barrio.

## 9. Falta de datos: antigüedad de los carriles bici
**Etiquetas:** `data`, `help wanted`

La capa oficial de infraestructura ciclista no trae fecha de construcción, así que no podemos mostrar cómo ha crecido la red. ¿Hay otra fuente (memorias municipales, OpenStreetMap con `start_date`, histórico del geoportal) que permita reconstruirlo?

- Hecho cuando: una nota con las fuentes encontradas y un ejemplo de cuántos km se pueden fechar.
