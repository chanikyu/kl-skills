[English](no-hardcoding.md) · [한국어](no-hardcoding-ko.md) · [日本語](no-hardcoding-ja.md) · [中文](no-hardcoding-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# no-hardcoding

Mantiene valores, listas, correspondencias, rutas y umbrales fuera del código.

## Úsala en Claude

No hace falta decir nada: se aplica siempre que el código está a punto de llevar un valor.

## Qué hace

1. Un valor que ya está en un archivo se lee de ese archivo, nunca se copia en el código.
2. Las tablas de correspondencia, las listas de alias y las listas de objetivos van en archivos de datos (`.tsv`, `.json`).
3. Las rutas se calculan a partir de la ubicación del script, se reciben como argumentos o se leen del entorno.
4. Los umbrales, las semillas y los recuentos son argumentos de línea de comandos.
5. Solo se quedan en el código las constantes que nunca cambian, con un nombre y una fuente.

## Límites

Es una regla que debe seguir el modelo; ningún script la comprueba directamente.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
