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

## 2. Inferencia de memory_descriptions.md (cuando aplique)

**Por que:** El archivo `historico_actividades.md` contiene notas en lenguaje natural escritas por el usuario. El archivo `memory_descriptions.md` requiere un JSON enriquecido con fechas distribuidas, evidencias concretas y observaciones para actas. La inferencia manual toma 30-60 minutos por bitacora; un agente de IA puede hacerlo en segundos.

**Cuando aplica:** Hay entradas en `contexto/historico_actividades.md` que **NO** tienen la marca `[DILIGENCIADA]`.

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
    "momento_2": {
      "fecha": "DD/MM/AAAA",
      "observaciones_instructor": "<...>",
      "observaciones_aprendiz": "<...>",
      "observaciones_coformador": "<...>",
      "compromisos_mejora": "<...>"
    },
    "momento_3": { ... mismo formato ... }
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

**Restriccion:** Solo llenar `momento_2` si la fecha actual esta dentro de +-7 dias del 22/06/2026. Solo llenar `momento_3` si esta dentro de +-7 dias del 07/10/2026. Si no aplica, dejar el campo vacio.

### Flujo del agente

1. Leer `contexto/historico_actividades.md`.
2. Identificar entradas sin `[DILIGENCIADA]`.
3. Para cada entrada: extraer numero, rango, actividades; distribuir fechas; inferir evidencias; generar objeto JSON.
4. Leer `contexto/memory_descriptions.md` actual.
5. Hacer merge: mantener bitacoras ya diligenciadas, agregar/actualizar las nuevas.
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

Regenera archivos del proyecto desde cero. Util cuando algo se corrompe o se quiere empezar de nuevo.

```bash
uv run python scripts/reset.py --all         # Todo excepto .env
uv run python scripts/reset.py --templates   # Solo plantillas
uv run python scripts/reset.py --context     # Solo contexto
uv run python scripts/reset.py --env         # Solo .env
uv run python scripts/reset.py --all --include-env  # Todo incluyendo .env
```

Las plantillas se descargan desde GitHub. Si falla, busca un backup local. Si todo falla, sugiere clonar el repositorio.
