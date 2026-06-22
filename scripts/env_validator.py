"""
env_validator.py - Modulo compartido para validar variables de entorno.

Usado por:
    - scripts/setup.py  (wizard y modo agente)
    - scripts/diligenciar.py  (validacion previa al envio de correo)

NO escribe en .env. Solo valida y reporta.

Si el modo es "ai", imprime JSON estructurado a stdout.
Si el modo es "human", imprime mensajes legibles a stderr.
"""

import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

REQUIRED_VARS = [
    {
        "key": "GMAIL_SENDER",
        "description": "Correo Gmail remitente desde el que se envian los documentos",
        "example": "tu-correo@gmail.com",
        "secret": False,
    },
    {
        "key": "GMAIL_APP_PASSWORD",
        "description": "Contrasena de aplicacion de Google de 16 caracteres (NO es la contrasena normal)",
        "example": "abcd efgh ijkl mnop",
        "secret": True,
    },
    {
        "key": "EMAIL_DESTINATARIO_PRODUCCION",
        "description": "Correo del instructor SENA (modo produccion)",
        "example": "instructor@sena.edu.co",
        "secret": False,
    },
    {
        "key": "EMAIL_DESTINATARIO_PRUEBAS",
        "description": "Correo para pruebas (modo pruebas)",
        "example": "tu-correo-pruebas@gmail.com",
        "secret": False,
    },
    {
        "key": "EMAIL_CC",
        "description": "Correo en copia fijo para monitorizacion",
        "example": "tu-correo-cc@gmail.com",
        "secret": False,
    },
    {
        "key": "EMAIL_MODO",
        "description": "Modo de operacion: pruebas o produccion",
        "example": "pruebas",
        "secret": False,
    },
    {
        "key": "APRENDIZ_NOMBRE",
        "description": "Tu nombre completo de aprendiz",
        "example": "Tu Nombre Completo",
        "secret": False,
    },
    {
        "key": "EMPRESA_NOMBRE",
        "description": "Nombre de la empresa donde realizas la etapa productiva",
        "example": "Nombre de tu Empresa SAS",
        "secret": False,
    },
    {
        "key": "INSTRUCTOR_NOMBRE",
        "description": "Nombre completo del instructor SENA de seguimiento",
        "example": "Nombre del Instructor",
        "secret": False,
    },
]

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _validate_email(value):
    if not value or not value.strip():
        return "El correo no puede estar vacio."
    if not EMAIL_RE.match(value.strip()):
        return f"Formato de correo invalido: {value!r}."
    return None


def _validate_app_password(value):
    if not value or not value.strip():
        return "La contrasena no puede estar vacia."
    cleaned = value.replace(" ", "")
    if len(cleaned) != 16:
        return (
            "La contrasena de aplicacion debe tener 16 caracteres (sin espacios). "
            f"Longitud actual: {len(cleaned)}."
        )
    if not re.match(r"^[A-Za-z0-9 ]+$", value):
        return "La contrasena solo debe contener letras, numeros y espacios."
    return None


def _validate_modo(value):
    v = (value or "").strip().lower()
    if v not in ("pruebas", "produccion"):
        return f"EMAIL_MODO debe ser 'pruebas' o 'produccion'. Recibido: {value!r}."
    return None


def _validate_non_empty(value: str):
    """Valida que un campo de texto no este vacio y tenga al menos 2 palabras."""
    if not value or not value.strip():
        return "El valor no puede estar vacio."
    if len(value.strip().split()) < 2:
        return "Debe contener al menos nombre y apellido (minimo 2 palabras)."
    return None


VALIDATORS = {
    "GMAIL_SENDER": _validate_email,
    "GMAIL_APP_PASSWORD": _validate_app_password,
    "EMAIL_DESTINATARIO_PRODUCCION": _validate_email,
    "EMAIL_DESTINATARIO_PRUEBAS": _validate_email,
    "EMAIL_CC": _validate_email,
    "EMAIL_MODO": _validate_modo,
    "APRENDIZ_NOMBRE": _validate_non_empty,
    "EMPRESA_NOMBRE": _validate_non_empty,
    "INSTRUCTOR_NOMBRE": _validate_non_empty,
}


def parse_env_file(env_path=None):
    """Lee un archivo .env y retorna {KEY: value}. Solo lectura."""
    path = Path(env_path) if env_path else ENV_PATH
    env = {}
    if not path.exists():
        return env
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n").rstrip("\r")
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    continue
                key, _, value = stripped.partition("=")
                env[key.strip()] = value.strip()
    except OSError as e:
        print(f"[env_validator] Advertencia: no se pudo leer {path}: {e}", file=sys.stderr)
    return env


def collect_env_values(env_path=None):
    """Recolecta valores: prioridad os.environ > archivo .env."""
    file_env = parse_env_file(env_path)
    merged = {}
    for var in REQUIRED_VARS:
        key = var["key"]
        merged[key] = os.environ.get(key) or file_env.get(key, "")
    return merged


def find_missing(env_values):
    """Retorna REQUIRED_VARS que estan vacias o con valor invalido."""
    missing = []
    for var in REQUIRED_VARS:
        key = var["key"]
        value = env_values.get(key, "")
        validator = VALIDATORS.get(key)
        if validator is None:
            if not value:
                missing.append(var)
        else:
            if validator(value) is not None:
                missing.append(var)
    return missing


def validate_env(env_path=None):
    """Valida el entorno.

    Returns:
        (ok, missing, values): tupla con estado, variables faltantes, valores.
    """
    values = collect_env_values(env_path)
    missing = find_missing(values)
    return (len(missing) == 0, missing, values)


def report_human(missing, env_path=None):
    """Imprime mensaje legible a stderr para usuarios humanos."""
    path = Path(env_path) if env_path else ENV_PATH
    print(
        "[ERROR] Faltan variables de entorno requeridas en .env",
        file=sys.stderr,
    )
    print(f"[ERROR] Archivo .env: {path}", file=sys.stderr)
    print("[ERROR] Ejecute el wizard interactivo:", file=sys.stderr)
    print("         python scripts/setup.py", file=sys.stderr)
    print("[ERROR] Variables faltantes o invalidas:", file=sys.stderr)
    for var in missing:
        print(
            f"         - {var['key']}: {var['description']} (ej: {var['example']})",
            file=sys.stderr,
        )


def report_ai(missing, env_path=None):
    """Imprime JSON estructurado a stdout para agentes de IA."""
    path = str(env_path) if env_path else str(ENV_PATH)
    if not missing:
        result = {
            "status": "ok",
            "message": "Todas las variables de entorno requeridas estan configuradas.",
            "path": path,
        }
    else:
        result = {
            "status": "incomplete",
            "message": (
                "Faltan variables de entorno. El agente debe preguntar al usuario "
                "cada variable, escribir los valores en el archivo .env, y re-ejecutar "
                "el script para revalidar."
            ),
            "path": path,
            "missing": [
                {
                    "variable": v["key"],
                    "description": v["description"],
                    "example": v["example"],
                    "secret": v["secret"],
                }
                for v in missing
            ],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def require_env(mode="human", env_path=None):
    """Valida el entorno y reporta segun el modo.

    Args:
        mode: "human" (mensaje legible a stderr) o "ai" (JSON a stdout).
        env_path: Ruta al archivo .env.

    Returns:
        True si el entorno esta completo, False si falta algo.
    """
    ok, missing, _ = validate_env(env_path)
    if ok:
        return True
    if mode == "ai":
        report_ai(missing, env_path)
    else:
        report_human(missing, env_path)
    return False