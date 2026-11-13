[English](pipeline-debug.md) · [한국어](pipeline-debug-ko.md) · [日本語](pipeline-debug-ja.md) · [中文](pipeline-debug-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# pipeline-debug

Cuando el código falla o da un resultado incorrecto, rastrea el fallo hacia atrás a lo largo del pipeline en lugar de parchear la línea donde apareció.

## Úsala en Claude

Di «Encuentra la causa de este error». `skill-match` nombra la skill para errores, tracebacks y ejecuciones fallidas.

## Qué hace

1. Traza un mapa de las etapas por las que pasaron los datos.
2. Comprueba qué entró y qué salió de cada etapa (recuentos, columnas, algunos valores reales) frente a lo que se esperaba.
3. La primera etapa cuya salida está mal es la causa; el error suele aparecer más adelante.
4. Reproduce el fallo en esa etapa, lo fija con una comprobación que falla, lo corrige ahí y vuelve a ejecutar todas las etapas posteriores.

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `probe.py [--rows N] FILE ...` | Muestra filas, columnas, celdas vacías y las primeras líneas de un archivo que pasa de una etapa a otra |

## Límites

Necesita los archivos intermedios; un pipeline que no guarda nada entre etapas tiene que volver a ejecutarse guardándolos.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
