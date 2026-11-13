[English](llm-wiki-docs.md) · [한국어](llm-wiki-docs-ko.md) · [日本語](llm-wiki-docs-ja.md) · [中文](llm-wiki-docs-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# llm-wiki-docs

Guarda lo que aprendes en una wiki dentro de `~/llm-wiki-docs/<topic>/wiki/`: una página por tema, escrita con tus propias palabras, con un índice y un registro.

## Úsala en Claude

Di «Pon esto en la wiki» o «Guarda esto en la wiki». `skill-match` nombra la skill cuando un mensaje la pide. Claude también la usa después de una investigación o un análisis que vale la pena conservar.

## Qué hace

1. Las fuentes se quedan tal cual en `raw/`. La página de la wiki es un texto nuevo, nunca una fuente editada.
2. Un tema es una página. El mismo tema actualiza la página existente en lugar de empezar una casi duplicada.
3. `index.md` tiene una línea por página y es lo primero que se busca.
4. En `log.md` solo se añade al final: `## [YYYY-MM-DD] ingest | title`.
5. Las páginas se enlazan con `[[page]]`, y cada afirmación remite a su fuente.

Lo que cambia cuando cambia el código se queda en la documentación del propio proyecto; lo que sigue siendo cierto va a la wiki.

## Archivos y scripts

```text
~/llm-wiki-docs/<topic>/
  README.md      what the topic holds and where things go
  raw/           sources, untouched
  wiki/          pages, index.md, log.md
```

| Script | Qué hace |
| --- | --- |
| `new-topic.sh <topic> ["description"]` | Crea las carpetas y un índice y un registro vacíos, sin sobrescribir nada |
| `index-add.py <topic> <page> <category> ["summary"]` | Añade una página al índice |
| `log-append.py <topic> ingest\|query\|lint "title" [--pages --source --note]` | Añade una entrada al registro |
| `lint.py [topic]` | Busca páginas que faltan en el índice o en el registro, enlaces rotos y páginas huérfanas |

`LLM_WIKI_ROOT` mueve la raíz fuera de `~/llm-wiki-docs`.

## Hooks que la respaldan

`wiki-index-check` avisa de una página que falta en el índice, `wiki-graph` vuelve a dibujar el grafo, `prose-check` señala los puntos difíciles de leer y `wiki-sync` detecta, al terminar la respuesta, las páginas editadas desde la shell.

## Límites

La wiki solo vive en tu equipo; nada la sincroniza con otro sitio.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
