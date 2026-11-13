[English](research-to-wiki.md) · [한국어](research-to-wiki-ko.md) · [日本語](research-to-wiki-ja.md) · [中文](research-to-wiki-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# research-to-wiki

Convierte una petición de investigación en una página de la wiki que muestra hasta qué punto está establecida cada afirmación.

## Úsala en Claude

Di «Investiga si X causa Y» o «Busca la evidencia sobre X». `skill-match` nombra la skill en las peticiones de investigación.

## Qué hace

1. Busca primero en la wiki; actualiza una página existente en lugar de empezar una nueva.
2. Busca en la bibliografía los dos lados de la pregunta y los factores de confusión.
3. Termina cada línea de fuente con dos etiquetas: qué tipo de estudio es (`메타분석` metaanálisis, `무작위시험` ensayo aleatorizado, `추적관찰` cohorte, `유전분석` aleatorización mendeliana, `단면비교` transversal, `동물실험` en animales, `세포실험` en células, `리뷰` revisión, `의견` opinión) y cuánto se leyó (`본문` texto completo, `초록` resumen del artículo, `검색요약` resumen de la búsqueda). El comprobador lee estos nombres coreanos de sus archivos de datos, así que se escriben tal cual.
4. Escribe la página con la conclusión primero, con tus propias palabras, y cada número junto a aquello con lo que se compara.
5. La comprueba y luego la anota en el índice y el registro de la wiki.

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `check_research.py <page>` | Señala una conclusión que falta, fuentes sin enlace o sin etiquetas, y citas sin fuente |

Los nombres de las etiquetas son archivos de datos (`data/evidence-levels.tsv`, `data/reading-levels.txt`); la plantilla de la página es `assets/research-page-template.md`.

## Límites

La revisión ve si las etiquetas están, no si son correctas. Para eso sigue haciendo falta leer el artículo.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
