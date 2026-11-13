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

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `recall.py "question" [--mode auto\|cag\|rag] [--top 3] [--min-coverage 0.4]` | Busca en la wiki |

Las palabras vacías, las partículas y los fragmentos comunes son archivos de datos en `data/`. `WIKI_RECALL_MIN_COVERAGE` cambia el umbral.

## Hooks que la respaldan

El gate `wiki-recall` se ejecuta con cada mensaje.

## Límites

Las líneas adjuntas son extractos elegidos por la búsqueda. Abre la página antes de citarla.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
