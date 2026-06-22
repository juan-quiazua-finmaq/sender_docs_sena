# Automatizacion de Documentos SENA — Bitacoras y Actas

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

Este proyecto automatiza el diligenciamiento de **bitacoras (Excel)** y **actas de seguimiento/evaluacion (Word)** requeridas por el SENA durante la etapa productiva. Genera los documentos a partir de un registro de actividades, los organiza en carpetas y los envia por correo electronico al instructor.

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
- `--force-moment 2|3`: Forzar generacion de un acta
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

Si necesita regenerar archivos del proyecto, use `reset.py`:

```bash
# Regenerar todo (excepto .env)
uv run python scripts/reset.py --all

# Solo plantillas
uv run python scripts/reset.py --templates

# Solo archivos de contexto
uv run python scripts/reset.py --context

# Resetear .env (requiere confirmacion)
uv run python scripts/reset.py --env

# Resetear todo incluyendo .env (requiere confirmacion)
uv run python scripts/reset.py --all --include-env

# Sin confirmacion (para agentes)
uv run python scripts/reset.py --all --yes
```

El script intenta:
1. Descargar las plantillas desde GitHub.
2. Si falla, busca un backup local en `contexto/plantillas_backup/`.
3. Si todo falla, sugiere clonar el repositorio manualmente.

---

## Pruebas

```bash
uv run python -m unittest discover tests -v
```

---

## Licencia

Uso libre para fines academicos y personales. Para uso institucional o comercial, consultar con el autor del repositorio.
