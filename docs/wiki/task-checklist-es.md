[English](task-checklist.md) · [한국어](task-checklist-ko.md) · [日本語](task-checklist-ja.md) · [中文](task-checklist-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# task-checklist

Convierte cada instrucción en una lista de comprobación antes de trabajar, y solo termina cuando cada punto está hecho o cerrado con un motivo.

## Úsala en Claude

No hace falta decir nada: el gate `checklist-start` pide una lista de comprobación con cada mensaje.

## Qué hace

1. Lee el mensaje entero: puntos numerados, peticiones escondidas en las frases, decisiones que ya tomaste.
2. Lo divide en puntos que se pueden comprobar: «los tests pasan» en lugar de «mejorar los tests». Una pregunta del mensaje también es un punto.
3. Los escribe en la lista de comprobación de la sesión, uno por línea: `- [ ] item`.
4. Marca cada punto como `- [x]` en cuanto está hecho; uno que no se puede hacer se cierra como `- [~] item — reason`.
5. Antes de terminar, vuelve a abrir la lista y acaba lo que siga en `- [ ]`.

## Archivos y scripts

```text
~/.claude/checklists/<session>.md        this instruction's list
~/.claude/checklists/<session>.prev.md   the previous instruction's list, kept
```

`KL_CHECKLIST_DIR` mueve la carpeta.

## Hooks que la respaldan

`checklist-start` aparta la lista anterior y dice dónde escribir la nueva. `checklist-check` devuelve la respuesta una vez si falta la lista o si tiene puntos pendientes.

## Límites

El gate ve si los puntos están marcados, no si el trabajo detrás de la marca se hizo bien.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
