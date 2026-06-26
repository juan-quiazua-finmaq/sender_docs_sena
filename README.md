# Automatizacion de Documentos SENA — Bitacoras y Actas

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

Este proyecto automatiza el diligenciamiento de **bitacoras (Excel)** y **actas de seguimiento/evaluacion (Word)** requeridas por el SENA durante la etapa productiva. Genera los documentos a partir de un registro de actividades, los organiza en carpetas y los envia por correo electronico al instructor.

---

## Inicio Rapido (Primer Uso)

Si es tu primera vez usando este proyecto, sigue estos pasos en orden:

### 1. Preparar el entorno

```bash
# Resetear todo al estado de primer uso (opcional, si acabas de clonar)
uv run python scripts/reset.py --all --include-env --yes

# Configurar credenciales y datos personales
uv run python scripts/setup.py
```

### 2. Llenar el historico de actividades

Edita `contexto/historico_actividades.md` con las actividades que realizaste en cada periodo (quincenal). Ejemplo:

```markdown
## Bitacora numero 1 - (08/04/2026 al 22/04/2026)
- Familiarizacion con la estructura general de la empresa
- Estudio del stack tecnologico
- Configuracion de repositorios
```

### 3. Inferir el JSON enriquecido (con agente de IA)

Pidele a un agente de IA (Claude, GPT, Gemini, etc.) que:
1. Lea `instrucciones/AGENTS.md` (especialmente la seccion 2b)
2. Lea `contexto/historico_actividades.md`
3. Complete `contexto/memory_descriptions.md` con el JSON enriquecido (seccion `bitacoras` y `actas`)

O ejecuta tu agente de IA preferido y pidele:
> "Lee el archivo instrucciones/AGENTS.md y sigue las instrucciones para diligenciar las bitacoras y actas a partir de contexto/historico_actividades.md"

### 4. Ejecutar el script principal

```bash
uv run python scripts/diligenciar.py --ai-mode
```

Esto generara:
- Las bitacoras en Excel
- Las actas en Word (momento 1, 2 o 3 segun la fecha)
- Un correo electronico al instructor con los archivos adjuntos

### 5. Verificar el estado del proyecto

```bash
uv run python scripts/doctor.py
```

### Comandos Utiles

| Comando | Descripcion |
|---------|-------------|
| `uv run python scripts/setup.py` | Configurar el entorno (.env) |
| `uv run python scripts/doctor.py` | Diagnosticar el estado del proyecto |
| `uv run python scripts/reset.py --all` | Resetear todo (excepto .env) |
| `uv run python scripts/diligenciar.py --ai-mode` | Generar bitacoras y acta |
| `uv run python scripts/diligenciar.py --dry-run` | Simular sin enviar correo |
| `uv run python scripts/diligenciar.py --date 2026-06-22` | Forzar fecha de ejecucion |

### Limpieza y Reset

Si necesitas empezar de nuevo o limpiar el estado:

```bash
# Limpiar estado de actas enviadas
uv run python scripts/reset.py --state

# Eliminar archivos generados
uv run python scripts/reset.py --output

# Resetear todo (plantillas + contexto + estado + output)
uv run python scripts/reset.py --all --yes

# Resetear TODO incluyendo .env
uv run python scripts/reset.py --all --include-env --yes
```

---

## Caracteristicas principales

- Diligenciamiento automatico de bitacoras Excel y actas Word.
- Procesamiento por lote: detecta y procesa todas las bitacoras pendientes en una ejecucion.
- Envio automatico de email con los documentos adjuntos.
- Deteccion inteligente de actas (Momento 2 / Momento 3) segun la fecha.
- Inferencia asistida por IA de descripciones y evidencias.
- Diagnostico completo con `doctor.py`.
- Regeneracion selectiva con `reset.py`.
- Suite de pruebas unitarias e integracion.
- Logica de catch-up: si ejecuta cerca de la fecha del Momento 2 o 3, las actas de momentos anteriores no enviadas se envian automaticamente.
- Estado de envio persistido en `contexto/actas_enviadas.json`.
- Checklist de campos que requieren diligenciamiento/firma manual.
- Observaciones por variable: las 9 celdas de la Tabla de Valoracion (M2 y M3) se diligencian individualmente con texto contextualizado por variable.

---

## Observaciones por variable (Tabla de Valoracion)

### Que se resolvio

Antes, el script escribia un unico texto de compromisos de mejora solo en la **primera fila tecnica** (fila 6) y la **primera fila actitudinal** (fila 17) de la Tabla de Valoracion del acta. Esto dejaba **7 de las 9 variables evaluadas con la celda de observaciones completamente vacia** en el Word generado:

| Filas diligenciadas antes | Filas que quedaban vacias |
|---------------------------|---------------------------|
| Fila 6 (tecnica) | Filas 7, 8, 9 (tecnicas) |
| Fila 17 (actitudinal) | Filas 18, 19, 20, 21 (actitudinales) |

Ahora cada una de las 9 variables recibe su propio texto de observacion, generado de forma individualizada por el agente de IA.

### Nueva estructura `valoraciones[]`

El campo `compromisos_mejora` (string unico) fue reemplazado por un array **`valoraciones[]`** de 9 objetos dentro de cada momento (`momento_2` y `momento_3`) en el JSON de `contexto/memory_descriptions.md`. Cada objeto contiene:

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `variable` | string | Nombre de la variable evaluada |
| `categoria` | string | `"tecnico"` o `"actitudinal"` |
| `observacion` | string | Texto contextualizado (1-2 frases, max. 40 palabras) |

### Variables diligenciadas (9 en total)

**4 variables tecnicas** (filas 6-9 de la Tabla de Valoracion):

| # | Variable |
|---|----------|
| 1 | Gestion de conocimiento |
| 2 | Creatividad y calidad |
| 3 | Administracion de recursos |
| 4 | Seguridad y salud en el trabajo |

**5 variables actitudinales** (filas 17-21 de la Tabla de Valoracion):

| # | Variable |
|---|----------|
| 5 | Trabajo en equipo |
| 6 | Relaciones interpersonales |
| 7 | Solucion de problemas |
| 8 | Cumplimiento |
| 9 | Organizacion |

### Compatibilidad hacia atras

El campo legacy `compromisos_mejora` se mantiene en el JSON como fallback:

- Si `valoraciones[]` **existe y tiene 9 entradas** → el script usa cada `observacion` para su celda correspondiente. `compromisos_mejora` se ignora.
- Si `valoraciones[]` **no existe o esta vacio** → el script usa `compromisos_mejora` como antes (mismo texto en filas 6 y 17).
- Si **ambos existen** pero `valoraciones[]` tiene menos de 9 entradas → las faltantes se rellenan con `compromisos_mejora`.

### Generacion por el agente de IA

Las observaciones son generadas por el agente de IA al diligenciar `contexto/memory_descriptions.md`, siguiendo la especificacion detallada de `instrucciones/AGENTS.md` (seccion 2c). El agente debe producir un texto unico por variable, con tono institucional SENA, basado en las actividades reales del historico y sin inventar evidencias.

---

## Primeros pasos

### Requisitos

- Python 3.10 o superior
- [uv](https://docs.astral.sh/uv/) (gestor de dependencias)
- Git

### Instalacion

```bash
git clone <url-del-repositorio>
cd sender_docs_sena
uv sync
```

### Configuracion inicial

Ejecute el wizard interactivo para configurar el archivo `.env`:

```bash
uv run python scripts/setup.py
```

El wizard le pedira:
- Credenciales de Gmail (remitente + contrasena de aplicacion)
- Correos del instructor SENA (produccion y pruebas)
- Correo en copia (CC)
- Modo de operacion (`pruebas` o `produccion`)
- Su nombre de aprendiz
- Nombre de la empresa
- Nombre del instructor SENA

### Verificacion

Despues de configurar, ejecute el diagnostico:

```bash
uv run python scripts/doctor.py
```

Esto verifica que todo este en orden. Si hay problemas, el script le indicara que hacer.

### Ejecucion

Para generar los documentos y enviar el correo:

```bash
uv run python scripts/diligenciar.py
```

Flags utiles:
- `--date YYYY-MM-DD`: Forzar fecha de ejecucion
- `--force-moment 1|2|3`: Forzar generacion de un acta especifica. Use `--force-moment 1` para forzar Momento 1 (Planeacion), `--force-moment 2` para Seguimiento, `--force-moment 3` para Evaluacion Final.
- `--dry-run`: Simular sin escribir archivos
- `--no-email`: No enviar correo

---

## Estructura del proyecto

```
sender_docs_sena/
├── scripts/                       # Codigo ejecutable
│   ├── diligenciar.py             # Script principal
│   ├── email_module.py            # Envio de correo
│   ├── env_validator.py           # Validacion de .env (compartido)
│   ├── setup.py                   # Wizard de configuracion
│   ├── doctor.py                  # Diagnostico del proyecto
│   └── reset.py                   # Regeneracion de archivos
├── tests/                         # Suite de pruebas
│   ├── test_diligenciar.py
│   ├── test_email_module.py
│   └── test_setup.py
├── contexto/                      # Datos de entrada
│   ├── plantillas/                # Plantillas institucionales
│   ├── historico_actividades.md   # Registro de actividades
│   ├── memory_descriptions.md     # JSON enriquecido
│   └── mensaje_instructor.md      # Plantilla del correo
├── output/                        # Documentos generados (gitignored)
├── .env                           # Variables de entorno (gitignored)
├── .env.example                   # Plantilla de .env
├── pyproject.toml
├── README.md
└── instrucciones/
    └── AGENTS.md                  # Instrucciones para agentes de IA
```

---

## Configuracion de .env

El archivo `.env` contiene 9 variables:

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `GMAIL_SENDER` | Correo Gmail remitente | `tu-correo@gmail.com` |
| `GMAIL_APP_PASSWORD` | Contrasena de aplicacion (16 chars) | `abcd efgh ijkl mnop` |
| `EMAIL_DESTINATARIO_PRODUCCION` | Correo del instructor (produccion) | `instructor@sena.edu.co` |
| `EMAIL_DESTINATARIO_PRUEBAS` | Correo para pruebas | `tu-prueba@gmail.com` |
| `EMAIL_CC` | Correo en copia | `tu-cc@gmail.com` |
| `EMAIL_MODO` | `pruebas` o `produccion` | `pruebas` |
| `APRENDIZ_NOMBRE` | Tu nombre completo | `Tu Nombre Apellido` |
| `EMPRESA_NOMBRE` | Nombre de la empresa | `Empresa SAS` |
| `INSTRUCTOR_NOMBRE` | Nombre del instructor SENA | `Nombre Instructor` |

> **Importante:** El archivo `.env` nunca debe subirse al repositorio. Esta en `.gitignore`.

### Fechas de las Actas (opcionales)

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `ACTA_M1_FECHA` | `2026-04-08` | Fecha objetivo Momento 1 (Planeacion), formato YYYY-MM-DD |
| `ACTA_M2_FECHA` | `2026-06-22` | Fecha objetivo Momento 2 (Seguimiento), formato YYYY-MM-DD |
| `ACTA_M3_FECHA` | `2026-10-07` | Fecha objetivo Momento 3 (Evaluacion Final), formato YYYY-MM-DD |
| `ACTA_VENTANA_DIAS` | `7` | Tolerancia en dias (antes/despues) para activar el momento |
| `FECHA_INICIO_ETAPA` | (vacio) | Fecha inicio etapa productiva, formato DD/MM/AAAA (Momento 1) |
| `FECHA_FIN_ETAPA` | (vacio) | Fecha fin etapa productiva, formato DD/MM/AAAA (Momento 1) |
| `FECHA_AFILIACION_ARL` | (vacio) | Fecha afiliacion ARL, formato DD/MM/AAAA (Momento 1, opcional) |
| `ARL_NUMERO` | (vacio) | Numero de poliza ARL (Momento 1, opcional) |
| `HORARIO_ETAPA` | (vacio) | "Diurno" / "Nocturno" / "Mixto" (Momento 1) |

> **Advertencia:** Si cambia estas fechas, el catch-up enviara todos los momentos no enviados hasta la fecha actual. Verifique `contexto/actas_enviadas.json` antes de ejecutar en produccion.

### Obtener contrasena de aplicacion de Google

1. Active la verificacion en 2 pasos en su cuenta de Google.
2. Vaya a [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Seleccione "Correo" como aplicacion y "Otro" como dispositivo.
4. Copie la contrasena de 16 caracteres generada y peguela en `GMAIL_APP_PASSWORD`.

---

## Uso con un agente de IA

Este proyecto esta optimizado para ser usado con un agente de IA. El flujo recomendado es:

1. El usuario actualiza `contexto/historico_actividades.md` con las actividades de los ultimos 15 dias.
2. El agente de IA infiere las descripciones detalladas y actualiza `contexto/memory_descriptions.md`.
3. El agente (o el usuario) ejecuta `uv run python scripts/diligenciar.py`.
4. El script genera los documentos y envia el correo al instructor.

Para instrucciones detalladas del agente, consulte `instrucciones/AGENTS.md`.

---

## Solucion de problemas

Si algo no funciona, ejecute el diagnostico:

```bash
uv run python scripts/doctor.py
```

El doctor verificara:
- Variables de entorno (.env)
- Archivos de contexto
- Plantillas (Excel y Word)
- Placeholders en el mensaje al instructor
- Bitacoras pendientes

Si el doctor detecta problemas, le indicara que ejecutar para resolverlos.

### Problemas comunes

| Problema | Solucion |
|----------|----------|
| "Faltan variables de entorno" | Ejecute `uv run python scripts/setup.py` |
| "Faltan plantillas" | Ejecute `uv run python scripts/reset.py --templates` |
| "No hay bitacoras pendientes" | Verifique que su historico no tenga la marca `[DILIGENCIADA]` |
| "Error de autenticacion SMTP" | Verifique su `GMAIL_APP_PASSWORD` y que la verificacion en 2 pasos este activa |
| "JSON malformado en memory_descriptions.md" | Ejecute `uv run python scripts/reset.py --context` para regenerar |

---

## Reset del proyecto

Si necesitas limpiar el estado del proyecto o prepararlo para un primer uso, usa `scripts/reset.py`:

```bash
# Resetear todo (plantillas + contexto + estado de actas + output generado)
uv run python scripts/reset.py --all --yes

# Tambien resetear el .env (hace backup automatico)
uv run python scripts/reset.py --all --include-env --yes

# Solo limpiar el estado de actas enviadas (actas_enviadas.json)
uv run python scripts/reset.py --state

# Solo eliminar archivos generados (output/)
uv run python scripts/reset.py --output

# Solo regenerar plantillas desde GitHub/backup
uv run python scripts/reset.py --templates

# Solo regenerar archivos de contexto
uv run python scripts/reset.py --context
```

Despues de un reset completo, sigue los pasos de la seccion "Inicio Rapido (Primer Uso)" para configurar el sistema desde cero.

---

## Estado de actas

El script rastrea cuales actas (Momentos 1, 2, 3) ya fueron enviadas en el archivo `contexto/actas_enviadas.json`. Este archivo tiene este formato:

```json
{
    "momento_1": { "enviada": false, "fecha_envio": null },
    "momento_2": { "enviada": false, "fecha_envio": null },
    "momento_3": { "enviada": false, "fecha_envio": null }
}
```

Para forzar el reenvio de un momento, edite el archivo y cambie `enviada: false`. Para limpiar todo el estado, ejecute `uv run python scripts/reset.py --all` (esto regenera el archivo al estado inicial).

---

## Checklist manual

Tras la ejecucion, el script genera un archivo `checklist_manual.txt` en la carpeta de cada acta y lo imprime en consola bajo el bloque `[CHECKLIST MANUAL]`. Este lista los campos que **usted debe diligenciar manualmente** (firmas, observaciones del instructor/co-formador, enlace de grabacion, datos de la Tabla 1 de informacion general, etc.). El script no puede diligenciar firmas digitales ni datos que solo el instructor o co-formador conocen.

> Las firmas del aprendiz, instructor de seguimiento y ente co-formador (en Tablas 2/4/9) SIEMPRE requieren firma humana fisica o digital. El script no las puede generar.

---

## Pruebas

```bash
uv run python -m unittest discover tests -v
```

---

## Licencia

Uso libre para fines academicos y personales. Para uso institucional o comercial, consultar con el autor del repositorio.
