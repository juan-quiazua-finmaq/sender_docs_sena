# 📋 Docs_SENA — Automatización de Bitácoras y Actas SENA

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

Este proyecto automatiza el diligenciamiento de **bitácoras (Excel)** y **actas de seguimiento/evaluación (Word)** requeridas por el SENA durante la etapa productiva. Genera documentos profesionales, los organiza por carpetas y los envía automáticamente por correo electrónico.

---

## ✨ Características principales

- 📝 **Diligenciamiento automático** de bitácoras Excel y actas Word a partir de archivos de texto plano.
- 🔄 **Procesamiento por lote**: detecta y procesa todas las bitácoras pendientes en una sola ejecución.
- 📧 **Envío automático de email** con todos los documentos generados adjuntos.
- 🧠 **Detección inteligente de actas**: identifica automáticamente si corresponde generar el acta de seguimiento (Momento 2) o evaluación final (Momento 3) según la fecha.
- 🖊️ **Inserción de firmas digitales** en los documentos generados.
- 🗂️ **Organización automática** de salida en carpetas con nomenclatura clara.
- 🧪 **Suite completa de pruebas** unitarias e integración.
- 🤖 **Optimizado para agentes de IA**: flujo recomendado para reducir errores humanos y agilizar el proceso.

---

## 🚀 Instalación rápida

### Prerrequisitos

| Requisito | Versión | Descripción |
|-----------|---------|-------------|
| Python | `>=3.10` | Lenguaje de programación principal |
| git | Cualquier versión reciente | Para clonar el repositorio |
| uv | Última versión | Gestor de entornos y dependencias Python (ultrarrápido, reemplaza a `pip` y `venv`) |

> **¿Qué es `uv`?**  
> `uv` es un gestor de entornos virtuales y dependencias para Python, escrito en Rust. Es mucho más rápido que `pip` y `venv` tradicionales, y permite sincronizar dependencias con un solo comando.

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd Docs_SENA

# 2. Instalar uv (si no lo tienes)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Sincronizar dependencias (crea el entorno virtual automáticamente)
uv sync
```

---

## ⚙️ Configuración

### 1. Variables de entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Abre `.env` con tu editor favorito y completa los siguientes valores:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `GMAIL_APP_PASSWORD` | Contraseña de 16 caracteres generada por Google para aplicaciones | `abcd efgh ijkl mnop` |
| `GMAIL_SENDER` | Correo de Gmail desde el que se enviarán los documentos | `tu-correo@gmail.com` |
| `EMAIL_DESTINATARIO_PRODUCCION` | Correo del instructor SENA en producción | `instructor@sena.edu.co` |
| `EMAIL_DESTINATARIO_PRUEBAS` | Correo para pruebas (tuyo o de un compañero) | `tu-correo-pruebas@gmail.com` |
| `EMAIL_CC` | Correo en copia fijo (monitorización) | `tu-correo-cc@gmail.com` |
| `EMAIL_MODO` | Modo de operación: `pruebas` o `produccion` | `pruebas` |

> [!WARNING]
> **Nunca subas tu archivo `.env` al repositorio.** Está protegido por `.gitignore`, pero verifica que no lo expongas accidentalmente.

### 2. Guía paso a paso: Obtener contraseña de aplicación de Google

Para que el script pueda enviar correos automáticamente, necesitas una **contraseña de aplicación** de Gmail (no es tu contraseña normal).

1. Ve a [https://myaccount.google.com/security](https://myaccount.google.com/security) e inicia sesión con tu cuenta de Gmail.
2. En la sección **"Cómo inicias sesión en Google"**, verifica que la **Verificación en dos pasos** esté **activada**. Si no lo está, actívala primero.
3. En el mismo apartado de seguridad, busca y selecciona **"Contraseñas de aplicaciones"**.
4. En el desplegable, selecciona **"Correo"** como aplicación y **"Otro"** como dispositivo (puedes poner `Docs_SENA`).
5. Haz clic en **Generar**. Google mostrará una contraseña de **16 caracteres** (por ejemplo: `abcd efgh ijkl mnop`).
6. **Copia esa contraseña** y pégala en tu archivo `.env` en la variable `GMAIL_APP_PASSWORD`.
7. Guarda el archivo `.env`.

> [!IMPORTANT]
> Si cambias la contraseña principal de tu cuenta de Google, las contraseñas de aplicaciones se invalidan y debes generar una nueva.

---

## 📁 Estructura del proyecto

```
Docs_SENA/
├── scripts/                    # Código ejecutable
│   ├── diligenciar.py          # Script principal de automatización
│   └── email_module.py         # Módulo de envío de correo
├── tests/                        # Pruebas automatizadas
│   ├── test_diligenciar.py       # Tests del script principal
│   └── test_email_module.py      # Tests del módulo de correo
├── contexto/                     # Datos de entrada y plantillas
│   ├── plantillas/               # Plantillas base (debes diligenciarlas manualmente)
│   │   ├── bitacoras.xlsx        # Plantilla Excel de bitácoras
│   │   └── actas.docx            # Plantilla Word de actas
│   ├── historico_actividades.md  # Registro manual de actividades
│   ├── memory_descriptions.md    # Descripciones inferidas por IA (JSON)
│   └── mensaje_instructor.md     # Plantilla editable del cuerpo del correo al instructor
├── instrucciones/                # Instrucciones para agentes de IA
│   └── AGENTS.md                 # Reglas de operación del agente líder
├── output/                       # Documentos generados (se crea automáticamente)
├── .env                          # Variables de entorno (no subir a git)
├── .env.example                  # Plantilla de variables de entorno
├── pyproject.toml                # Configuración del proyecto y dependencias
├── .gitignore                    # Archivos ignorados por git
└── README.md                     # Este archivo
```

> **Nota:** La firma digital `FirmeManu.png` (imagen PNG con fondo transparente) debe estar disponible en el directorio raíz del workspace, junto a la carpeta `Docs_SENA/`. Se inserta manualmente en las plantillas `bitacoras.xlsx` y `actas.docx`.

---

## 📝 Diligenciamiento de plantillas (CRÍTICO)

> [!WARNING]
> **Las plantillas deben diligenciarse manualmente ANTES de usar el script.** Si no completas los campos estáticos, esos espacios quedarán vacíos en **todos** los documentos generados.

### Plantilla `contexto/plantillas/bitacoras.xlsx`

Abre el archivo y completa al menos los siguientes campos (la ubicación exacta depende de la plantilla SENA):

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Nombre del aprendiz | Tu nombre completo | `Manuel Quiazua` |
| Nombre de la empresa | Razón social de la empresa | `Tech Solutions SAS` |
| Nombre del instructor | Instructor de seguimiento SENA | `Oscar Ivan Ospina Ospina` |
| Datos de la empresa | NIT, dirección, teléfono, etc. | `901.234.567-8` |
| **Firma** | Imagen PNG sin fondo (transparente) | `FirmeManu.png` |

> [!CAUTION]
> La **firma debe ser una imagen PNG con fondo transparente**. Si tiene fondo blanco u otro color, se verá mal impresa en los documentos oficiales.

### Plantilla `contexto/plantillas/actas.docx`

Abre el archivo y completa:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Datos del aprendiz | Nombre completo, documento, programa de formación | `Manuel Quiazua` |
| Datos de la empresa | Nombre, NIT, representante legal | `Tech Solutions SAS` |
| Datos del instructor | Nombre y datos de contacto | `Oscar Ivan Ospina Ospina` |
| **Firma** | Imagen PNG sin fondo (transparente) | `FirmeManu.png` |

> [!WARNING]
> **Consecuencia de no diligenciar:** Si dejas estos campos vacíos, el script solo llenará las actividades dinámicas, pero los datos personales, empresariales y la firma aparecerán en blanco en todos los documentos entregados.

---

## 📄 Diligenciamiento de archivos de entrada

### `historico_actividades.md`

Este archivo es el **registro manual** de tus actividades. El script lo lee para saber qué bitácoras están pendientes.

**Formato exacto:**

```markdown
# Historico de Actividades Manuel Quiazua

Este es un markdown que se actualiza de manera manual...
---

## Bitacora numero 1 - (08/04/2026 al 22/04/2026) [DILIGENCIADA]
- El aprendiz se familiarizo con la estructura general de la empresa
- El aprendiz estudio profundamente en el stack tecnologico general de la empresa
- ...

## bitacora numero 2 - (22/04/2026 al 06/05/2026)
- Se le indico el plan de aprendizaje para colaborar en los equipos internos
- ...
```

**Reglas del formato:**

- Cada bitácora empieza con un encabezado de nivel 2 (`##`) que contenga `Bitacora numero <N>`.
- Las actividades se listan con guiones (`-`) debajo del encabezado.
- La etiqueta `[DILIGENCIADA]` indica que esa bitácora **ya fue procesada** y el script la omitirá.
- **Si quitas `[DILIGENCIADA]`**, el script la detectará como pendiente y la procesará en el siguiente lote.

**Cómo agregar nuevas bitácoras:**

1. Abre `contexto/historico_actividades.md`.
2. Al final del archivo, agrega un nuevo bloque con el formato anterior.
3. **No pongas `[DILIGENCIADA]`** si aún no ha sido procesada.
4. Guarda el archivo.

### `memory_descriptions.md`

Este archivo contiene un **bloque JSON** con descripciones detalladas, evidencias y observaciones inferidas para cada bitácora y acta. Es la **fuente de datos enriquecida** que usa el script para llenar los documentos.

**Estructura del JSON:**

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
      "fecha": "22/06/2026",
      "observaciones_instructor": "El aprendiz demuestra gran interés...",
      "observaciones_aprendiz": "He logrado familiarizarme con el stack...",
      "observaciones_coformador": "Manuel muestra excelente actitud...",
      "compromisos_mejora": "Se sugiere reforzar la documentación técnica..."
    },
    "momento_3": {
      "fecha": "07/10/2026",
      "observaciones_instructor": "Desempeño general sobresaliente...",
      "observaciones_aprendiz": "Culmino mi etapa productiva muy satisfecho...",
      "observaciones_coformador": "El aporte de Manuel fue valioso...",
      "compromisos_mejora": "Se recomienda profundizar en pruebas automatizadas..."
    }
  }
}
```

**Campos obligatorios por bitácora:**

| Campo | Formato | Descripción |
|-------|---------|-------------|
| `numero` | Entero | Identificador de la bitácora (`1`, `2`, `3`...) |
| `fecha_inicio` | `DD/MM/AAAA` | Fecha de inicio del período |
| `fecha_fin` | `DD/MM/AAAA` | Fecha de fin del período |
| `actividades` | Lista de objetos | Máximo 7 actividades por bitácora |

Cada actividad debe tener: `descripcion`, `fecha_inicio`, `fecha_fin`, `evidencia`.

**Campos obligatorios por acta:**

| Campo | Descripción |
|-------|-------------|
| `fecha` | Fecha del acta |
| `observaciones_aprendiz` | Texto de las observaciones del aprendiz |
| `compromisos_mejora` | Texto de compromisos (opcional pero recomendado) |

> [!TIP]
> **Recomendación fuerte:** Usa un **agente de IA** para generar el contenido de `memory_descriptions.md` a partir de `historico_actividades.md`. El agente puede inferir descripciones detalladas, distribuir fechas, proponer evidencias y redactar observaciones coherentes para las actas, ahorrándote horas de trabajo manual.

---

## Plantilla del mensaje al instructor

El cuerpo del correo electrónico que se envía al instructor SENA se construye a partir de la plantilla `contexto/mensaje_instructor.md`. Puedes editar este archivo libremente para personalizar el saludo, agregar contexto adicional o ajustar la despedida.

**Placeholders disponibles** (el script los reemplaza automáticamente):

| Placeholder | Se reemplaza por |
|-------------|------------------|
| `{{destinatario}}` | Nombre del instructor destinatario |
| `{{lista_bitacoras}}` | Lista de bitácoras con sus periodos |
| `{{acta_moment}}` | Referencia al acta (Momento 2 o 3) si aplica |
| `{{firma}}` | Tu nombre y empresa |
| `{{fecha_ejecucion}}` | Fecha de ejecución del script |

> **Recomendación:** Si editas la plantilla, conserva los placeholders para que el script pueda inyectar los datos dinámicos. Si eliminas un placeholder, esa parte del correo aparecerá vacía.

Cuando uses un agente de IA para operar el proyecto, el agente te preguntará si quieres usar la plantilla actual o si prefieres editarla primero (incluyendo dictarle el texto nuevo). Consulta `instrucciones/AGENTS.md` para más detalles.

---

## 🎯 Uso del script

### Comando básico

```bash
uv run python scripts/diligenciar.py
```

Este comando:
1. Lee todas las bitácoras pendientes en `historico_actividades.md`.
2. Genera los archivos Excel y Word correspondientes.
3. Los guarda en `output/` organizados por carpetas.
4. Envía un correo con los documentos adjuntos (si no se desactiva).

### Flags disponibles

| Flag | Tipo | Descripción | Ejemplo |
|------|------|-------------|---------|
| `--date` | `YYYY-MM-DD` | Fuerza la fecha de ejecución. Si no se indica, usa la fecha actual del sistema. | `--date 2026-07-08` |
| `--force-moment` | `2` o `3` | Fuerza el diligenciamiento de un acta específica (Momento 2 = Seguimiento, Momento 3 = Evaluación Final), ignorando la detección automática por fecha. | `--force-moment 2` |
| `--dry-run` | Flag | Modo de simulación: analiza los archivos de entrada, identifica qué se procesaría, pero **no escribe ningún archivo** ni modifica el histórico ni envía correo. | `--dry-run` |
| `--no-email` | Flag | Desactiva el envío de correo electrónico al finalizar. Por defecto, el correo se envía automáticamente. | `--no-email` |

### Ejemplos de combinaciones

```bash
# Ejecutar con la fecha actual, procesar todo lo pendiente y enviar correo
uv run python scripts/diligenciar.py

# Ejecutar sin enviar correo
uv run python scripts/diligenciar.py --no-email

# Simular ejecución (no escribe nada, útil para verificar antes de correr)
uv run python scripts/diligenciar.py --dry-run

# Forzar una fecha específica y generar el acta del momento 2
uv run python scripts/diligenciar.py --date 2026-07-08 --force-moment 2

# Combinar fecha, forzar acta y desactivar correo
uv run python scripts/diligenciar.py --date 2026-10-08 --force-moment 3 --no-email
```

---

## 🤖 Uso recomendado con Agente de IA ⭐

Este es el flujo **más recomendado** para usar el proyecto. Reduce errores humanos, genera contenido de calidad y agiliza todo el proceso.

### Referencia

Consulta el archivo [`instrucciones/AGENTS.md`](instrucciones/AGENTS.md) para las reglas de operación del agente líder.

### ¿Por qué usar un agente de IA?

- 🧠 **Inferencia automática**: El agente lee `historico_actividades.md` y genera descripciones detalladas, evidencias y observaciones para actas en `memory_descriptions.md`.
- ✅ **Reducción de errores**: Evita olvidar campos, escribir fechas incorrectas o dejar actividades sin evidencia.
- ⚡ **Velocidad**: Lo que te tomaría 1-2 horas escribiendo manualmente, el agente lo hace en segundos.
- 🔄 **Consistencia**: Mantiene un tono y estilo uniforme en todas las bitácoras y actas.

### Flujo sugerido con agente de IA

1. **Tú** actualizas `historico_actividades.md` con las actividades de los últimos 15 días.
2. **El agente** lee el histórico, infiere descripciones detalladas y actualiza `memory_descriptions.md`.
3. **El agente** (o tú) ejecutas `uv run python scripts/diligenciar.py`.
4. **El script** genera los documentos y los envía por correo.
5. **Tú** revisas el correo enviado y confirmas la entrega.

---

## ⏰ Automatización con CRON (Agentes de IA) ⭐⭐

Este es el flujo **más recomendado de todos**: configura tu agente de IA para que ejecute el script periódicamente sin que tengas que intervenir.

### Configuración en diferentes agentes

| Agente | Cómo configurar CRON |
|--------|----------------------|
| **Antigravity** | Usa la función de "Scheduled Tasks" o "CRON Jobs" en el panel del agente. Programa la ejecución del script cada 15 días. |
| **Codex** | Configura un `codex.md` con una regla de periodicidad. El agente puede ejecutar comandos en el entorno configurado. |
| **Claude** | Usa el proyecto de Claude con instrucciones de sistema que incluyan la periodicidad de ejecución. |
| **OpenClaw** | Configura un workflow con trigger de tiempo (cada 2 semanas) que ejecute `uv run python scripts/diligenciar.py`. |

### Ejemplo de prompt para configurar CRON

```
Eres el agente de automatización SENA. Tu tarea es:

1. Cada 15 días, leer el archivo contexto/historico_actividades.md.
2. Si hay nuevas bitácoras sin [DILIGENCIADA], inferir descripciones detalladas
   y actualizar contexto/memory_descriptions.md.
3. Ejecutar: uv run python scripts/diligenciar.py
4. Verificar que el correo se haya enviado correctamente.
5. Reportar el resultado en un resumen breve.

No modifiques las plantillas. No borres archivos de output/ anteriores.
```

### Beneficios

- 🕒 **Ejecución periódica sin intervención humana**.
- 📬 **Entregas puntuales** cada 15 días al instructor.
- 🧘 **Cero estrés**: olvídate de recordar fechas o formatos.

---

## 💾 Salida generada

Los documentos generados se organizan en la carpeta `output/`:

```
output/
├── bitacora1-2026-04-08/
│   ├── BitacoraMQuiazua1.xlsx
│   └── ejecucion.log
├── bitacora2-2026-04-22/
│   ├── BitacoraMQuiazua2.xlsx
│   └── ejecucion.log
└── bitacora3-2026-05-06/
    ├── BitacoraMQuiazua3.xlsx
    ├── Actas-Inicio-Medio-Final.docx   <-- si aplica acta
    └── ejecucion.log
```

**Nomenclatura de carpetas:** `bitacora<N>-<YYYY-MM-DD>/`

**Archivos generados en cada carpeta:**

| Archivo | Descripción |
|---------|-------------|
| `BitacoraMQuiazua<N>.xlsx` | Bitácora diligenciada con actividades y metadatos |
| `Actas-Inicio-Medio-Final.docx` | Acta diligenciada (solo si aplica el momento detectado) |
| `ejecucion.log` | Resumen de la ejecución del script para esa bitácora |

> **Regla de organización:** Si se procesa una bitácora y además corresponde un acta, el acta se guarda en la **misma carpeta** de la bitácora. Si solo se procesa un acta (sin bitácora pendiente), se crea una carpeta independiente: `acta-momento<N>-<fecha>/`.

---

## 🧪 Ejecución de pruebas

El proyecto incluye suites completas de pruebas unitarias y de integración.

```bash
# Ejecutar todas las pruebas con verbose
uv run python -m unittest discover tests -v
```

**Cobertura de tests:**

- `test_parse_memory_descriptions` — extracción correcta del JSON de memoria.
- `test_get_next_undiligenced_bitacora` — detección de bitácora pendiente.
- `test_mark_bitacora_as_diligenced` — marcado correcto de bitácora como diligenciada.
- `test_excel_integration` — verificación de filas pares, merges verticales y metadatos en Excel.
- `test_max_7_activities` — truncamiento y advertencia al exceder 7 actividades.
- `test_word_integration_momento_2` — diligenciamiento correcto del Momento 2.
- `test_word_integration_momento_3` — diligenciamiento correcto del Momento 3.
- `test_word_template_backup` — creación automática del respaldo de plantilla Word.
- `test_output_folder_creation` — creación de carpetas de salida con nomenclatura correcta.
- `test_calibri_9_application` — aplicación de tipografía Calibri 9pt.
- `test_construir_asunto_*` — formatos de asunto para 1, 2 o 3 bitácoras, con/sin acta.
- `test_enviar_email_mock_smtp` — verificación de estructura del email enviado.
- `test_enviar_email_reintentos_*` — reintentos automáticos ante fallos SMTP.

---

## 🖥️ Sistemas compatibles

| Sistema Operativo | Estado | Requisitos |
|-------------------|--------|------------|
| Windows | ✅ Compatible | Python 3.10+, uv, git. Recomendado usar PowerShell o Git Bash. |
| Linux | ✅ Compatible | Python 3.10+, uv, git. Distribuciones basadas en Debian/Ubuntu/Fedora. |
| macOS | ✅ Compatible | Python 3.10+, uv, git. Recomendado usar Terminal o iTerm2. |

> **Nota:** El script no requiere interfaz gráfica. Funciona completamente por línea de comandos, por lo que es compatible con servidores remotos y contenedores.

---

## ❓ Solución de problemas comunes

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| **Campos vacíos en documentos generados** | Las plantillas (`bitacoras.xlsx`, `actas.docx`) no fueron diligenciadas manualmente con los datos del aprendiz, empresa e instructor. | Abre las plantillas en `contexto/plantillas/` y completa todos los campos estáticos antes de ejecutar el script. |
| **Error de autenticación SMTP** | La `GMAIL_APP_PASSWORD` es incorrecta, expiró o la verificación en dos pasos no está activada. | Revisa la sección [Obtener contraseña de aplicación de Google](#2-guía-paso-a-paso-obtener-contraseña-de-aplicación-de-google). Genera una nueva contraseña de aplicación y actualiza tu `.env`. |
| **Plantilla no encontrada** | Los archivos `bitacoras.xlsx` o `actas.docx` no están en `contexto/plantillas/`. | Verifica que las plantillas existan en esa ruta. Si las moviste, restaúralas. |
| **No se genera ningún documento** | Todas las bitácoras en `historico_actividades.md` ya tienen la etiqueta `[DILIGENCIADA]`. | Revisa el histórico. Si hay una bitácora nueva, asegúrate de que **no** tenga `[DILIGENCIADA]`. |
| **Error "No se encontró el bloque JSON"** | El archivo `memory_descriptions.md` no contiene un bloque de código JSON válido. | Verifica que el archivo tenga el formato ```json ... ``` correcto. |
| **Más de 7 actividades y se truncan** | El Excel solo tiene espacio físico para 7 actividades (filas 40-53). | Divide las actividades en dos bitácoras o resume las más importantes. El script trunca automáticamente e imprime una advertencia. |
| **El correo no se envía** | El flag `--no-email` está activado, o es un `--dry-run`, o el modo es incorrecto. | Verifica que no uses `--no-email` ni `--dry-run`. Revisa que `EMAIL_MODO` en `.env` sea `pruebas` o `produccion`. |
| **Firma no aparece o se ve mal** | La imagen de firma no es PNG transparente o no está en la ruta esperada. | Usa una imagen PNG con fondo transparente. Verifica que la firma esté insertada correctamente en la plantilla. |

---

## 📄 Licencia y créditos

Este proyecto fue desarrollado para automatizar el diligenciamiento de documentos SENA durante la etapa productiva del aprendiz **Manuel Quiazua**.

- **Stack:** Python 3.10+, openpyxl, python-docx, uv.
- **Inspiración:** Procesos repetitivos de documentación académica que pueden (y deben) automatizarse.

> Uso libre para fines académicos y personales. Para uso institucional o comercial, consulta al autor.

---

*Documentación generada para el proyecto de automatización SENA — Etapa Productiva.*
