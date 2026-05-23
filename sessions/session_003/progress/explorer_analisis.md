# Análisis de Estructura para Capa de Email

**Fecha de análisis:** 23 de mayo de 2026  
**Sesión:** session_003  
**Propósito:** Identificar puntos de integración óptimos para la capa de envío de correo electrónico

---

## 1. Estructura Actual del Proyecto

### Archivos Principales

| Archivo | Ruta | Propósito |
|---------|------|-----------|
| `diligenciar.py` | `/home/eivorkinkest/Documentos/Docs_SENA/diligenciar.py` | Script principal de automatización. Contiene funciones para diligenciar bitácoras (Excel) y actas (Word). Punto de entrada: `main()` |
| `test_diligenciar.py` | `/home/eivorkinkest/Documentos/Docs_SENA/test_diligenciar.py` | Suite de tests unitarios y de integración. 11 tests existentes que cubren parsing, Excel, Word y backups |
| `memory_descriptions.md` | `/home/eivorkinkest/Documentos/Docs_SENA/DocsOriginales/memory_descriptions.md` | Contiene el bloque JSON con datos de bitácoras y actas |
| `historico_actividades.md` | `/home/eivorkinkest/Documentos/Docs_SENA/DocsOriginales/historico_actividades.md` | Registro de bitácoras diligenciadas (marcadas con `[DILIGENCIADA]`) |
| `spec_email_layer.md` | `/home/eivorkinkest/Documentos/Docs_SENA/sessions/session_003/spec_email_layer.md` | Especificación de requerimientos para la capa de email |

### Archivos de Plantilla (DocsOriginales/)

| Archivo | Propósito |
|---------|-----------|
| `BitacoraMQuiazua_template.xlsx` | Plantilla limpia de bitácora Excel (respaldo) |
| `Actas-Inicio-Medio-Final_template.docx` | Plantilla limpia de actas Word (respaldo) |
| `BitacoraMQuiazua1.xlsx` | Archivo de trabajo Excel |
| `Actas-Inicio-Medio-Final.docx` | Archivo de trabajo Word |

### Estructura de Salida

```
DocsOriginales/
└── output/
    ├── bitacora1-YYYY-MM-DD/
    │   ├── BitacoraMQuiazua1.xlsx
    │   ├── Actas-Inicio-Medio-Final.docx
    │   └── ejecucion.log
    ├── bitacora2-YYYY-MM-DD/
    └── bitacora3-YYYY-MM-DD/
```

### Estado de `.gitignore`

**PROBLEMA IDENTIFICADO:** No existe archivo `.gitignore` en la raíz del proyecto. Esto es crítico porque las credenciales de Gmail (App Password) se almacenarán en `.env` y deben ser excluidas del control de versiones.

---

## 2. Puntos de Integración Identificados

### 2.1. Pregunta de Autorización (ANTES de ejecutar)

**Ubicación óptima:** Inicio de la función `main()`, justo después del parsing de argumentos y antes de cualquier procesamiento.

**Línea específica:** Después de la línea 383 (`args = parser.parse_args()`) y antes de la línea 386 (resolución de fecha).

**Código actual de referencia:**
```python
def main():
    parser = argparse.ArgumentParser(...)
    # ... definición de argumentos ...
    args = parser.parse_args()  # Línea 383
    
    # >>> INSERTAR AQUÍ: pregunta de autorización de email <<<
    
    # 1. Resolver fecha de ejecución  # Línea 386
    if args.date:
        exec_date = datetime.datetime.strptime(...)
```

**Justificación:**
- El argumento `--dry-run` ya está disponible en este punto
- Se puede evaluar si el usuario desea envío de email antes de cualquier operación
- La respuesta se almacena en una variable de flag para usarla al final

### 2.2. Llamada al Módulo de Email (DESPUÉS de generar documentos)

**Ubicación óptima:** Al final de `main()`, después de escribir el log de ejecución y antes del mensaje de finalización.

**Línea específica:** Después de la línea 470 (escritura del log) y antes de la línea 472 (mensaje de éxito).

**Código actual de referencia:**
```python
    if log_dir and not args.dry_run:
        log_path = os.path.join(log_dir, "ejecucion.log")
        # ... escritura del log ...
        print(f"[Log] Resumen guardado en {log_path}")  # Línea 470
    
    # >>> INSERTAR AQUÍ: llamada a enviar_email() si flag está activo <<<
    
    print(f"=== AUTOMATIZACIÓN SENA FINALIZADA CON ÉXITO ===")  # Línea 472
```

**Información disponible en este punto:**
- `pending_num`: Número de bitácora procesada
- `bitacora_data`: Datos completos de la bitácora (fechas, actividades)
- `target_moment`: Momento del acta procesada (2 o 3)
- `log_dir`: Ruta de la carpeta de salida con los documentos
- `exec_date_str`: Fecha de ejecución formateada

### 2.3. Almacenamiento de Configuración

**Archivo `.env` (NUEVO - crear en raíz):**
```bash
# Credenciales de Gmail
GMAIL_APP_PASSWORD=<app_password_de_16_caracteres>

# Destinatario (configurable por entorno)
EMAIL_DESTINATARIO=oiospina@sena.edu.co  # Producción
# EMAIL_DESTINATARIO=jmqo2015@gmail.com  # Pruebas

# Configuración opcional
EMAIL_REMITENTE=jmqo2026@gmail.com
EMAIL_CC=eivorkinkest@gmail.com
EMAIL_MAX_RETRIES=3
```

**Archivo `.gitignore` (NUEVO - crear en raíz):**
```gitignore
# Credenciales y secretos
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
```

**Carga de variables en `diligenciar.py`:**
Agregar al inicio del archivo (después de los imports):
```python
from dotenv import load_dotenv
load_dotenv()  # Carga variables desde .env

# Constantes de email (se leen de .env)
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO", "oiospina@sena.edu.co")
EMAIL_CC = os.getenv("EMAIL_CC", "eivorkinkest@gmail.com")
EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE", "jmqo2026@gmail.com")
EMAIL_MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
```

---

## 3. Dependencias Necesarias

### Librerías de Python para Email

| Librería | Tipo | Propósito | Instalación |
|----------|------|-----------|-------------|
| `smtplib` | Standard library | Cliente SMTP para conexión con Gmail | Incluida en Python |
| `email` | Standard library | Construcción de mensajes MIME | Incluida en Python |
| `email.mime.multipart` | Standard library | Mensajes con múltiples partes (texto + adjuntos) | Incluida en Python |
| `email.mime.text` | Standard library | Parte de texto del email | Incluida en Python |
| `email.mime.base` | Standard library | Base para adjuntos | Incluida en Python |
| `email.mime.application` | Standard library | Adjuntos de archivos | Incluida en Python |
| `email.encoders` | Standard library | Codificación de adjuntos (base64) | Incluida en Python |
| `python-dotenv` | Third-party | Carga de variables desde `.env` | `pip install python-dotenv` |

### Comando de instalación:
```bash
pip install python-dotenv
```

**Nota:** No se requieren librerías externas para SMTP. Las librerías estándar de Python (`smtplib`, `email.*`) son suficientes para enviar correos mediante Gmail.

---

## 4. Riesgos Identificados

### 4.1. Riesgos Críticos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Sin `.gitignore`** | Credenciales de Gmail podrían subirse a GitHub | Crear `.gitignore` antes de crear `.env` |
| **App Password inválido** | Fallo de autenticación en Gmail | Validar credenciales en primer uso, mostrar error claro |
| **Archivos adjuntos no existen** | Email se envía sin adjuntos o falla | Verificar existencia de archivos antes de adjuntar |
| **Conexión SMTP bloqueada** | Firewall o red corporativa bloquea puerto 587 | Implementar timeout, mensaje de error descriptivo |

### 4.2. Riesgos de Integración con Código Existente

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| **Modificación de `main()`** | El flujo actual tiene múltiples branches condicionales | Usar flag booleano `send_email_flag`, lógica aislada |
| **Variables de entorno no cargadas** | `python-dotenv` no encuentra `.env` | Usar `load_dotenv()` con ruta explícita si es necesario |
| **Tests existentes fallan** | Nuevas dependencias rompen tests | Mockear funciones de email en `test_diligenciar.py` |
| **dry-run no considerado** | Email podría enviarse en modo dry-run | Verificar `args.dry_run` antes de cualquier envío real |
| **Carpeta de salida vacía** | Si no se genera ningún documento, no hay qué adjuntar | Validar que `log_dir` exista y tenga archivos antes de enviar |

### 4.3. Riesgos Específicos de Gmail

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| **Límite de envío diario** | Gmail tiene límite de ~500 emails/día | No aplica (uso ocasional), pero monitorear |
| **App Password expira** | Si se revoca acceso, el password deja de funcionar | Documentar proceso de regeneración en README |
| **Less Secure Apps** | Gmail requiere App Password, no password normal | Documentar claramente en README cómo generar App Password |

---

## 5. Recomendación de Arquitectura

### 5.1. Estructura de Archivos Propuesta

```
/home/eivorkinkest/Documentos/Docs_SENA/
├── diligenciar.py           # Script principal (modificar)
├── test_diligenciar.py      # Tests (modificar para mockear email)
├── .env                     # NUEVO: Variables de entorno (NO commitear)
├── .gitignore               # NUEVO: Excluir .env y otros
├── email_module.py          # NUEVO: Módulo de envío de email
├── requirements.txt         # NUEVO/OPTIONAL: Dependencias
└── DocsOriginales/
    └── output/
        └── bitacoraN-YYYY-MM-DD/
            ├── BitacoraMQuiazuaN.xlsx
            ├── Actas-Inicio-Medio-Final.docx
            └── ejecucion.log
```

### 5.2. Diseño del Módulo de Email (`email_module.py`)

**Enfoque recomendado:** Módulo funcional con una función principal y helpers.

```python
# email_module.py
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Tuple

# Constantes fijas
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
REMITENTE_FIJO = "jmqo2026@gmail.com"
CC_FIJO = "eivorkinkest@gmail.com"


def construir_asunto(bitacora_num: Optional[int], bitacora_data: Optional[dict], 
                     momento: Optional[int]) -> str:
    """Construye el asunto dinámico según los documentos generados."""
    pass


def construir_cuerpo(bitacora_data: Optional[dict], momento: Optional[int]) -> str:
    """Construye el cuerpo del email según la plantilla estandarizada."""
    pass


def adjuntar_archivos(message: MIMEMultipart, carpeta_salida: str) -> List[str]:
    """Adjunta todos los archivos .xlsx y .docx de la carpeta. Retorna lista de adjuntados."""
    pass


def enviar_email(destinatario: str, asunto: str, cuerpo: str, 
                 carpeta_salida: str, max_retries: int = 3) -> Tuple[bool, str]:
    """
    Función principal de envío.
    
    Args:
        destinatario: Email del instructor
        asunto: Asunto del correo
        cuerpo: Cuerpo del mensaje
        carpeta_salida: Ruta con los documentos a adjuntar
        max_retries: Número máximo de reintentos (default: 3)
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje de estado)
    """
    pass


def reintentar_envio_manual(bitacora_num: int, carpeta_salida: str) -> bool:
    """
    Ofrece reintento manual tras fallos automáticos.
    Pregunta al usuario y ejecuta envío.
    """
    pass
```

### 5.3. Integración en `diligenciar.py`

**Modificaciones mínimas requeridas:**

1. **Imports al inicio:**
```python
import os
import shutil
import json
import datetime
import argparse
import re
# ... imports existentes ...
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Imports del módulo de email (al final, después de definir funciones)
# Se importa al final para evitar circular dependencies si las hubiera
```

2. **Al inicio de `main()` (después de parse_args):**
```python
    # Preguntar autorización de email
    send_email = False
    if not args.dry_run:
        respuesta = input("\n¿Desea enviar por correo electrónico los documentos generados al finalizar? (s/n): ")
        send_email = respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']
    else:
        print("[Dry Run] Se simularía el envío de email al finalizar.")
```

3. **Al final de `main()` (antes del mensaje de éxito):**
```python
    # Envío de email si autorizado y hay documentos
    if send_email and not args.dry_run and log_dir:
        from email_module import enviar_email, reintentar_envio_manual
        
        destinatario = os.getenv("EMAIL_DESTINATARIO", "oiospina@sena.edu.co")
        asunto = construir_asunto(pending_num, bitacora_data, target_moment)
        cuerpo = construir_cuerpo(bitacora_data, target_moment)
        
        exito, mensaje = enviar_email(
            destinatario=destinatario,
            asunto=asunto,
            cuerpo=cuerpo,
            carpeta_salida=log_dir,
            max_retries=EMAIL_MAX_RETRIES
        )
        
        if exito:
            print(f"[Email] {mensaje}")
        else:
            print(f"[Email] {mensaje}")
            # Ofrecer reintento manual
            reintentar = input("¿Desea intentar enviar manualmente? (s/n): ")
            if reintentar.lower() in ['s', 'si', 'sí']:
                reintentar_envio_manual(pending_num, log_dir)
    elif send_email and args.dry_run:
        print("[Email Dry Run] Se habría enviado correo con:")
        print(f"  - Destinatario: {destinatario}")
        print(f"  - Asunto: {asunto}")
        print(f"  - Adjuntos: {archivos_en_carpeta(log_dir)}")
```

### 5.4. Consideraciones de Testing

**Para `test_diligenciar.py`:**

1. Agregar test unitario para `construir_asunto()`
2. Agregar test unitario para `construir_cuerpo()`
3. Mockear `smtplib.SMTP` en tests de integración
4. Verificar que `--dry-run` no envía emails reales

---

## 6. Resumen de Acciones Requeridas

| # | Acción | Archivo | Prioridad |
|---|--------|---------|-----------|
| 1 | Crear `.gitignore` en raíz | `.gitignore` | CRÍTICA |
| 2 | Crear `.env` con credenciales | `.env` | CRÍTICA |
| 3 | Crear módulo de email | `email_module.py` | ALTA |
| 4 | Modificar `main()` para pregunta | `diligenciar.py` | ALTA |
| 5 | Modificar `main()` para envío | `diligenciar.py` | ALTA |
| 6 | Agregar tests para email | `test_diligenciar.py` | MEDIA |
| 7 | Actualizar README con setup | `README.md` | MEDIA |
| 8 | Crear `requirements.txt` | `requirements.txt` | BAJA |

---

## 7. Conclusión

La arquitectura actual de `diligenciar.py` es **favorable para la integración** de la capa de email:

- ✅ Función `main()` bien estructurada con puntos claros de inserción
- ✅ Uso existente de `argparse` permite agregar flags fácilmente
- ✅ Patrón de logging ya implementado (archivo `ejecucion.log`)
- ✅ Carpeta de salida (`log_dir`) disponible con todos los documentos
- ✅ Modo `--dry-run` existente facilita testing sin envíos reales

**Puntos de atención:**
- ⚠️ No existe `.gitignore` - crear antes de `.env`
- ⚠️ Dependencia nueva `python-dotenv` requiere instalación
- ⚠️ Tests existentes deben actualizarse para mockear email

**Recomendación final:** Implementar el módulo de email como archivo separado (`email_module.py`) con funciones puras, manteniendo `diligenciar.py` limpio y facilitando el testing unitario aislado.
