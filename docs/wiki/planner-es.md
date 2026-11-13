[English](planner.md) · [한국어](planner-ko.md) · [日本語](planner-ja.md) · [中文](planner-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# planner

Planifica un proyecto como lo planifica su campo, mantiene conectados los objetivos a largo, medio y corto plazo, y avisa del trabajo que se desvía del plan.

## Úsala en Claude

Di «Planifícalo con el planner» o «Escribe una hoja de ruta para X». `skill-match` nombra la skill en las peticiones de planificación.

## Qué hace

1. Primero fija el marco: qué campo (estrategia de negocio, servicio y web, UI/UX, producto, contenido, software, publicidad, producción y calidad), qué horizonte, qué nivel.
2. Después trabaja en orden: investiga el problema, fija objetivos, prueba la viabilidad, define las funciones, escribe requisitos y especificaciones, diseña flujos y wireframes, y fija el calendario con los equipos relacionados (interpretados por subagentes).
3. Los objetivos se numeran `L1` → `M1.2` → `S1.2.3`, así que una tarea sin padre se detecta de forma mecánica.
4. El trabajo se anota como `- [YYYY-MM-DD] S1.1.1 …`; el trabajo fuera del plan lleva `(계획 밖)` («fuera del plan») y el motivo, y un objetivo terminado lleva `완료` («completado») o `done`. La revisión de desvíos busca exactamente `(계획 밖)`.

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `check_plan.py <plan.md>` | Señala secciones que faltan, objetivos sin padre o sin meta, y funciones sin objetivo |
| `check_drift.py <plan.md>` | Señala trabajo fuera del plan no declarado, objetivos vencidos y objetivos a largo plazo que nadie ha tocado |

La plantilla del plan es `assets/plan-template.md`; la guía de campos es `references/domains.md`.

## Hooks que la respaldan

`plan-drift` revisa un plan cuando se escribe, y `after-bash` revisa los desvíos después de cada commit. Los dos informan y nunca bloquean.

## Límites

Los desvíos se juzgan a partir del registro de progreso y de los mensajes de commit; el trabajo que no deja rastro no se ve.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
