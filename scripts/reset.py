"""
reset.py - Regenera archivos del proyecto desde cero.

Permite resetear partes del proyecto de forma selectiva:
    --templates    Regenera bitacoras.xlsx y actas.docx
    --context      Regenera historico_actividades.md, memory_descriptions.md, mensaje_instructor.md
    --env          Regenera .env desde .env.example
    --include-env  Incluye .env en --all (por defecto se excluye)
    --all          Regenera todo (excepto .env a menos que se incluya)
    --yes          No pedir confirmacion

Para las plantillas, intenta descargarlas desde GitHub. Si falla,
busca un backup local. Si ambos fallan, sugiere clonar el repositorio.

Uso:
    python scripts/reset.py --all
    python scripts/reset.py --templates
    python scripts/reset.py --context
    python scripts/reset.py --env
    python scripts/reset.py --all --include-env --yes
"""

import argparse
import json
import os
import shutil
import sys
import urllib.request
import urllib.error
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONTEXTO_DIR = BASE_DIR / "contexto"
PLANTILLAS_DIR = CONTEXTO_DIR / "plantillas"
PLANTILLAS_BACKUP_DIR = CONTEXTO_DIR / "plantillas_backup"
ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE_PATH = BASE_DIR / ".env.example"
HISTORICO_PATH = CONTEXTO_DIR / "historico_actividades.md"
MEMORY_PATH = CONTEXTO_DIR / "memory_descriptions.md"
MENSAJE_PATH = CONTEXTO_DIR / "mensaje_instructor.md"

# CONFIGURAR: Reemplazar con el owner/repo real de GitHub
GITHUB_REPO = "your-username/your-repo"
GITHUB_BRANCH = "main"

GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"


# ============================================================================
# Regeneracion de plantillas
# ============================================================================

def download_from_github(filename: str, dest: Path) -> bool:
    """Intenta descargar un archivo desde GitHub. Retorna True si tuvo exito."""
    url = f"{GITHUB_RAW_URL}/contexto/plantillas/{filename}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status != 200:
                return False
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as f:
                f.write(response.read())
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
        print(f"  [WARN] No se pudo descargar {filename} desde GitHub: {e}", file=sys.stderr)
        return False


def copy_from_backup(filename: str, dest: Path) -> bool:
    """Copia un archivo desde el backup local. Retorna True si tuvo exito."""
    src = PLANTILLAS_BACKUP_DIR / filename
    if not src.exists():
        return False
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return True
    except OSError as e:
        print(f"  [WARN] No se pudo copiar {filename} desde backup: {e}", file=sys.stderr)
        return False


def reset_template(filename: str) -> bool:
    """Regenera una plantilla individual. Retorna True si tuvo exito."""
    dest = PLANTILLAS_DIR / filename

    # Intentar GitHub primero
    print(f"  -> {filename}: intentando descargar desde GitHub...")
    if download_from_github(filename, dest):
        print(f"  [OK] {filename} descargado desde GitHub.")
        return True

    # Fallback a backup local
    print(f"  -> {filename}: intentando desde backup local...")
    if copy_from_backup(filename, dest):
        print(f"  [OK] {filename} copiado desde backup local.")
        return True

    # Si todo falla
    print(f"  [FAIL] No se pudo regenerar {filename}.")
    print(f"         Sugerencia: clone el repositorio nuevamente o restaure el archivo manualmente.")
    return False


def reset_templates() -> bool:
    """Regenera ambas plantillas. Retorna True si ambas tuvieron exito."""
    print("[Plantillas]")
    results = []
    for filename in ["bitacoras.xlsx", "actas.docx"]:
        results.append(reset_template(filename))
    return all(results)


# ============================================================================
# Regeneracion de archivos de contexto
# ============================================================================

HISTORICO_TEMPLATE = """# Historico de Actividades

Este es un markdown que se actualiza de manera manual. Su unica funcion es
alimentar el script que diligencia automaticamente cada una de las bitacoras
que se deben presentar al instructor de seguimiento.

---

> [!WARNING]
> **Importante:**
> Estos datos cambian en funcion de las actividades que usted haya realizado.
> Puede decirle a un agente de IA que redacte el contenido aqui, o hacerlo
> manualmente siguiendo este formato. **No olvide quitar `[DILIGENCIADA]`**
> de otra manera el script se saltara esa bitacora.

---

## Bitacora numero 1 - (FECHA_INICIO al FECHA_FIN)

- (Describa la primera actividad realizada en este periodo)
- (Describa la segunda actividad)

"""


MEMORY_TEMPLATE = """# Registro de Razonamiento: Descripciones, Evidencias e Inferencias

Este archivo contiene el razonamiento contextual inferido por el agente de IA.
Decopla la inferencia de la ejecucion fisica de los scripts de automatizacion.

```json
{
  "bitacoras": [],
  "actas": {
    "momento_2": {
      "fecha": "",
      "observaciones_instructor": "",
      "observaciones_aprendiz": "",
      "observaciones_coformador": "",
      "compromisos_mejora": ""
    },
    "momento_3": {
      "fecha": "",
      "observaciones_instructor": "",
      "observaciones_aprendiz": "",
      "observaciones_coformador": "",
      "compromisos_mejora": ""
    }
  }
}
```
"""


MENSAJE_TEMPLATE = """# Plantilla del Mensaje al Instructor

> Este archivo es la plantilla del cuerpo del correo electronico que se envia
> al instructor SENA con los documentos de bitacoras y actas.
>
> **El usuario puede editar este archivo libremente** para personalizar el mensaje.
> El script leera este archivo y reemplazara los placeholders con los datos reales.
>
> **Placeholders disponibles:**
> - `{{destinatario}}` - Nombre del instructor destinatario
> - `{{lista_bitacoras}}` - Lista de bitacoras con sus periodos
> - `{{acta_moment}}` - Numero del momento del acta (2 o 3), o vacio
> - `{{firma}}` - Tu nombre y empresa
> - `{{fecha_ejecucion}}` - Fecha de ejecucion del script

---

Estimado {{destinatario}},

Reciba un cordial saludo. Por medio del presente correo, hago entrega de las
bitacoras correspondientes a mi etapa productiva, las cuales detallo a continuacion:

{{lista_bitacoras}}
{{acta_moment}}

Nos gustaria saber si para la proxima semana o esta tiene disponibilidad para
las correspondientes visitas.

No siendo mas, agradecemos su tiempo y atencion.

Cordialmente,
{{firma}}
"""


def reset_context() -> bool:
    """Regenera los 3 archivos de contexto."""
    print("[Archivos de contexto]")
    success = True
    for path, content, name in [
        (HISTORICO_PATH, HISTORICO_TEMPLATE, "historico_actividades.md"),
        (MEMORY_PATH, MEMORY_TEMPLATE, "memory_descriptions.md"),
        (MENSAJE_PATH, MENSAJE_TEMPLATE, "mensaje_instructor.md"),
    ]:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"  [OK] {name} regenerado.")
        except OSError as e:
            print(f"  [FAIL] No se pudo escribir {name}: {e}", file=sys.stderr)
            success = False
    return success


# ============================================================================
# Regeneracion de .env
# ============================================================================

def reset_env() -> bool:
    """Regenera .env desde .env.example."""
    print("[.env]")
    if not ENV_EXAMPLE_PATH.exists():
        print(f"  [FAIL] No se encontro {ENV_EXAMPLE_PATH}.", file=sys.stderr)
        return False

    # Hacer backup del .env actual si existe
    if ENV_PATH.exists():
        backup = ENV_PATH.with_suffix(f".backup-{os.getpid()}")
        try:
            shutil.copy2(ENV_PATH, backup)
            print(f"  [INFO] Backup del .env actual: {backup.name}")
        except OSError as e:
            print(f"  [WARN] No se pudo hacer backup: {e}", file=sys.stderr)

    try:
        shutil.copy2(ENV_EXAMPLE_PATH, ENV_PATH)
        print(f"  [OK] .env regenerado desde .env.example (valores vacios, ejecute setup.py).")
        return True
    except OSError as e:
        print(f"  [FAIL] No se pudo escribir .env: {e}", file=sys.stderr)
        return False


# ============================================================================
# Main
# ============================================================================

def confirm(prompt: str, args_yes: bool) -> bool:
    """Pide confirmacion al usuario. Retorna True si confirma."""
    if args_yes:
        return True
    resp = input(f"{prompt} (s/n): ").strip().lower()
    return resp in ("s", "si", "y", "yes")


def main():
    parser = argparse.ArgumentParser(description="Regenera archivos del proyecto desde cero.")
    parser.add_argument("--templates", action="store_true", help="Regenera plantillas.")
    parser.add_argument("--context", action="store_true", help="Regenera archivos de contexto.")
    parser.add_argument("--env", action="store_true", help="Regenera .env.")
    parser.add_argument("--all", action="store_true", help="Regenera todo (excepto .env).")
    parser.add_argument("--include-env", action="store_true", help="Incluir .env en --all.")
    parser.add_argument("--yes", action="store_true", help="No pedir confirmacion.")
    parser.add_argument("--ai-mode", action="store_true", help="Modo agente: salida JSON.")
    args = parser.parse_args()

    # Si no se pasa ningun flag, usar --all
    if not any([args.templates, args.context, args.env, args.all]):
        args.all = True

    do_templates = args.templates or args.all
    do_context = args.context or args.all
    do_env = args.env or (args.all and args.include_env)

    # Confirmacion
    if not args.ai_mode and not args.yes:
        print("=== RESET - Regeneracion de archivos del proyecto ===\n")
        actions = []
        if do_templates:
            actions.append("- Plantillas (bitacoras.xlsx, actas.docx)")
        if do_context:
            actions.append("- Archivos de contexto (historico, memory, mensaje)")
        if do_env:
            actions.append("- .env (se hara backup primero)")
        if not actions:
            print("No hay acciones para ejecutar. Use --templates, --context, --env, o --all.")
            return 0
        print("Se regeneraran los siguientes archivos:")
        for a in actions:
            print(f"  {a}")
        if not confirm("\n¿Continuar?", args.yes):
            print("Operacion cancelada.")
            return 1
        print()

    results = {}
    if do_templates:
        results["templates"] = "ok" if reset_templates() else "fail"
    if do_context:
        results["context"] = "ok" if reset_context() else "fail"
    if do_env:
        results["env"] = "ok" if reset_env() else "fail"

    if args.ai_mode:
        # Modo agente: JSON
        all_ok = all(v == "ok" for v in results.values())
        print(json.dumps({
            "status": "ok" if all_ok else "partial" if any(v == "ok" for v in results.values()) else "fail",
            "actions": results,
        }, ensure_ascii=False, indent=2))

    return 0 if all(v == "ok" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
