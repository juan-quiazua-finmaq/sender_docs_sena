# AGENTS.md — Instrucciones para Agentes de IA

## Proposito del Proyecto

Este proyecto automatiza el diligenciamiento de bitacoras (formato Excel) y actas de seguimiento/evaluacion (formato Word) requeridas por el SENA para la etapa productiva del aprendiz. El agente de IA infiere descripciones de actividades a partir de notas en lenguaje natural, genera los documentos oficiales y envia un correo al instructor con los archivos adjuntos.

## Flujo de Ejecucion

```
0. (Opcional) Ejecutar doctor.py para verificar el estado del proyecto
   |
1. Validar entorno (.env)
   |
2. Inferir memory_descriptions.md (si hay bitacoras nuevas sin [DILIGENCIADA])
   |
3. Confirmar mensaje_instructor.md (plantilla del correo)
   |
4. Ejecutar diligenciar.py --ai-mode
```

Si cualquiera de estos pasos falla por datos faltantes o invalidos, el agente debe **detenerse y pedir clarificacion al usuario antes de continuar**. Nunca debe inventar valores, direcciones de correo o descripciones de actividades.

---

## 1. Validacion del Entorno (.env)

**Por que:** El script envia correos reales usando credenciales de Gmail. Si `.env` esta incompleto, el envio fallara y podria bloquear la cuenta.

**Comando:**

```bash
uv run python scripts/setup.py --ai-mode
```

**Interpretacion del output (stdout JSON):**

- `status: "ok"` -> entorno completo, continuar al paso 2.
- `status: "incomplete"` -> faltan variables. El JSON incluye:
  - `path`: ruta del archivo .env
  - `missing`: lista de variables con `variable`, `description`, `example`, `secret`

**Accion del agente cuando incomplete:**

1. Leer el array `missing` del JSON.
2. Para cada variable: mostrar al usuario descripcion + ejemplo. Si `secret=true`, no mostrar valores en pantalla al re-imprimir.
3. Preguntar el valor al usuario.
4. Escribir los valores en `.env` (sin sobrescribir a ciegas; editar/append).
5. Re-ejecutar `uv run python scripts/setup.py --ai-mode`.
6. Repetir hasta `status: "ok"`.
7. Si tras 3 intentos sigue incompleto, pedir al usuario que ejecute manualmente `python scripts/setup.py` (wizard).

**Reglas de seguridad:**

- NUNCA imprimir valores de variables con `secret=true` en pantalla ni en logs.
- NUNCA escribir el password en un archivo distinto a `.env`.
- SIEMPRE validar formato (email valido, password 16 chars) antes de escribir.

**Exit codes:** 0 = ok, 1 = incomplete (ver JSON en stdout).

---

## 2. Inferencia de memory_descriptions.md (bitacoras y contenido de actas)

**Por que:** El archivo `historico_actividades.md` contiene notas en lenguaje natural escritas por el usuario. El archivo `memory_descriptions.md` requiere un JSON enriquecido con fechas distribuidas, evidencias concretas y observaciones para actas. La inferencia manual toma 30-60 minutos por bitacora; un agente de IA puede hacerlo en segundos.

**Cuando aplica:** Hay entradas en `contexto/historico_actividades.md` que **NO** tienen la marca `[DILIGENCIADA]`.

**Ademas:** Se debe verificar que la seccion `actas.momento_1` exista en el JSON. Si no existe, debe inferirse el contenido a partir de TODAS las bitacoras (ver seccion 2b mas abajo).

**Estructura esperada del JSON** (dentro del bloque ` ```json ... ``` ` de `contexto/memory_descriptions.md`):

```json
{
  "bitacoras": [
    {
      "numero": <int>,
      "fecha_inicio": "DD/MM/AAAA",
      "fecha_fin": "DD/MM/AAAA",
      "actividades": [
        {
          "descripcion": "<texto original o ligeramente enriquecido>",
          "fecha_inicio": "DD/MM/AAAA",
          "fecha_fin": "DD/MM/AAAA",
          "evidencia": "<evidencia concreta inferida>"
        }
      ]
    }
  ],
  "actas": {
    "momento_1": {
      "resultados_aprendizaje": "<string - competencias desarrolladas consolidadas de TODAS las bitacoras>",
      "actividades_desarrollar": "<string - actividades realizadas consolidadas de TODAS las bitacoras>",
      "evidencias_aprendizaje": "<string - evidencias concretas consolidadas de TODAS las bitacoras>",
      "observaciones_adicionales": "<string - resumen positivo general del desempeno>"
    },
    "momento_2": {
      "fecha": "DD/MM/AAAA",
      "observaciones_instructor": "(opcional - no implementado en script, se rellena manualmente por el instructor en Paragraph 14)",
      "observaciones_aprendiz": "<string - primera persona, reflexivo, menciona logros>",
      "observaciones_coformador": "<string - tercera persona, evalua actitud, positivo>",
      "compromisos_mejora": "<string - DEPRECADO: ver seccion 2c. Se mantiene como fallback si valoraciones[] no esta presente>",
      "valoraciones": [
        {
          "variable": "Gestion de conocimiento",
          "categoria": "tecnico",
          "observacion": "<string - 1-2 frases, tono positivo, evidencia concreta del historico>"
        }
      ]
    },
    "momento_3": {
      "fecha": "DD/MM/AAAA",
      "observaciones_instructor": "<string - tercera persona, evalua desempeno, positivo>",
      "observaciones_aprendiz": "<string - primera persona, reflexivo, menciona logros>",
      "observaciones_coformador": "<string - tercera persona, evalua actitud, positivo>",
      "compromisos_mejora": "<string - DEPRECADO: ver seccion 2c. Se mantiene como fallback si valoraciones[] no esta presente>",
      "valoraciones": [
        {
          "variable": "Gestion de conocimiento",
          "categoria": "tecnico",
          "observacion": "<string - 1-2 frases, tono positivo, evidencia concreta del historico>"
        }
      ]
    }
  }
}
```

### Reglas de inferencia

#### Distribucion de fechas por actividad

El rango de la bitacora es `fecha_inicio` a `fecha_fin` (15 dias tipicamente). Cada actividad debe recibir un sub-rango continuo **sin solapamientos** y **sin huecos**, distribuyendo los dias proporcionalmente al orden de las actividades.

Ejemplo para 5 actividades entre 08/04/2026 y 22/04/2026 (15 dias, 3 dias c/u):

```
Actividad 1: 08/04/2026 al 10/04/2026
Actividad 2: 11/04/2026 al 13/04/2026
Actividad 3: 14/04/2026 al 16/04/2026
Actividad 4: 17/04/2026 al 19/04/2026
Actividad 5: 20/04/2026 al 22/04/2026
```

Reglas:
- El primer sub-rango empieza en `fecha_inicio` de la bitacora.
- El ultimo sub-rango termina en `fecha_fin` de la bitacora.
- Si el numero de actividades no divide exacto los dias, los dias sobrantes se agregan al primer sub-rango.
- Minimo 1 dia por actividad.

#### Generacion de evidencia

La evidencia debe ser **concreta y verificable**, no generica. Ejemplos:

| Actividad (historico) | Evidencia mala (no usar) | Evidencia buena |
|---|---|---|
| estudio Python | "Estudio de Python" | "Estructuras de clases en Python y prototipo basico de endpoints con FastAPI." |
| aprendio AWS | "Conocimientos de AWS" | "Resumen conceptual de servicios principales (EC2, S3, RDS) y diagramas basicos." |
| se le asigno lambda | "Desarrollo de lambda" | "Propuesta y diseno del flujo automatizado para el requerimiento de TI." |

Tono recomendado: impersonal, tecnico, conciso (1-2 oraciones por evidencia).

#### Generacion de observaciones (actas)

- `observaciones_aprendiz`: primera persona, reflexivo, menciona logros tecnicos especificos del periodo.
- `observaciones_instructor` y `observaciones_coformador`: tercera persona, evalua desempeno y actitud.
- `compromisos_mejora`: 1-2 sugerencias de mejora concretas y accionables.

**Restriccion (fechas configurables):** Las fechas objetivo de los momentos se controlan por .env:
- `ACTA_M1_FECHA` (default: 2026-04-08) - Momento 1 (Planeacion).
- `ACTA_M2_FECHA` (default: 2026-06-22) - Momento 2 (Seguimiento).
- `ACTA_M3_FECHA` (default: 2026-10-07) - Momento 3 (Evaluacion).
- `ACTA_VENTANA_DIAS` (default: 7) - tolerancia en dias antes/despues de la fecha objetivo.

Solo llenar `momento_1` si la fecha actual esta dentro de la ventana de `ACTA_M1_FECHA`. Solo llenar `momento_2` si esta dentro de la ventana de `ACTA_M2_FECHA`. Solo llenar `momento_3` si esta dentro de la ventana de `ACTA_M3_FECHA`. Si no aplica, dejar el campo vacio.

#### Inferencia de contenido para actas (momento_1, momento_2, momento_3)

Ademas de inferir bitacoras, el agente debe inferir el contenido de los tres momentos del acta a partir del historico de actividades y las bitacoras existentes.

**Momento 1 (Planeacion) - Tabla 2, filas 6-9:**

Cuando la fecha actual este dentro de la ventana de `ACTA_M1_FECHA`, inferir:

| Campo en JSON | Campo en Acta | Como inferirlo |
|---------------|---------------|---------------|
| `actas.momento_1.resultados_aprendizaje` | Tabla 2 R6 | Consolidar TODAS las competencias tecnicas desarrolladas a lo largo de todas las bitacoras (1, 2, 3, ..., N). Listar tecnologias, frameworks, conceptos aprendidos. |
| `actas.momento_1.actividades_desarrollar` | Tabla 2 R7 | Listar las actividades realizadas en TODAS las bitacoras como texto corrido y numerado. Usar el campo `descripcion` de cada actividad en `bitacoras[].actividades[]`. |
| `actas.momento_1.evidencias_aprendizaje` | Tabla 2 R8 | Consolidar TODAS las evidencias de `bitacoras[].actividades[].evidencia` en un texto corrido. |
| `actas.momento_1.observaciones_adicionales` | Tabla 2 R9 | Resumen positivo general del desempeno del aprendiz: proactividad, cumplimiento, adaptacion, actitud. 2-3 oraciones. |

**Momento 2 (Seguimiento) - Tabla 3 + Paragraphs 14, 17, 20:**

Cuando la fecha actual este dentro de la ventana de `ACTA_M2_FECHA`, inferir/verificar:

| Campo en JSON | Ubicacion en Word | Como inferirlo |
|---------------|-------------------|---------------|
| `actas.momento_2.valoraciones[]` | Tabla 3, R6-R9 C6 (tecnicas) y R17-R21 C6 (actitudinales) | **FUENTE PRIMARIA.** Array de 9 objetos (4 tecnicos + 5 actitudinales). Cada entrada genera el texto de su celda "Observaciones / Compromisos de mejora" individual. Ver seccion 2c para esquema, mapeo y reglas de inferencia. |
| `actas.momento_2.compromisos_mejora` | Tabla 3, R6C6 y R17C6 (fallback) | **DEPRECADO.** Solo se usa si `valoraciones[]` no esta presente o esta vacio. Escribe el mismo texto en la primera fila tecnica y actitudinal. 1-2 compromisos positivos y accionables. Formato: "1. ... 2. ..." |
| `actas.momento_2.observaciones_aprendiz` | Paragraph 17 | Primera persona, reflexivo. Mencionar logros tecnicos especificos del periodo. |
| `actas.momento_2.observaciones_coformador` | Paragraph 20 | Tercera persona, evalua dedicacion, integracion al equipo, responsabilidad. Tono positivo. |

> **Nota:** `observaciones_instructor` (Paragraph 14) **no** se diligencia automaticamente. El script omite este campo para que el instructor lo complete manualmente, respetando la regla de no hardcodear contenido academico sensible. El campo puede incluirse en el JSON si se desea, pero el script lo ignorara al generar el Word.

**Momento 3 (Evaluacion Final) - Tabla 5 + Tablas 6, 7, 8:**

Cuando la fecha actual este dentro de la ventana de `ACTA_M3_FECHA`, inferir/verificar:

| Campo en JSON | Ubicacion en Word | Como inferirlo |
|---------------|-------------------|---------------|
| `actas.momento_3.valoraciones[]` | Tabla 5, R6-R9 C6 (tecnicas) y R17-R21 C6 (actitudinales) | **FUENTE PRIMARIA.** Array de 9 objetos (4 tecnicos + 5 actitudinales). Cada entrada genera el texto de su celda "Observaciones / Compromisos de mejora" individual. Ver seccion 2c para esquema, mapeo y reglas de inferencia. |
| `actas.momento_3.compromisos_mejora` | Tabla 5, R6C6 y R17C6 (fallback) | **DEPRECADO.** Solo se usa si `valoraciones[]` no esta presente o esta vacio. Escribe el mismo texto en la primera fila tecnica y actitudinal. 1-2 compromisos positivos y accionables. Formato: "1. ... 2. ..." |
| `actas.momento_3.observaciones_aprendiz` | Tabla 8, R2C1 | Primera persona, reflexivo, logros tecnicos del periodo completo. |
| `actas.momento_3.observaciones_instructor` | Tabla 7 | Tercera persona, evalua desempeno y actitud. Tono positivo. |
| `actas.momento_3.observaciones_coformador` | Tabla 6 | Tercera persona, evalua dedicacion, integracion, responsabilidad. Tono positivo. |

**Reglas de tono y formato (OBLIGATORIO):**

1. **Tono POSITIVO:** Nunca escribir algo negativo. Todo debe ser favorable.
2. **Tercera persona para instructor/co-formador:** "El aprendiz demuestra...", "El aprendiz muestra...", "Muestra dedicacion...", "Se integra..."
3. **Primera persona para aprendiz:** "Durante el periodo he desarrollado...", "He logrado...", "He fortalecido..."
4. **Compromisos positivos y accionables:** Siempre en formato "1. [verbo infinitivo]..." (ejemplo: "1. Documentar...", "2. Profundizar...")
5. **NO hardcodear:** NO usar textos genericos de ejemplo. El contenido debe basarse en las actividades REALES del `historico_actividades.md`.
6. **Consolidar todo el periodo:** Para Momento 1 y Momento 3, usar TODAS las bitacoras, no solo la mas reciente.
7. **Longitud:** 2-4 oraciones por campo. Conciso pero sustantivo.

**Ejemplo de inference (no usar como plantilla literal, solo como referencia de tono):**

Input (historico):
```
## Bitacora numero 1 - (08/04/2026 al 22/04/2026)
- Familiarizacion con estructura de la empresa
- Estudio de stack tecnologico
```

Output valido para `momento_1.resultados_aprendizaje`:
> "El aprendiz desarrollo competencias en familiarizacion con entornos empresariales, comprension del stack tecnologico de la empresa y adaptacion a la cultura organizacional."

Output NO valido (negativo):
> "El aprendiz tuvo dificultades para adaptarse al stack tecnologico."

### Flujo del agente

1. Leer `contexto/historico_actividades.md`.
2. Identificar entradas sin `[DILIGENCIADA]`.
3. Para cada entrada: extraer numero, rango, actividades; distribuir fechas; inferir evidencias; generar objeto JSON.
4. Leer `contexto/memory_descriptions.md` actual.
5. Hacer merge: mantener bitacoras ya diligenciadas, agregar/actualizar las nuevas.
5b. Verificar/Completar la seccion `actas`:
    - Si `actas.momento_1` no existe o esta vacio, inferir contenido a partir de TODAS las bitacoras (ver seccion 2b).
    - Si la fecha actual esta en la ventana de M2 y `actas.momento_2` tiene campos vacios, inferirlos.
    - Si la fecha actual esta en la ventana de M3 y `actas.momento_3` tiene campos vacios, inferirlos.
6. Mostrar al usuario el JSON propuesto.
7. Preguntar: "Esta de acuerdo con el JSON propuesto? (s/n) Si no, indique que cambiar."
8. Si acepta: escribir el archivo.
9. Si rechaza: iterar con las correcciones.

### Plantillas de evidencia por dominio

- **Empresa/Stack**: "Resumen tecnico de la infraestructura de desarrollo y stack seleccionado."
- **Repos**: "Credenciales y claves SSH configuradas para repositorios de control de versiones."
- **Seguridad**: "Certificacion de lectura y aceptacion de politicas de seguridad corporativas."
- **AWS**: "Resumen conceptual de servicios principales (EC2, S3, RDS) y diagramas basicos."
- **Python**: "Estructuras de clases en Python y prototipo basico de endpoints con FastAPI."
- **Arquitectura**: "Esquema conceptual de arquitectura limpia y principios SOLID analizados."
- **Automatizacion**: "Propuesta y diseno del flujo automatizado para el requerimiento de TI."
- **Datos (DuckDB, polars)**: "Scripts de consulta en DuckDB y manipulacion de DataFrames utilizando Polars."
- **SDD**: "Documento borrador de especificacion del estandar SDD preparado."
- **Lambda/ETL**: "Prototipo funcional de la lambda con pipeline ETL implementado y probado en entorno staging."

### 2.1 Advertencia: Catch-up de actas

> **IMPORTANTE:** El script implementa logica de "catch-up": si al momento de ejecutar la fecha actual cae en la ventana del Momento 2 o 3, y hay actas de momentos anteriores (Momento 1) que no han sido enviadas, el script las enviara tambien. El estado de envio se persiste en `contexto/actas_enviadas.json`.

Ademas, el script genera UN SOLO archivo de Word (`Actas-Inicio-Medio-Final.docx`) que contiene los tres momentos. Si ya se envio el momento 1 y luego se requiere el momento 2, el script toma el mismo archivo plantilla, diligencia los campos faltantes del momento 2 (y momento 3 si aplica), y guarda el archivo actualizado. Esto significa que el JSON en `memory_descriptions.md` debe contener TODOS los campos de los tres momentos, no solo los del momento actual.

Si cambia las fechas en `.env` (`ACTA_M*_FECHA` o `ACTA_VENTANA_DIAS`), **primero revise `actas_enviadas.json`** para confirmar que el catch-up no enviara actas que usted no espera. Para forzar un reenvio de un momento especifico sin catch-up (es decir, sin enviar los momentos anteriores no enviados), edite manualmente el archivo `actas_enviadas.json` cambiando `enviada: false` en el momento deseado. Alternativamente, `--force-moment N` SI activa el catch-up — es decir, `--force-moment 3` enviara los Momentos 1, 2 y 3 si ninguno ha sido enviado.

### 2c. Observaciones por variable (Tabla de Valoracion M2/M3)

#### Problema actual

El script `diligenciar.py` escribe el campo `compromisos_mejora` (un unico string) solamente en la **primera fila tecnica** (fila 6) y la **primera fila actitudinal** (fila 17) de la Tabla de Valoracion. Esto deja **7 de las 9 variables** con la celda "Observaciones / Compromisos de mejora" completamente vacia en el Word generado:

| Filas diligenciadas | Filas vacias |
|---------------------|--------------|
| Fila 6 (tecnica) | Filas 7, 8, 9 (tecnicas) |
| Fila 17 (actitudinal) | Filas 18, 19, 20, 21 (actitudinales) |

La solucion es reemplazar el string unico `compromisos_mejora` por un array `valoraciones[]` de 9 objetos, uno por cada variable evaluada, de modo que cada celda del Word reciba su propio texto contextualizado.

#### Esquema JSON canonico

El array `valoraciones[]` se agrega dentro de `momento_2` y `momento_3` en el JSON de `memory_descriptions.md`. Debe contener exactamente **9 entradas** por momento, en el mismo orden de las filas del Word:

```json
"actas": {
  "momento_2": {
    "fecha": "DD/MM/AAAA",
    "observaciones_instructor": "",
    "observaciones_aprendiz": "...",
    "observaciones_coformador": "...",
    "compromisos_mejora": "(deprecado - fallback si valoraciones[] ausente)",
    "valoraciones": [
      { "variable": "Gestion de conocimiento",            "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Creatividad y calidad",              "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Administracion de recursos",         "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Seguridad y salud en el trabajo",    "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Trabajo en equipo",                  "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Relaciones interpersonales",         "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Solucion de problemas",              "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Cumplimiento",                       "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Organizacion",                       "categoria": "actitudinal", "observacion": "..." }
    ]
  },
  "momento_3": {
    "fecha": "DD/MM/AAAA",
    "observaciones_instructor": "...",
    "observaciones_aprendiz": "...",
    "observaciones_coformador": "...",
    "compromisos_mejora": "(deprecado - fallback si valoraciones[] ausente)",
    "valoraciones": [
      { "variable": "Gestion de conocimiento",            "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Creatividad y calidad",              "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Administracion de recursos",         "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Seguridad y salud en el trabajo",    "categoria": "tecnico",     "observacion": "..." },
      { "variable": "Trabajo en equipo",                  "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Relaciones interpersonales",         "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Solucion de problemas",              "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Cumplimiento",                       "categoria": "actitudinal", "observacion": "..." },
      { "variable": "Organizacion",                       "categoria": "actitudinal", "observacion": "..." }
    ]
  }
}
```

> **Nota de orden:** El orden del array **debe** ser: filas 6, 7, 8, 9 (tecnicas) seguido de filas 17, 18, 19, 20, 21 (actitudinales). No se incluye un campo `orden` explicito; el indice del array (0-8) determina la posicion. Esto simplifica el esquema y evita redundancia.

#### Mapeo variable -> fila del Word

| Indice | Variable | Categoria | Fila Word (Tabla 3 M2 / Tabla 5 M3) | Celda |
|--------|----------|-----------|--------------------------------------|-------|
| 0 | Gestion de conocimiento | tecnico | 6 | C6 |
| 1 | Creatividad y calidad | tecnico | 7 | C6 |
| 2 | Administracion de recursos | tecnico | 8 | C6 |
| 3 | Seguridad y salud en el trabajo | tecnico | 9 | C6 |
| 4 | Trabajo en equipo | actitudinal | 17 | C6 |
| 5 | Relaciones interpersonales | actitudinal | 18 | C6 |
| 6 | Solucion de problemas | actitudinal | 19 | C6 |
| 7 | Cumplimiento | actitudinal | 20 | C6 |
| 8 | Organizacion | actitudinal | 21 | C6 |

#### Especificacion de inferencia (texto del usuario)

> **Objetivo:** Generar la observacion del campo "Observaciones / Compromisos de mejora" usando las actividades y evidencias del aprendiz (docx).
>
> **Entrada:**
> - Variable evaluada.
> - Categoria: Factor tecnico / Factor actitudinal.
> - Actividades realizadas del historico.
> - Evidencias disponibles.
>
> **Reglas:**
> - La valoracion siempre sera: Satisfactorio.
> - Generar texto breve (1-2 frases).
> - Relacionar la variable con actividades reales realizadas.
> - Usar lenguaje institucional SENA.
> - No inventar actividades no registradas.
> - No repetir observaciones entre variables.
>
> **Plantilla base:**
> *"Demostro desempeno satisfactorio en [variable], evidenciado mediante su participacion en actividades relacionadas con [actividad/evidencia]. Continua fortaleciendo sus competencias tecnicas y profesionales."*
>
> **Ejemplos segun contexto:**
>
> | Variable | Ejemplo de observacion |
> |----------|----------------------|
> | Gestion de conocimiento (tecnico) | "Demostro apropiacion del conocimiento mediante el aprendizaje y aplicacion de tecnologias como AWS, Python, FastAPI y herramientas de datos, fortaleciendo sus competencias tecnicas." |
> | Creatividad y calidad (tecnico) | "Aplico buenas practicas de desarrollo mediante la implementacion de soluciones automatizadas, arquitectura limpia y procesos orientados a mejorar la calidad del software." |
> | Administracion de recursos (tecnico) | "Fortalecio la gestion de recursos tecnologicos mediante el uso de servicios AWS, procesamiento de datos y analisis de arquitecturas orientadas a soluciones empresariales." |
> | Trabajo en equipo (actitudinal) | "Demostro adecuada integracion con el equipo de trabajo, participando en actividades tecnicas y aportando en la construccion de soluciones para requerimientos internos." |
>
> **Salida esperada (por variable):**
> ```json
> {
>   "variable": "Gestion de conocimiento",
>   "observacion": "Demostro apropiacion del conocimiento mediante..."
> }
> ```

#### Reglas de inferencia para `valoraciones[]`

1. **Una observacion unica por variable:** Cada una de las 9 variables debe recibir un texto distinto. Nunca copiar el mismo texto en dos variables.
2. **Longitud:** 1-2 frases (maximo 40 palabras por observacion).
3. **Evidencia concreta:** Cada observacion debe referenciar al menos una actividad o evidencia real del `historico_actividades.md` o de `bitacoras[].actividades[]`. No inventar actividades.
4. **Tono positivo e institucional SENA:** Usar verbos en pasado ("Demostro", "Aplico", "Fortalecio", "Participo"). La valoracion implicita siempre es "Satisfactorio".
5. **No repetir entre momentos:** Si el aprendiz ya tiene una observacion similar en M2, la de M3 debe reflejar progreso o profundizacion (no copiar literal).
6. **Variables tecnicas:** Relacionar con tecnologias, herramientas, frameworks, arquitecturas o estandares concretos que aparezcan en el historico (AWS, Python, FastAPI, DuckDB, Polars, SDD, DAMA, CDC, etc.).
7. **Variables actitudinales:** Relacionar con comportamientos observables: integracion al equipo, puntualidad, proactividad, resolucion de conflictos, organizacion del trabajo.
8. **Variable especial — Seguridad y salud en el trabajo:** Si el historico menciona politicas de seguridad, certificaciones o capacitaciones, usarlas. Si no hay evidencia directa, usar un texto generico institucional ("Cumplio con los lineamientos de seguridad y salud en el trabajo durante la etapa productiva.").

#### Compatibilidad hacia atras (fallback `compromisos_mejora`)

El campo `compromisos_mejora` (string unico) **se mantiene** en el JSON por compatibilidad hacia atras:

- Si `valoraciones[]` **existe y tiene 9 entradas**: el script debe usar cada `observacion` para su celda correspondiente. `compromisos_mejora` se ignora.
- Si `valoraciones[]` **no existe o esta vacio**: el script usa `compromisos_mejora` como fallback (comportamiento actual: escribe el mismo texto en filas 6 y 17).
- Si **ambos** existen pero `valoraciones[]` tiene menos de 9 entradas: rellenar las que faltan con `compromisos_mejora` como valor por defecto.

> **Nota para el agente inferidor:** Cuando genere el JSON para `memory_descriptions.md`, siempre debe incluir `valoraciones[]` con las 9 entradas completas para M2 y M3. El campo `compromisos_mejora` puede dejarse como string vacio si `valoraciones[]` esta completo.

#### Memoria operativa del proceso

Cada nueva bitacora agregada al `historico_actividades.md` amplia el contexto disponible para generar mejores observaciones en futuros formatos. El agente debe considerar **todas** las bitacoras acumuladas (no solo la mas reciente) al inferir las observaciones de cada variable, de modo que el texto refleje la evolucion completa del aprendiz durante la etapa productiva.

---

## 3. Confirmacion de mensaje_instructor.md

**Por que:** El cuerpo del correo electronico es de caracter personal/academico. El agente nunca debe modificarlo sin autorizacion explicita.

**Pasos:**

1. Verificar que existe `contexto/mensaje_instructor.md`. Si no existe: alertar al usuario y sugerir crear uno con la plantilla base (mostrar contenido sugerido).
2. Leer la primera linea despues del separador `---`.
3. Preguntar al usuario: "La plantilla del mensaje al instructor en `contexto/mensaje_instructor.md` es la actual. ¿Desea (a) usarla tal como esta, o (b) editarla primero?"
4. Si (a): continuar al paso 4.
5. Si (b): preguntar el nuevo texto (recordar mantener los placeholders `{{destinatario}}`, `{{lista_bitacoras}}`, `{{acta_moment}}`, `{{firma}}`, `{{fecha_ejecucion}}`); escribir; repetir paso 3.
6. NUNCA modificar sin autorizacion explicita.

Aplica tambien al flujo con CRON.

---

## 4. Ejecucion del Script

**Comando:**

```bash
uv run python scripts/diligenciar.py --ai-mode
```

**Interpretacion del output:**

- Si todo sale bien: el script imprime logs de progreso y envia el correo. El agente debe confirmar al usuario con un resumen breve (bitacoras procesadas, acta generada, correo enviado a X).
- Si falla por entorno (.env incompleto): volver al paso 1.
- Si falla SMTP: el modulo `email_module` ya tiene 3 reintentos automaticos. Si tras 3 intentos sigue fallando, generar `ejecucion.log` y pedir al usuario que revise credenciales.
- Si falla por `memory_descriptions.md` malformado: reparar el JSON (regenerar segun paso 2) y re-ejecutar.

**Exit codes:** 0 = ok, 1 = fallo de validacion de entorno (ver JSON en stdout), otro = fallo de ejecucion (ver `output/<carpeta>/ejecucion.log`).

**Importante:** Tras la ejecucion, el script imprime un bloque `[CHECKLIST MANUAL]` y guarda un archivo `checklist_manual.txt` en la carpeta de cada acta. Este checklist lista los campos que el script NO puede diligenciar automaticamente:
- **Tabla 1 (General):** Regional, Centro de formacion, Programa, datos personales del aprendiz, instructor y co-formador (el usuario debe diligenciarlos manualmente la primera vez o pedirle al agente que le pregunte los valores).
- **Firmas:** Aprendiz, instructor seguimiento, ente co-formador (en Tabla 2 R11 / Tabla 4 / Tabla 9 segun el momento).
- **Enlace de grabacion:** Si la reunion fue virtual, enlace en la celda correspondiente.
Complete esos campos manualmente antes de imprimir o enviar las actas.

Los campos de contenido de las actas (Momento 1 R6-R9, Momentos 2 y 3 - Valoracion X, Compromisos, Retroalimentaciones) son diligenciados automaticamente por el script usando el JSON inferido en `memory_descriptions.md`.

> **Excepcion manual — Paragraph 14 (Momento 2):** La observacion del instructor en el Paragraph 14 del Word **no** se diligencia automaticamente. El script deja este campo vacio para que el instructor lo complete directamente, garantizando que la evaluacion academica sea autentica y no generada por IA.

---

## Estructura del Proyecto

```
sender_docs_sena/
├── scripts/                          # Codigo ejecutable
│   ├── diligenciar.py                # Script principal de automatizacion
│   ├── email_module.py               # Modulo de envio de correo
│   ├── env_validator.py              # Validador de .env (compartido)
│   ├── setup.py                      # Wizard/validador de .env
│   ├── doctor.py                     # Diagnostico completo del proyecto
│   └── reset.py                      # Regeneracion de archivos
├── tests/                            # Suite de pruebas unitarias e integracion
│   ├── test_diligenciar.py
│   ├── test_email_module.py
│   └── test_setup.py
├── contexto/                         # Datos de entrada y plantillas
│   ├── plantillas/                   # Plantillas de documentos (NO TOCAR salvo actualizacion institucional)
│   │   ├── bitacoras.xlsx
│   │   └── actas.docx
│   ├── historico_actividades.md      # Registro manual de actividades
│   ├── memory_descriptions.md        # JSON enriquecido (inferido por IA)
│   └── mensaje_instructor.md         # Plantilla editable del correo al instructor
├── output/                           # Documentos generados (gitignored)
├── .env                              # Variables de entorno (gitignored)
├── .env.example                      # Plantilla de variables de entorno
├── pyproject.toml                    # Dependencias
├── README.md                         # Documentacion principal del usuario
└── instrucciones/
    └── AGENTS.md                     # Este archivo
```

---

## Seguridad

- El archivo `.env` NUNCA debe subirse al repositorio (ya esta en `.gitignore`).
- El password de Gmail NUNCA debe imprimirse en pantalla ni en logs. Los tests verifican esto.
- El agente NUNCA debe inventar valores, direcciones de correo o descripciones. Si falta informacion, debe preguntar al usuario.
- Antes de sobrescribir `.env`, `setup.py` crea un respaldo `.env.backup-<timestamp>`.

---

## Herramientas Auxiliares

### doctor.py

Diagnostico completo del proyecto. Verifica que todo este en orden antes de ejecutar el flujo principal.

```bash
uv run python scripts/doctor.py          # Modo humano (output legible)
uv run python scripts/doctor.py --ai-mode # Modo agente (JSON en stdout)
```

El doctor detecta:
- Variables de entorno faltantes o invalidas
- Archivos de contexto faltantes
- Plantillas faltantes o corruptas
- Placeholders faltantes en el mensaje al instructor
- Bitacoras pendientes

Si el doctor detecta problemas, el agente debe informar al usuario y sugerir las acciones correctivas (que el propio doctor lista en su salida).

### reset.py

Regenera archivos del proyecto desde cero. Util cuando algo se corrompe, se quiere empezar de nuevo, o se prepara el sistema para un primer uso.

**Comandos:**

```bash
uv run python scripts/reset.py --all                # Regenera todo (excepto .env)
uv run python scripts/reset.py --templates          # Solo plantillas (bitacoras.xlsx, actas.docx)
uv run python scripts/reset.py --context            # Solo contexto (historico, memory, mensaje)
uv run python scripts/reset.py --state              # Solo estado de runtime (actas_enviadas.json)
uv run python scripts/reset.py --output             # Solo archivos generados (output/)
uv run python scripts/reset.py --env                # Solo .env (hace backup antes)
uv run python scripts/reset.py --all --include-env  # Todo incluyendo .env
uv run python scripts/reset.py --all --yes          # Sin pedir confirmacion
uv run python scripts/reset.py --all --ai-mode      # Salida JSON para agentes
```

**Que hace cada flag:**

| Flag | Accion |
|------|--------|
| `--templates` | Descarga `bitacoras.xlsx` y `actas.docx` desde GitHub (con fallback a backup local) |
| `--context` | Regenera `historico_actividades.md`, `memory_descriptions.md` y `mensaje_instructor.md` desde templates |
| `--state` | Resetea `contexto/actas_enviadas.json` al estado inicial (todos los momentos en `enviada: false`) |
| `--output` | Elimina todos los archivos y carpetas dentro de `output/` (bitacoras, actas, logs generados) |
| `--env` | Regenera `.env` desde `.env.example` (con backup del actual) |
| `--all` | Equivale a `--templates --context --state --output` (no incluye `.env` a menos que se use `--include-env`) |
| `--yes` | No pide confirmacion al usuario |
| `--ai-mode` | Salida JSON estructurada para que un agente de IA pueda procesarla |

**Flujo de "primer uso" con reset.py:**

Despues de ejecutar `uv run python scripts/reset.py --all --include-env --yes`, el sistema queda en estado de primer uso. El script imprime los siguientes pasos:

```
[OK] Reset completado. El sistema esta listo para un primer uso.

Siguientes pasos para un nuevo usuario:
  1. Configurar el entorno:
     uv run python scripts/setup.py

  2. Llenar el historico de actividades:
     Editar contexto/historico_actividades.md con las actividades realizadas

  3. Inferir el JSON enriquecido:
     Pedirle a un agente de IA que lea instrucciones/AGENTS.md y complete
     contexto/memory_descriptions.md (seccion bitacoras y actas).

  4. Ejecutar el script principal:
     uv run python scripts/diligenciar.py --ai-mode

  5. Verificar con el doctor:
     uv run python scripts/doctor.py
```

Si el reset falla (por ejemplo, no se puede descargar desde GitHub), el script sugiere:
- Clonar el repositorio nuevamente
- Restaurar los archivos manualmente
- Usar `python scripts/reset.py --help` para ver todas las opciones

Las plantillas se descargan desde GitHub. Si falla, busca un backup local. Si todo falla, sugiere clonar el repositorio.
