"""
setup.py - Wizard interactivo y validador de variables de entorno.

Doble modo de operacion:

1. MODO HUMANO (sin --ai-mode):
   Wizard interactivo que pregunta cada variable por consola,
   valida formato y escribe/actualiza el archivo .env.

2. MODO AGENTE (con --ai-mode):
   Valida el .env sin interaccion. Imprime JSON estructurado a stdout:
     - status "ok" + exit code 0 si todo esta completo.
     - status "incomplete" + lista de variables faltantes + exit code 1
       si falta alguna variable (el agente debe preguntar al usuario
       y re-ejecutar este script).

Uso:
    python scripts/setup.py              # Modo humano (wizard)
    python scripts/setup.py --ai-mode    # Modo agente (JSON output)
    python scripts/setup.py --ai-mode --check   # Solo valida, nunca escribe

La logica de validacion esta en scripts/env_validator.py.
Este modulo solo agrega:
  - Wizard interactivo (modo humano)
  - Escritura del archivo .env
  - Entry point con argparse
"""

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio scripts/ al path para imports relativos
sys.path.insert(0, str(Path(__file__).resolve().parent))

import env_validator as ev
from env_validator import REQUIRED_VARS, ENV_PATH, BASE_DIR

ENV_EXAMPLE_PATH = BASE_DIR / ".env.example"


# =============================================================================
# Modo agente (--ai-mode)
# =============================================================================

def mode_ai(check_only: bool = False) -> int:
    """Valida .env y emite JSON estructurado a stdout.

    Returns:
        0 si todo OK, 1 si incompleto.
    """
    ok, missing, _ = ev.validate_env()
    if ok:
        ev.report_ai([])
        return 0
    ev.report_ai(missing)
    return 1


# =============================================================================
# Modo humano (wizard interactivo)
# =============================================================================

def mask_secret(value: str) -> str:
    """Enmascara un valor secreto mostrando solo los primeros/ultimos caracteres."""
    if not value:
        return "(vacio)"
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def prompt_value(var: dict, current_value: str = "") -> str:
    """Muestra el prompt para una variable y retorna el valor ingresado.

    Si current_value existe, lo muestra (enmascarado si es secreto) y permite
    mantenerlo presionando Enter.
    """
    key = var["key"]
    description = var["description"]
    example = var["example"]
    is_secret = var["secret"]
    validator = ev.VALIDATORS.get(key)

    print()
    print(f"  >> {key}")
    print(f"     {description}")
    print(f"     Ejemplo: {example}")

    if current_value:
        if is_secret:
            print(f"     Valor actual: {mask_secret(current_value)}")
        else:
            print(f"     Valor actual: {current_value}")

    prompt_label = (
        "     Nuevo valor (Enter para mantener actual): "
        if current_value
        else "     Ingrese el valor: "
    )

    while True:
        raw = input(prompt_label).strip()
        if not raw and current_value:
            return current_value
        if not raw and not current_value:
            print("     [ERROR] El valor no puede estar vacio.")
            continue
        if validator:
            error = validator(raw)
            if error:
                print(f"     [ERROR] {error}")
                continue
        return raw


def backup_existing_env() -> Path | None:
    """Crea un respaldo de .env con timestamp."""
    if not ENV_PATH.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BASE_DIR / f".env.backup-{timestamp}"
    try:
        shutil.copy2(ENV_PATH, backup_path)
        return backup_path
    except OSError as e:
        print(f"[Setup] Advertencia: no se pudo crear respaldo: {e}", file=sys.stderr)
        return None


def write_env_file(values: dict) -> bool:
    """Escribe el archivo .env con los valores provistos."""
    backup = backup_existing_env()
    if backup:
        print(f"[Setup] Respaldo creado: {backup.name}")

    sections = {
        "GMAIL_SENDER": "Credenciales Gmail",
        "GMAIL_APP_PASSWORD": "Credenciales Gmail",
        "EMAIL_DESTINATARIO_PRODUCCION": "Destinatarios",
        "EMAIL_DESTINATARIO_PRUEBAS": "Destinatarios",
        "EMAIL_CC": "Destinatarios",
        "EMAIL_MODO": "Modo de operacion",
    }
    lines = [
        "# ====================================================================",
        "# Variables de entorno - Docs SENA",
        "# ====================================================================",
        "# Archivo generado/editado por scripts/setup.py.",
        "# Nunca subir este archivo al repositorio (ya esta en .gitignore).",
        "# ====================================================================",
        "",
    ]
    current_section = None
    for var in REQUIRED_VARS:
        key = var["key"]
        section = sections.get(key, "")
        if section != current_section:
            lines.append("")
            lines.append(f"# --- {section} ---")
            current_section = section
        lines.append(f"# {var['description']}")
        lines.append(f"# Ejemplo: {var['example']}")
        lines.append(f"{key}={values.get(key, '')}")
    lines.append("")

    try:
        with ENV_PATH.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return True
    except OSError as e:
        print(f"[Setup] Error al escribir .env: {e}", file=sys.stderr)
        return False


def mode_human() -> int:
    """Wizard interactivo para humanos."""
    print("=" * 70)
    print("  SETUP - Configuracion de variables de entorno (Docs SENA)")
    print("=" * 70)
    print()
    print("Este wizard le guiara para configurar el archivo .env.")
    print("Si no existe, se creara desde cero. Si existe, podra mantener")
    print("los valores actuales o cambiarlos.")
    print()
    print("Si una IA lo esta ayudando, pidale que use 'setup.py --ai-mode'")
    print("y siga el flujo estructurado en JSON.")

    env_values = ev.collect_env_values()
    new_values = dict(env_values)

    for var in REQUIRED_VARS:
        key = var["key"]
        current = env_values.get(key, "")
        new_values[key] = prompt_value(var, current)

    print()
    print("=" * 70)
    print("  Resumen de valores a guardar:")
    print("=" * 70)
    for var in REQUIRED_VARS:
        key = var["key"]
        value = new_values.get(key, "")
        if var["secret"]:
            display = mask_secret(value)
        else:
            display = value if value else "(vacio)"
        print(f"  {key} = {display}")

    print()
    confirm = input("  ¿Guardar estos valores en .env? (s/n): ").strip().lower()
    if confirm not in ("s", "si", "y", "yes"):
        print()
        print("[Setup] Operacion cancelada por el usuario. No se escribio .env.")
        return 1

    if write_env_file(new_values):
        print()
        print(f"[Setup] Archivo .env escrito correctamente en: {ENV_PATH}")
        print("[Setup] Ya puede ejecutar: python scripts/diligenciar.py")
        return 0
    else:
        print()
        print("[Setup] ERROR: no se pudo escribir el archivo .env.", file=sys.stderr)
        return 1


# =============================================================================
# Entry point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Configurador de variables de entorno para Docs SENA."
    )
    parser.add_argument(
        "--ai-mode",
        action="store_true",
        help="Modo agente: valida .env y emite JSON estructurado a stdout (sin prompts).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Solo valida. Nunca escribe .env. Implica --ai-mode.",
    )
    args = parser.parse_args()

    if args.ai_mode or args.check:
        return mode_ai(check_only=args.check)
    else:
        return mode_human()


if __name__ == "__main__":
    sys.exit(main())