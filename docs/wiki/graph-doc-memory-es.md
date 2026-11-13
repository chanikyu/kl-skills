[English](graph-doc-memory.md) · [한국어](graph-doc-memory-ko.md) · [日本語](graph-doc-memory-ja.md) · [中文](graph-doc-memory-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# graph-doc-memory

Convierte toda la wiki en una sola base de datos de grafo y la abre como un grafo interactivo en el navegador, solo cuando lo pides.

## Úsala en Claude

Di «Muéstrame el grafo de la wiki».

## Qué hace

1. Cada página dentro de `<topic>/wiki/` es un nodo; cada `[[link]]` o `[text](page.md)` es un enlace. Los enlaces a páginas que aún no existen se quedan en el grafo como círculos discontinuos: huecos que vale la pena llenar.
2. Al construirlo se generan `~/llm-wiki-docs/.graph/graph.json` y un `viewer.html` autónomo que se abre por `file://` sin servidor.
3. El visor: búsqueda, interruptores para páginas huérfanas y páginas que faltan, tamaño de los nodos, grosor de los enlaces, las cuatro fuerzas y un grafo local alrededor del nodo seleccionado. Haz clic en un nodo para ver su ruta, sus enlaces y sus enlaces entrantes.

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `open-graph.sh [--root DIR] [--out DIR] [--no-build]` | Reconstruye el grafo y abre el visor |
| `build_graph.py [--root ROOT] [--out OUT] [--quiet]` | Lo reconstruye sin abrirlo |

## Hooks que la respaldan

`wiki-graph` reconstruye el grafo cuando se escribe una página de la wiki; `wiki-sync` detecta las ediciones hechas en la shell al terminar la respuesta.

## Límites

Nunca se abre por sí solo. El grafo está tan conectado como lo estén los enlaces de las páginas.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
