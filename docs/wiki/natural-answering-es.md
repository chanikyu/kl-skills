[English](natural-answering.md) · [한국어](natural-answering-ko.md) · [日本語](natural-answering-ja.md) · [中文](natural-answering-zh.md) · **Español**

[Inicio](Home-es.md) · [Instalación](Installation-es.md) · [Cómo funciona](How-it-works-es.md)

# natural-answering

Escribe respuestas, informes y documentos que el lector puede seguir a la primera, negándose a saltarse los eslabones de la explicación.

## Úsala en Claude

No hace falta decir nada: el gate `answer-check` lee cada respuesta.

## Qué hace

1. Hay ocho cosas que nunca se omiten: el significado de un término donde aparece por primera vez, el paso de un número a la conclusión, con qué se compara un número, por qué se hizo el trabajo, el sujeto de la frase, las unidades en palabras cotidianas, los elementos que hay detrás de un recuento y palabras sencillas para lo que dijo un revisor o una herramienta.
2. La primera frase responde a la pregunta que se hizo.
3. Una respuesta cabe en una pantalla; lo que sea más largo se convierte en un documento con un resumen breve.
4. Después de cambios en el código, un informe sigue seis pasos: resultado, resumen, cambios, verificación, problemas y límites, seguimiento.

## Archivos y scripts

| Script | Qué hace |
| --- | --- |
| `check_prose.py <files>` | Señala términos y siglas sin definir, frases largas y otras omisiones |

Las reglas son datos en `data/`; el informe de trabajo y los esqueletos de documentos están en `references/`.

## Hooks que la respaldan

`answer-check` devuelve una respuesta una vez cuando le falta algo: una pregunta que se vuelve a hacer, un turno que cambió archivos sin el informe de seis pasos, una respuesta de más de una pantalla o hallazgos de redacción. `prose-check` lee las páginas de la wiki.

## Límites

Las revisiones están pensadas primero para el coreano. En los textos en cualquier otro idioma solo se revisan siglas sin definir y frases largas.

---

[kl-skills](../../README.md) · licencia MIT · hecho para [Claude Code](https://claude.com/claude-code)
