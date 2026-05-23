# Automatización de Documentos SENA

Este proyecto automatiza el diligenciamiento de bitácoras (Excel) y actas de seguimiento/evaluación (Word) requeridas por el SENA durante la etapa productiva del aprendiz Manuel Quiazua.

## 1. Propósito del Script

El script `scripts/diligenciar.py` lee dos fuentes de datos en formato Markdown, extrae la información contextual de bitácoras y actas, y genera automáticamente:

- **Bitácoras en Excel** (`BitacoraMQuiazua<N>.xlsx`): Una por cada período de actividades, con metadatos y hasta 7 actividades detalladas.
- **Actas en Word** (`Actas-Inicio-Medio-Final.docx`): Diligencia los momentos 2 (Seguimiento) y 3 (Evaluación Final) con observaciones, marcas de cumplimiento, compromisos de mejora y juicio de evaluación.

El sistema mantiene un registro de qué bitácoras ya fueron procesadas mediante una etiqueta `[DILIGENCIADA]` en el archivo de histórico, permitiendo un flujo de procesamiento por lote.

## 2. Requisitos Previos

- **Python 3.x** (probado en Python 3.12)
- **Dependencias de Python**:
  - `openpyxl` — manipulación de archivos Excel
  - `python-docx` — manipulación de archivos Word

Instalación de dependencias:

```bash
pip install openpyxl python-docx
```

> El proyecto incluye un entorno virtual (`.venv`) con las dependencias ya instaladas.

## 3. Estructura del Proyecto

```
/Docs_SENA/
├── scripts/                          # Código ejecutable
│   ├── diligenciar.py                # Script principal de automatización
│   └── email_module.py               # Módulo de envío de correo
├── tests/                            # Pruebas
│   ├── test_diligenciar.py           # Suite de pruebas unitarias e integración
│   └── test_email_module.py          # Pruebas del módulo de correo
├── contexto/                         # Datos de entrada y plantillas
│   ├── historico_actividades.md      # Bitácoras manuales con estado [DILIGENCIADA]
│   ├── memory_descriptions.md        # Fuente JSON con descripciones inferidas por IA
│   ├── BitacoraMQuiazua1.xlsx        # Plantilla original de bitácora (Excel)
│   ├── BitacoraMQuiazua_template.xlsx# Respaldo automático de plantilla limpia
│   ├── Actas-Inicio-Medio-Final.docx # Plantilla original de actas (Word)
│   └── FirmeManu.png                 # Firma digital del aprendiz
├── instrucciones/                    # Instrucciones para el agente
│   ├── AGENTS.md                     # Reglas de operación del agente líder
│   └── sessions/                     # Historial de sesiones de trabajo
├── output/                           # Archivos generados (raíz)
│   ├── bitacora1-2026-04-08/
│   ├── bitacora2-2026-04-22/
│   └── ...
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── .venv/                            # Entorno virtual Python
```

## 4. Formato de `memory_descriptions.md`

Este archivo contiene un bloque JSON con las descripciones detalladas de cada bitácora y acta. Debe incluir las claves `bitacoras` (lista) y `actas` (objeto).

```json
{
  "bitacoras": [
    {
      "numero": 1,
      "fecha_inicio": "08/04/2026",
      "fecha_fin": "22/04/2026",
      "actividades": [
        {
          "descripcion": "El aprendiz se familiarizo con la estructura general de la empresa",
          "fecha_inicio": "08/04/2026",
          "fecha_fin": "10/04/2026",
          "evidencia": "Organigrama de la organización y documentación de procesos del área de TI."
        }
      ]
    }
  ],
  "actas": {
    "momento_2": {
      "fecha": "08/07/2026",
      "observaciones_instructor": "El aprendiz demuestra gran interés...",
      "observaciones_aprendiz": "He logrado familiarizarme con el stack...",
      "observaciones_coformador": "Manuel muestra excelente actitud...",
      "compromisos_mejora": "Se sugiere reforzar la documentación técnica..."
    },
    "momento_3": {
      "fecha": "08/10/2026",
      "observaciones_instructor": "Desempeño general sobresaliente...",
      "observaciones_aprendiz": "Culmino mi etapa productiva muy satisfecho...",
      "observaciones_coformador": "El aporte de Manuel fue valioso...",
      "compromisos_mejora": "Se recomienda profundizar en pruebas automatizadas..."
    }
  }
}
```

**Claves obligatorias por bitácora:**
- `numero` — identificador numérico de la bitácora
- `fecha_inicio` — fecha de inicio del período (DD/MM/AAAA)
- `fecha_fin` — fecha de fin del período (DD/MM/AAAA)
- `actividades` — lista de objetos con `descripcion`, `fecha_inicio`, `fecha_fin`, `evidencia`

**Claves obligatorias por acta:**
- `fecha` — fecha del acta
- `observaciones_aprendiz` — texto de las observaciones del aprendiz
- `compromisos_mejora` — texto de compromisos (opcional pero recomendado)

## 5. Formato de `historico_actividades.md`

Este archivo es el registro manual de bitácoras. Cada bitácora se define con un encabezado de nivel 2 (`##`) y una lista de actividades. El script detecta automáticamente todas las bitácoras que **no** tengan la etiqueta `[DILIGENCIADA]` y las procesa en un solo lote.

```markdown
# Historico de Actividades Manuel Quiazua

Este es un markdown que se actualiza de manera manual, su unica funcion es alimentar el agente que dilegencia automaticamente cada una de las bitacoras que se deben de presentar al instructor de seguimiento del sena.
---

## Bitacora numero 1 - (08/04/2026 al 22/04/2026) [DILIGENCIADA]
- El aprendiz se familiarizo con la estructura general de la empresa
- El aprendiz estudio profundamente en el stack tecnologico general de la empresa
- El aprendiz tuvo acceso a repositorios internos
- El aprendiz fue instruido en las politicas de seguridad de la empresa
- Se le asigno pequeños ejercicios para comprender el stack tecnologico

## bitacora numero 2 - (22/04/2026 al 06/05/2026)
- Se le indico el plan de aprendizaje para colaborar en los equipos internos de la compañia
- Se oriento al aprendiz en el aprendizaje de conceptos basicos relacionados con AWS
- Se oriento al aprendiz en el aprendizaje de conceptos basicos relacionados con Python
- Se instruyo al aprendiz para realizar aprendizaje sobre arquitecturas de diseño
```

**Reglas del formato:**
- El encabezado debe contener `Bitacora numero <N>` (insensible a mayúsculas/minúsculas).
- La etiqueta `[DILIGENCIADA]` indica que ya fue procesada.
- Las actividades se listan con guiones (`-`) debajo del encabezado.

## 6. Argumentos de Línea de Comandos

```
python scripts/diligenciar.py [OPCIONES]
```

| Argumento | Tipo | Descripción |
|-----------|------|-------------|
| `--date` | `YYYY-MM-DD` | Fuerza la fecha de ejecución. Si no se indica, usa la fecha actual del sistema. |
| `--force-moment` | `2` o `3` | Fuerza el diligenciamiento de un acta específica (Momento 2 o 3), ignorando la detección automática por proximidad de fecha. |
| `--dry-run` | flag | Modo de simulación: analiza los archivos de entrada, identifica la bitácora y el acta que se procesarían, pero **no escribe ningún archivo** ni modifica el histórico. |
| `--no-email` | flag | Desactiva el envío de correo electrónico al finalizar. Por defecto, el correo se envía automáticamente sin preguntar. |

## 7. Comportamiento de Envío de Correo

A partir de la sesión 004, el envío de correo ya **no pregunta** interactivamente al usuario. Por defecto, al finalizar la ejecución se envía un correo con todos los documentos generados. Para desactivarlo:

```bash
python scripts/diligenciar.py --no-email
```

El modo `--dry-run` también desactiva el envío.

## 8. Procesamiento por Lote (Batch)

El script detecta **todas** las bitácoras pendientes en `historico_actividades.md` y las procesa en una sola ejecución. Cada bitácora:

1. Genera su archivo Excel en `output/bitacora<N>-<YYYY-MM-DD>/`
2. Se marca como `[DILIGENCIADA]` en el histórico
3. Se acumula en la lista de archivos para el correo final

Si además corresponde un acta (Momento 2 o 3), también se genera y adjunta al mismo correo.

## 9. Ejemplos de Ejecución

**Ejecutar con la fecha actual (procesa todas las pendientes y envía correo):**
```bash
python scripts/diligenciar.py
```

**Ejecutar sin enviar correo:**
```bash
python scripts/diligenciar.py --no-email
```

**Simular ejecución sin escribir archivos ni enviar correo:**
```bash
python scripts/diligenciar.py --dry-run
```

**Forzar una fecha y acta específica:**
```bash
python scripts/diligenciar.py --date 2026-07-08 --force-moment 2
```

**Combinar opciones:**
```bash
python scripts/diligenciar.py --date 2026-10-08 --force-moment 3 --no-email
```

## 10. Estructura de Carpetas de Salida

Los archivos generados se organizan bajo `output/` en la raíz del proyecto:

```
output/
├── bitacora1-2026-04-08/
│   ├── BitacoraMQuiazua1.xlsx
│   └── ejecucion.log
├── bitacora2-2026-04-22/
│   ├── BitacoraMQuiazua2.xlsx
│   └── ejecucion.log
└── acta-momento2-2026-07-08/
    ├── Actas-Inicio-Medio-Final.docx
    └── ejecucion.log
```

**Reglas de organización:**
- Si se procesa una bitácora, el acta (si aplica) se guarda en la **misma carpeta** de la bitácora.
- Si solo se procesa un acta (sin bitácora pendiente), se crea una carpeta independiente: `acta-momento<N>-<fecha>/`.
- Cada carpeta incluye un archivo `ejecucion.log` con el resumen de la ejecución.

## 11. Comportamiento ante Errores (Casos Edge)

| Situación | Comportamiento |
|-----------|----------------|
| **No existe `memory_descriptions.md`** | Lanza `FileNotFoundError` con la ruta esperada. |
| **No existe bloque JSON en `memory_descriptions.md`** | Lanza `ValueError` indicando que falta el bloque ` ```json ... ``` `. |
| **No existe `historico_actividades.md`** | Lanza `FileNotFoundError`. |
| **Todas las bitácoras están [DILIGENCIADA]** | Imprime mensaje informativo y continúa con el procesamiento de actas (si aplica). |
| **Bitácora pendiente sin datos en `memory_descriptions.md`** | Imprime error informativo, omite esa bitácora y continúa con las siguientes. |
| **Más de 7 actividades en una bitácora** | Trunca a 7 actividades e imprime advertencia en consola. Las filas 40-53 del Excel son el límite físico. |
| **Momento de acta inválido** (distinto de 2 o 3) | Imprime advertencia y omite el procesamiento de Word. |
| **Plantilla original no encontrada** | Lanza `FileNotFoundError` para Excel o Word según corresponda. |
| **Falta de permisos de escritura** | Error del sistema operativo al intentar guardar en `output/`. |

## 12. Ejecución de Pruebas

El proyecto incluye suites completas de pruebas unitarias y de integración.

**Comando para ejecutar todas las pruebas:**
```bash
python -m unittest tests/test_diligenciar.py -v
python -m unittest tests/test_email_module.py -v
```

**O ejecutar ambas suites:**
```bash
python -m unittest discover tests -v
```

**Cobertura de tests (diligenciar):**
- `test_parse_memory_descriptions` — extracción correcta del JSON de memoria.
- `test_get_next_undiligenced_bitacora` — detección de bitácora pendiente.
- `test_mark_bitacora_as_diligenced` — marcado correcto de bitácora como diligenciada.
- `test_excel_integration` — verificación de filas pares, merges verticales y metadatos en Excel.
- `test_max_7_activities` — truncamiento y advertencia al exceder 7 actividades.
- `test_word_integration_momento_2` — diligenciamiento correcto del Momento 2 (Tabla 3, P17, compromisos).
- `test_word_integration_momento_3` — diligenciamiento correcto del Momento 3 (Tabla 5, Tabla 8, juicio Aprobado).
- `test_word_template_backup` — creación automática del respaldo de plantilla Word.
- `test_output_folder_creation` — creación de carpetas de salida con nomenclatura correcta.
- `test_calibri_9_application` — aplicación de tipografía Calibri 9pt.
- `test_word_compromisos_mejora_momento_2` — inserción de compromisos en Tabla 3.
- `test_word_compromisos_mejora_momento_3` — inserción de compromisos en Tabla 5.

**Cobertura de tests (email):**
- `test_construir_asunto_*` — formatos de asunto para 1, 2 o 3 bitácoras, con/sin acta.
- `test_construir_cuerpo_*` — cuerpo del mensaje con saludo personalizado y listado de bitácoras.
- `test_enviar_email_mock_smtp` — verificación de estructura del email enviado.
- `test_enviar_email_reintentos_*` — reintentos automáticos ante fallos SMTP.
- `test_cargar_variables_entorno` — verificación de carga de `.env`.

## 13. Referencia para Agentes

Ver `instrucciones/AGENTS.md` para las reglas de operación del agente líder y el workflow de descomposición de tareas.

---

*Documentación generada para el proyecto de automatización SENA — Etapa Productiva.*
