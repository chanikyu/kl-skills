[English](Installation.md) · [한국어](Installation-ko.md) · [日本語](Installation-ja.md) · [中文](Installation-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# Instalación

## Requisitos

| Necesita | Para | Sin ello |
| --- | --- | --- |
| Claude Code | instala el plugin y ejecuta los hooks | no se instala nada |
| `python3` | la mayoría de los gates y todos los scripts de las skills (solo biblioteca estándar) | esos gates se omiten en silencio |
| `git` | la revisión de desvíos del plan | esa revisión se omite |

Los gates precompilados vienen para macOS (Apple silicon e Intel), Linux (x86_64 y ARM, también WSL) y Windows
(x86_64). En cualquier otro sistema, los gates dejan pasar en silencio.

## Instalar

En Claude Code:

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

La primera línea añade este repositorio como marketplace; la segunda instala el plugin.

## Comprueba que funcionó

Los hooks se cargan cuando empieza una sesión, así que reinicia Claude Code. La primera línea de la nueva sesión debería decir:

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

Si no aparece el banner, los hooks no se están ejecutando. Abre `/plugin` y comprueba que kl-skills está activado.

## Actualizar

```sh
claude plugin marketplace update kl-skills
claude plugin update kl-skills@kl-skills
```

Luego reinicia la sesión.

## Desinstalar

```sh
claude plugin uninstall kl-skills@kl-skills
```

Lo que se queda: tu wiki en `~/llm-wiki-docs/` con su grafo, tus planes y las listas de comprobación en
`~/.claude/checklists/`. Son tuyos, no del plugin.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
