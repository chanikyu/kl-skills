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

`code-check` se ejecuta con cada archivo de código que se escribe: Python y los lenguajes de `data/languages.json` (JavaScript, TypeScript, Rust, Swift, Go, shell y más). En un repositorio git solo señala los nombres que no estaban en el último commit, para que arreglar una línea no acabe renombrando todo el archivo. Informa y nunca bloquea.

## Límites

Python se lee con su propio analizador. Los demás lenguajes se leen con patrones, así que a veces un nombre se detecta por error. Los lenguajes que cierran bloques con `end` (Ruby, Lua, Julia, Elixir) solo pasan la revisión de nombres.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
