<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — skills y hook gates para Claude Code, instalados juntos. Dos comandos de instalación y el banner que aparece al reiniciar." width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />

[English](../../README.md) · [한국어](../ko-KR/README.md) · [日本語](../ja-JP/README.md) · [简体中文](../zh-CN/README.md) · **Español**

[Instalación](#instalación) · [Primeros pasos](#primeros-pasos) · [Contenido](#contenido) · [Novedades](#novedades)

</div>

<br />

## De un vistazo

Claude Code olvida lo que aprendió cuando termina una conversación, y en una conversación larga se aleja de reglas como «escríbelo sencillo».

kl-skills guarda lo que Claude aprende en una wiki y lo recupera en conversaciones posteriores. Las reglas van en hooks que revisan cada respuesta.

<img src="../../assets/turn-flow.png" alt="Un turno: empieza la sesión, llega un mensaje, se escriben archivos, se ejecuta Bash, termina la respuesta. En cada momento se ejecutan sus hook gates." width="100%" />

| Incluye | Cantidad | Qué hace |
| --- | --: | --- |
| Skills | 9 | Wiki, respuestas claras, reglas de código, planificación, depuración, investigación bibliográfica |
| Hook gates | 9 | Revisión de respuestas, mantenimiento de la wiki, revisión de textos y código, desvíos del plan |

<br />

## Instalación

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

Reinicia la sesión. La primera línea debería decir:

```
KL-SKILLS GATES v<version> — loaded, 9 rules enforced
```

> [!IMPORTANT]
> La mayoría de los gates están escritos en Python. Sin `python3`, se omiten en silencio.

> [!NOTE]
> Los mensajes de los gates y las reglas de escritura están pensados primero para el coreano. En español solo se revisan siglas sin definir y frases demasiado largas.

**Actualizar** — `claude plugin marketplace update kl-skills`, luego `claude plugin update kl-skills@kl-skills`, y reinicia.<br />
**Desinstalar** — `claude plugin uninstall kl-skills@kl-skills`. Tu wiki en `~/llm-wiki-docs/` se conserva.

<br />

## Primeros pasos

Empieza por lo que quieres hacer. Una skill se carga cuando la conversación encaja con ella; también puedes nombrarla.

| Quieres | Di | Skill |
| --- | --- | --- |
| Guardar lo que aprendiste | «Pon esto en la wiki» | `llm-wiki-docs` |
| Usar lo que sabe la wiki | nada — cada mensaje se compara con la wiki | `wiki-recall` |
| Ver toda la wiki | «Muéstrame el grafo de la wiki» | `graph-doc-memory` |
| Investigar una pregunta | «Investiga si X causa Y» | `research-to-wiki` |
| Planificar un proyecto | «Planifícalo con el planner» | `planner` |
| Encontrar por qué algo falló | «Encuentra la causa de este error» | `pipeline-debug` |
| Escribir código | nada — se aplican las reglas de nombres, comentarios y no hardcoding | `readable-code` · `no-hardcoding` |

Cuando un gate bloquea una respuesta, Claude Code muestra `Stop hook feedback:` con el motivo, y Claude reescribe la respuesta. Solo `answer-check` bloquea, y solo una vez por turno.

<br />

## Contenido

<img src="../../assets/parts.png" alt="Tu mensaje llega a Claude Code, que lee skills, pasa por los hook gates y guarda lo que aprende en la wiki." width="100%" />

### Skills

| Skill | Qué hace |
| --- | --- |
| `llm-wiki-docs` | Guarda lo que aprendes en una wiki, una página por tema |
| `wiki-recall` | Busca páginas relacionadas de la wiki y las usa en la respuesta |
| `graph-doc-memory` | Dibuja toda la wiki como un grafo en el navegador |
| `research-to-wiki` | Registra la investigación con el tipo de estudio de cada fuente y cuánto se leyó |
| `natural-answering` | Escribe sin saltarse términos, puntos de comparación ni el paso hasta la conclusión |
| `readable-code` | Los nombres dicen qué contienen; los comentarios, por qué |
| `no-hardcoding` | Mantiene listas, rutas y umbrales fuera del código |
| `pipeline-debug` | Busca la primera etapa que falló, no la línea que dio el error |
| `planner` | Planifica según el campo y el horizonte, y avisa del trabajo que se desvía del plan |

### Hook gates

| Cuándo | Gate | Qué hace |
| --- | --- | --- |
| Empieza la sesión | `session-start` | Muestra el banner |
| Llega un mensaje | `wiki-recall` | Adjunta páginas relacionadas de la wiki |
| Se escribe un archivo | `wiki-index-check` | Avisa de una página de la wiki que falta en el índice |
| Se escribe un archivo | `wiki-graph` | Vuelve a dibujar el grafo de la wiki |
| Se escribe un archivo | `prose-check` | Señala los puntos difíciles de leer en las páginas de la wiki |
| Se escribe un archivo | `code-check` | Señala nombres vagos de Python y docstrings que faltan |
| Se escribe un archivo | `plan-drift` | Revisa el marco del plan y sus desvíos |
| Se ejecuta Bash | `after-bash` | Detecta ediciones de la wiki y commits hechos en la shell |
| Termina la respuesta | `wiki-sync` | Pone el grafo al día, sin importar cómo se editaron las páginas |
| Termina la respuesta | `answer-check` | Revisa la respuesta y la bloquea una vez si hace falta |

<br />

## Novedades

De 0.17 a 0.20 salieron el 2026-11-11, y 0.21 el 2026-11-12. Historial completo: `git log`.

- **0.21** — las skills de mantenimiento (`plugin-release`, `hook-replay`) salieron del plugin; README en cinco idiomas
- **0.20** — un turno que cambió archivos debe terminar con un informe de trabajo en seis pasos
- **0.19** — `hook-replay`, `plugin-release` y `research-to-wiki`
- **0.18** — bloquea solo cuando de verdad volviste a preguntar; desvíos del plan y búsqueda en la wiki
- **0.17** — `planner`

<br />

## Requisitos

| Necesita | Para | Sin ello |
| --- | --- | --- |
| `python3` | la mayoría de los gates y todos los scripts de las skills (solo biblioteca estándar) | esos gates se omiten en silencio |
| `git` | la revisión de desvíos del plan | esa revisión se omite |

Los gates precompilados vienen para macOS (Apple silicon e Intel), Linux (x86_64 y ARM, también WSL) y Windows (x86_64). En cualquier otro sistema, los gates dejan pasar en silencio.

<br />

## Seguridad

- Los gates y los scripts de las skills no usan la red.
- La wiki, su grafo y tus planes se quedan en tu equipo.
- Cuando un gate no puede decidir, deja pasar el turno.

<br />

## Desarrollo

Publicar cambios, probar hooks con conversaciones reales, el contrato de salida de los hooks y el mapa de archivos: [docs/DEVELOPMENT.md](../DEVELOPMENT.md) (en inglés).

## Licencia

MIT
