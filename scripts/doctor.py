"""
doctor.py - Diagnostico completo del proyecto.

Verifica que todos los componentes esten en su lugar y funcionando.
Emite un reporte con problemas encontrados y sugerencias de solucion.

Modos:
    python scripts/doctor.py              # Modo humano: salida legible
    python scripts/doctor.py --ai-mode    # Modo agente: JSON estructurado

Exit codes:
    0  -> Todo OK
    1  -> Se encontraron problemas
    2  -> Problemas criticos (faltan plantillas o archivos esenciales)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Agregar scripts/ al path para imports
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import env_validator


BASE_DIR = Path(__file__).resolve().parent.parent
CONTEXTO_DIR = BASE_DIR / "contexto"
PLANTILLAS_DIR = CONTEXTO_DIR / "plantillas"
HISTORICO_PATH = CONTEXTO_DIR / "historico_actividades.md"
MEMORY_PATH = CONTEXTO_DIR / "memory_descriptions.md"
MENSAJE_PATH = CONTEXTO_DIR / "mensaje_instructor.md"

REQUIRED_PLACEHOLDERS = [
    "{{destinatario}}",
    "{{lista_bitacoras}}",
    "{{acta_moment}}",
    "{{firma}}",
    "{{fecha_ejecucion}}",
]


# ---------------------------------------------------------------------------
# Funciones de verificacion
# ---------------------------------------------------------------------------


def check_env():
    """Verifica que las 9 variables de entorno requeridas esten configuradas."""
    ok, missing, _ = env_validator.validate_env()
    if ok:
        return {
            "status": "ok",
            "details": "Todas las 9 variables de entorno requeridas estan configuradas.",
        }
    missing_keys = [v["key"] for v in missing]
    return {
        "status": "issues",
        "details": f"Faltan {len(missing)} variable(s) de entorno.",
        "missing": missing_keys,
    }


def check_context_files():
    """Verifica que los 3 archivos de contexto existan."""
    required = {
        "historico_actividades.md": HISTORICO_PATH,
        "memory_descriptions.md": MEMORY_PATH,
        "mensaje_instructor.md": MENSAJE_PATH,
    }
    missing = []
    for name, path in required.items():
        if not path.exists():
            missing.append(name)
    if missing:
        return {
            "status": "critical",
            "details": f"Faltan {len(missing)} archivo(s) de contexto.",
            "missing": missing,
        }
    return {"status": "ok", "details": "Los 3 archivos de contexto existen."}


def check_templates():
    """Verifica que las plantillas bitacoras.xlsx y actas.docx existan."""
    required = {
        "bitacoras.xlsx": PLANTILLAS_DIR / "bitacoras.xlsx",
        "actas.docx": PLANTILLAS_DIR / "actas.docx",
    }
    missing = []
    for name, path in required.items():
        if not path.exists():
            missing.append(name)
    if missing:
        return {
            "status": "critical",
            "details": f"Faltan {len(missing)} plantilla(s).",
            "missing": missing,
            "suggestion": "Ejecute: python scripts/reset.py --templates para regenerarlas desde GitHub.",
        }
    return {"status": "ok", "details": "Las 2 plantillas existen."}


def check_mensaje_instructor():
    """Verifica que mensaje_instructor.md contenga los 5 placeholders requeridos."""
    if not MENSAJE_PATH.exists():
        return {"status": "critical", "details": "El archivo mensaje_instructor.md no existe."}
    content = MENSAJE_PATH.read_text(encoding="utf-8")
    missing_placeholders = [p for p in REQUIRED_PLACEHOLDERS if p not in content]
    if missing_placeholders:
        return {
            "status": "issues",
            "details": f"Faltan {len(missing_placeholders)} placeholder(s) en el mensaje.",
            "missing_placeholders": missing_placeholders,
        }
    return {"status": "ok", "details": "El mensaje contiene los 5 placeholders requeridos."}


def check_bitacoras_pendientes():
    """Busca bitacoras en historico_actividades.md sin tag [DILIGENCIADA]."""
    if not HISTORICO_PATH.exists():
        return {
            "status": "ok",
            "details": "No se puede verificar (historico_actividades.md no existe).",
            "pending": [],
        }
    content = HISTORICO_PATH.read_text(encoding="utf-8")
    all_bitacoras = []
    pending = []
    for line in content.splitlines():
        m = re.search(r"##\s*[Bb]itacora\s*numero\s*(\d+)", line)
        if m:
            num = int(m.group(1))
            all_bitacoras.append(num)
            if "[DILIGENCIADA]" not in line:
                pending.append(num)
    return {
        "status": "ok",
        "details": f"{len(pending)} bitacora(s) pendiente(s) de {len(all_bitacoras)} total.",
        "pending": pending,
        "total": len(all_bitacoras),
    }


# ---------------------------------------------------------------------------
# Formateadores de salida
# ---------------------------------------------------------------------------


_SEP = "=" * 60


def report_human(checks):
    """Imprime diagnostico legible para humanos."""
    print(_SEP)
    print("  DOCTOR -- Diagnostico del Proyecto")
    print(_SEP)
    print()

    labels = {
        "env": "Entorno (.env)",
        "context_files": "Archivos de contexto",
        "templates": "Plantillas",
        "mensaje_instructor": "Mensaje al instructor",
        "bitacoras_pendientes": "Bitacoras pendientes",
    }

    for key, label in labels.items():
        c = checks[key]
        status = c["status"]
        if status == "ok":
            badge = "[OK]"
        elif status == "issues":
            badge = "[ISSUES]"
        else:
            badge = "[CRITICAL]"

        print(f"{badge}  {label}")
        print(f"      {c['details']}")
        if "missing" in c and c["missing"]:
            if isinstance(c["missing"], list):
                print(f"      Faltantes: {', '.join(str(x) for x in c['missing'])}")
        if "missing_placeholders" in c and c["missing_placeholders"]:
            print(f"      Faltantes: {', '.join(c['missing_placeholders'])}")
        if "suggestion" in c:
            print(f"      Sugerencia: {c['suggestion']}")
        if "pending" in c and c["pending"]:
            print(f"      Numeros: {c['pending']}")
        print()

    # Resumen
    print(_SEP)
    statuses = [c["status"] for c in checks.values()]
    n_issues = sum(1 for s in statuses if s != "ok")
    if n_issues == 0:
        print("  Resumen: Todo OK -- No se encontraron problemas.")
    else:
        print(f"  Resumen: {n_issues} problema(s) encontrado(s).")
    print(_SEP)


def report_ai(checks):
    """Imprime diagnostico estructurado en JSON para agentes de IA."""
    statuses = [c["status"] for c in checks.values()]
    if "critical" in statuses:
        overall = "critical"
    elif "issues" in statuses:
        overall = "issues"
    else:
        overall = "ok"

    suggestions = []
    if checks["env"]["status"] != "ok":
        suggestions.append("Ejecute: python scripts/setup.py para configurar el entorno")
    if checks["templates"]["status"] == "critical":
        suggestions.append("Ejecute: python scripts/reset.py --templates para regenerar plantillas")
    if checks["context_files"]["status"] == "critical":
        suggestions.append("Ejecute: python scripts/reset.py --context para regenerar archivos de contexto")
    if checks["mensaje_instructor"]["status"] != "ok":
        suggestions.append("Edite contexto/mensaje_instructor.md para agregar los placeholders faltantes")

    result = {
        "status": overall,
        "checks": checks,
        "suggestions": suggestions,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Diagnostico del proyecto.")
    parser.add_argument(
        "--ai-mode",
        action="store_true",
        help="Modo agente: salida JSON estructurada.",
    )
    args = parser.parse_args()

    checks = {
        "env": check_env(),
        "context_files": check_context_files(),
        "templates": check_templates(),
        "mensaje_instructor": check_mensaje_instructor(),
        "bitacoras_pendientes": check_bitacoras_pendientes(),
    }

    if args.ai_mode:
        report_ai(checks)
    else:
        report_human(checks)

    statuses = [c["status"] for c in checks.values()]
    if "critical" in statuses:
        return 2
    elif "issues" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
