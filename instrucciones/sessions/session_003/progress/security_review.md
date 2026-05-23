# Revisión de Seguridad - Capa de Email
## Sesión 003 - Auditoría de Seguridad

---

## 1. Checklist de Seguridad

| # | Ítem | Estado | Observaciones |
|---|------|--------|---------------|
| 1 | `.env` excluido en `.gitignore` | ✅ | `.env`, `.env.local`, `.env.*.local` correctamente excluidos |
| 2 | No hay credenciales hardcodeadas en `.py` | ✅ | Credenciales leídas exclusivamente desde `os.getenv()` |
| 3 | Conexión SMTP usa TLS/SSL | ✅ | `server.starttls()` en puerto 587 (línea 99) |
| 4 | Las credenciales no se loguean | ✅ | No hay `print()` de contraseñas ni variables sensibles |
| 5 | Los errores no exponen información sensible | ⚠️ | **PENDIENTE**: El mensaje de error en línea 121 revela `GMAIL_APP_PASSWORD` en texto |
| 6 | Los tests no usan credenciales reales | ✅ | Tests usan mocks (`@patch.dict`) con passwords de prueba |
| 7 | Permisos de archivo apropiados para `.env` | ❌ | **CRÍTICO**: Permisos 664 (rw-rw-r--) - cualquier usuario del grupo puede leer |

---

## 2. Vulnerabilidades Identificadas

### VULNERABILIDAD 1: Permisos de archivo excesivos en `.env`

- **Descripción**: El archivo `.env` tiene permisos 664 (`rw-rw-r--`), permitiendo que cualquier usuario del mismo grupo pueda leer las credenciales.
- **Severidad**: **Crítica**
- **Ubicación**: `/home/eivorkinkest/Documentos/Docs_SENA/.env` (permisos 664)
- **Recomendación de fix**:
  ```bash
  chmod 600 /home/eivorkinkest/Documentos/Docs_SENA/.env
  ```
  Esto limita los permisos a solo el propietario (`rw-------`).

---

### VULNERABILIDAD 2: Error SMTP expone nombre de variable de configuración

- **Descripción**: Cuando falla la autenticación SMTP, el mensaje de error incluye `"Verifique GMAIL_APP_PASSWORD."` (línea 121), revelando el nombre exacto de la variable de entorno que contiene la credencial.
- **Severidad**: **Media**
- **Ubicación**: `email_module.py`, líneas 118-122
- **Código actual**:
  ```python
  return (
      False,
      "Error de autenticación SMTP."
      " Verifique GMAIL_APP_PASSWORD.",
  )
  ```
- **Recomendación de fix**:
  ```python
  return (
      False,
      "Error de autenticación SMTP."
      " Verifique las credenciales de correo en .env",
  )
  ```

---

## 3. Recomendaciones de Hardening

### 3.1 Configuración de SMTP más segura

| Recomendación | Prioridad | Descripción |
|---------------|-----------|-------------|
| Usar App Password específico para la aplicación | Alta | Crear una App Password dedicada en Gmail, no usar la contraseña personal |
| Implementar validación de certificados SSL | Media | Considerar `context=ssl.create_default_context()` para verificación de certificados |
| Limitar intentos de reintento | Baja | El código actual reintenta 3 veces; considerar reducir a 2 en producción |

### 3.2 Validación de inputs

| Recomendación | Prioridad | Descripción |
|---------------|-----------|-------------|
| Validar formato de email | Media | Implementar validación con regex para `destinatario`, `cc` antes de enviar |
| Sanitizar nombres de archivo adjuntos | Media | `os.path.basename()` ya se usa, pero validar extensiones permitidas (.xlsx, .docx) |
| Verificar tamaño de archivos adjuntos | Baja | Considerar límite máximo (ej. 10MB) antes de adjuntar |

### 3.3 Manejo de errores seguro

| Recomendación | Prioridad | Descripción |
|---------------|-----------|-------------|
| No exponer variables de entorno en errores | Alta | Cambiar mensajes de error para no revelar nombres de variables |
| Loguear errores sin detalles sensibles | Alta | Usar logging en lugar de print, sin filtrar información sensible |
| Implementar circuit breaker | Baja | Para evitar múltiples intentos consecutivos en caso de falla sostenida |

### 3.4 Mejores prácticas de almacenamiento de secrets

| Recomendación | Prioridad | Descripción |
|---------------|-----------|-------------|
| Migrar a AWS Secrets Manager o similar | Alta | Para despliegues en AWS, considerar storing secrets en servicio dedicado |
| Rotación de App Password periódica | Media | Implementar política de rotación cada 90 días |
| Usar `.env.example` con valores dummy | Baja | Crear archivo de ejemplo para referencia sin valores reales |

---

## 4. Veredicto Final

### ¿Es seguro para producción?

**Condicional (Sí con reservas)**

### Resumen Ejecutivo

La implementación de la capa de email cumple con la mayoría de las mejores prácticas de seguridad:

✅ **Fortalezas**:
- Credenciales almacenadas en `.env` y correctamente excluidas del repositorio
- Conexión SMTP segura con STARTTLS en puerto 587
- No hay credenciales hardcodeadas en el código
- Tests utilizan mocks, no credenciales reales
- Manejo de reintentos implementa delay exponencial básico

⚠️ **Concerns que deben resolverse antes de producción**:
1. **Permisos 664 en `.env`** deben cambiarse a 600 (Crítico)
2. **Mensaje de error** expone nombre de variable (Medio - debe corregirse)

### Acción Requerida

Antes de pasar a producción, se deben implementar las siguientes correcciones mandatory:

1. ```bash
   chmod 600 /home/eivorkinkest/Documentos/Docs_SENA/.env
   ```

2. Modificar `email_module.py` línea 121 para quitar referencia a `GMAIL_APP_PASSWORD`:
   ```python
   # Cambiar:
   " Verifique GMAIL_APP_PASSWORD.",
   # Por:
   " Verifique las credenciales de correo en .env",
   ```

Una vez aplicadas estas correcciones, el módulo estará listo para uso en producción.

---

## 5. Metadata de Auditoría

| Campo | Valor |
|-------|-------|
| Fecha de auditoría | 2026-05-23 |
| Auditor | Security Agent |
| Archivos revisados | `.env`, `.gitignore`, `email_module.py`, `diligenciar.py`, `test_email_module.py` |
| Permisos de `.env` | 664 (debe ser 600) |
| Línea con fuga de información | `email_module.py:121` |
