[English](How-it-works.md) · [한국어](How-it-works-ko.md) · [日本語](How-it-works-ja.md) · [中文](How-it-works-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# Cómo funciona

<img src="../../assets/turn-flow.png" alt="Un turno: empieza la sesión, llega un mensaje, se escriben archivos, se ejecuta Bash, termina la respuesta. En cada momento se ejecutan sus hook gates." width="100%" />

## Skills, hook gates y la wiki

<img src="../../assets/parts.png" alt="Tu mensaje llega a Claude Code, que lee skills, pasa por los hook gates y guarda lo que aprende en la wiki." width="100%" />

- **Las skills** dicen cómo se hace un trabajo. Claude Code carga una skill cuando la conversación encaja con su
  descripción. Esa coincidencia la decide el propio modelo, así que no está garantizada.
- **Los hook gates** se ejecutan en momentos fijos, se acuerde alguien de ellos o no. `skill-match` cierra el
  hueco de arriba: compara cada mensaje con las palabras clave de cada skill y nombra la skill que encaja.
  Las palabras clave están solo en inglés y coreano; en otros idiomas Claude compara él mismo la descripción de la skill.
- **La wiki** guarda lo aprendido, una página por tema, y `wiki-recall` lo recupera.

## Hook gates

| Cuándo | Gate | Qué hace | Devuelve la respuesta |
| --- | --- | --- | --- |
| Empieza la sesión | `session-start` | Muestra el banner | — |
| Llega un mensaje | `wiki-recall` | Adjunta páginas relacionadas de la wiki | — |
| Llega un mensaje | `skill-match` | Nombra la skill que corresponde a este mensaje | — |
| Llega un mensaje | `checklist-start` | Dice dónde escribir la lista de comprobación de esta instrucción | — |
| Se escribe un archivo | `wiki-index-check` | Avisa de una página de la wiki que falta en el índice | — |
| Se escribe un archivo | `wiki-graph` | Vuelve a dibujar el grafo de la wiki | — |
| Se escribe un archivo | `prose-check` | Señala los puntos difíciles de leer en las páginas de la wiki | — |
| Se escribe un archivo | `code-check` | Señala nombres vagos de Python y docstrings que faltan | — |
| Se escribe un archivo | `plan-drift` | Revisa el marco del plan y sus desvíos | — |
| Se ejecuta Bash | `after-bash` | Detecta ediciones de la wiki y commits hechos en la shell | — |
| Termina la respuesta | `wiki-sync` | Pone el grafo al día, sin importar cómo se editaron las páginas | — |
| Termina la respuesta | `answer-check` | Revisa la respuesta: preguntas repetidas, el informe de trabajo, la longitud, la redacción, los términos del campo | una vez |
| Termina la respuesta | `checklist-check` | Comprueba que todos los puntos de la lista de comprobación estén hechos | una vez |

## Cuando se devuelve una respuesta

Dos gates pueden devolver una respuesta a Claude antes de que te llegue: `answer-check` y `checklist-check`.
Claude Code muestra entonces `Stop hook feedback:` con el motivo, y Claude corrige la respuesta o termina
los puntos pendientes. Cada gate lo hace **una vez por turno**; en el segundo intento solo informa de lo que
queda, así que un turno nunca puede entrar en bucle.

## Cuando un gate no puede decidir

Deja pasar el turno. Un gate que fallara rompería todas las sesiones en las que se dispara su evento, así que
todos los gates terminan limpiamente ante una entrada que no entienden.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
