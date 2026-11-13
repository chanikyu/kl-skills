[English](readable-code.md) · [한국어](readable-code-ko.md) · [日本語](readable-code-ja.md) · [中文](readable-code-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# readable-code

Código que el próximo lector puede seguir: nombres que dicen qué contienen y comentarios que dicen por qué.

## Úsala en Claude

No hace falta decir nada: se aplica siempre que se escribe o se cambia código.

## Qué hace

1. Un nombre dice qué es el valor: `student_name`, no `n`.
2. Los comentarios explican por qué el código es como es, no qué hace cada línea.
3. Los valores van en archivos de datos, no en el código (consulta [no-hardcoding](no-hardcoding-es.md)).

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `check_code.py <files>` | Señala nombres vagos, docstrings que faltan y funciones largas sin ningún comentario |

Los nombres cortos permitidos y los nombres vagos son archivos de datos en `data/`.

## Hooks que la respaldan

`code-check` se ejecuta con cada archivo de Python que se escribe. Informa y nunca bloquea.

## Límites

La revisión solo lee Python.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
