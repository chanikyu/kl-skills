[English](wiki-recall.md) · [한국어](wiki-recall-ko.md) · [日本語](wiki-recall-ja.md) · [中文](wiki-recall-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# wiki-recall

Trae a la respuesta lo que la wiki ya sabe, en lugar de volver a deducirlo.

## Úsala en Claude

No hace falta decir nada: un hook busca en la wiki con cada mensaje. Pregunta «¿Qué decidimos sobre X?» para ir más allá de las líneas adjuntas.

## Qué hace

1. Con cada mensaje, el hook adjunta las rutas y las líneas clave de las páginas claramente relacionadas: al menos dos palabras en común y el 40 % del peso de la pregunta cubierto. Los mensajes sin relación no reciben nada.
2. Para profundizar, Claude lee las páginas. Cuando toda la wiki es pequeña (30 000 caracteres o menos), la lee entera (CAG); si no, elige las mejores páginas (RAG: BM25, cobertura de la pregunta, vecinos en el grafo).
3. El coreano se compara en fragmentos de dos letras; una palabra de una sola letra solo cuenta cuando aparece sola.
4. El resumen de una línea de cada página en el índice (index.md) cuenta como parte de la página. De la pregunta se quitan las partículas que quedan solas ("Tauri를") y las terminaciones verbales ("뭐였지", "할까").
5. La cobertura y las palabras compartidas se miden dentro de un fragmento (un párrafo o una fila de tabla), no en toda la página, para que una página larga no se adjunte a cualquier mensaje.
6. El hook pasa la carpeta de trabajo. Solo se adjuntan los temas cuyo nombre está en esa ruta, los que el mensaje nombra y los temas compartidos.
7. Lo que el hook no encuentra lo busca Claude a fondo: toma las frases clave del mensaje, ejecuta `recall.py --excerpt` para extraer todos los fragmentos relacionados con cada frase y organiza solo lo que encaja con la pregunta.

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `recall.py "question" [--mode auto\|cag\|rag] [--top 3] [--min-coverage 0.4]` | Busca en la wiki |

Las palabras vacías, las partículas y los fragmentos comunes son archivos de datos en `data/`. `WIKI_RECALL_MIN_COVERAGE` cambia el umbral; `WIKI_RECALL_SHARED_TOPICS` (separados por comas) indica los temas que no pertenecen a ningún proyecto y siempre se pueden adjuntar.

## Hooks que la respaldan

El gate `wiki-recall` se ejecuta con cada mensaje.

## Límites

Las líneas adjuntas son extractos elegidos por la búsqueda. Abre la página antes de citarla.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
