"""
test_doctor.py - Tests para scripts/doctor.py.

Cubre:
    - check_env: valida que .env tiene las 9 variables requeridas.
    - check_context_files: verifica existencia de los 3 archivos de contexto.
    - check_templates: verifica existencia de plantillas xlsx/docx.
    - check_mensaje_instructor: verifica los 5 placeholders requeridos.
    - check_bitacoras_pendientes: detecta bitacoras sin [DILIGENCIADA].
    - report_human / report_ai: formateadores de salida.
    - Integracion: ejecucion como subproceso.

Autor: Tester Agent
Fecha: 2026-06-22
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Asegurar que scripts/ esta en sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import env_validator  # noqa: E402
import doctor  # noqa: E402


# =============================================================================
# TestDoctorChecks — tests unitarios de funciones de verificacion
# =============================================================================


class TestDoctorChecks(unittest.TestCase):
    """Tests para las funciones check_* de doctor.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Guardar paths originales
        self._orig_con = doctor.CONTEXTO_DIR
        self._orig_hist = doctor.HISTORICO_PATH
        self._orig_mem = doctor.MEMORY_PATH
        self._orig_men = doctor.MENSAJE_PATH
        self._orig_plant = doctor.PLANTILLAS_DIR
        self._orig_env_path = env_validator.ENV_PATH

        # Redirigir a directorio temporal
        tmp_con = Path(self.tmpdir) / "contexto"
        tmp_plant = tmp_con / "plantillas"
        tmp_con.mkdir(parents=True, exist_ok=True)
        tmp_plant.mkdir(parents=True, exist_ok=True)

        doctor.CONTEXTO_DIR = tmp_con
        doctor.HISTORICO_PATH = tmp_con / "historico_actividades.md"
        doctor.MEMORY_PATH = tmp_con / "memory_descriptions.md"
        doctor.MENSAJE_PATH = tmp_con / "mensaje_instructor.md"
        doctor.PLANTILLAS_DIR = tmp_plant
        env_validator.ENV_PATH = Path(self.tmpdir) / ".env"

        # Limpiar variables de entorno para aislar tests
        self._saved_env = {}
        for var in env_validator.REQUIRED_VARS:
            key = var["key"]
            self._saved_env[key] = os.environ.pop(key, None)

    def tearDown(self):
        # Restaurar paths originales
        doctor.CONTEXTO_DIR = self._orig_con
        doctor.HISTORICO_PATH = self._orig_hist
        doctor.MEMORY_PATH = self._orig_mem
        doctor.MENSAJE_PATH = self._orig_men
        doctor.PLANTILLAS_DIR = self._orig_plant
        env_validator.ENV_PATH = self._orig_env_path

        # Restaurar variables de entorno
        for key, value in self._saved_env.items():
            if value is not None:
                os.environ[key] = value

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_env_all_vars(self):
        """Escribe un .env con las 9 variables requeridas y validas."""
        content = (
            "GMAIL_SENDER=test@gmail.com\n"
            "GMAIL_APP_PASSWORD=abcdefghijklmnop\n"
            "EMAIL_DESTINATARIO_PRODUCCION=prod@sena.edu.co\n"
            "EMAIL_DESTINATARIO_PRUEBAS=test@gmail.com\n"
            "EMAIL_CC=cc@gmail.com\n"
            "EMAIL_MODO=pruebas\n"
            "APRENDIZ_NOMBRE=Juan Perez\n"
            "EMPRESA_NOMBRE=Mi Empresa SAS\n"
            "INSTRUCTOR_NOMBRE=Carlos Lopez\n"
        )
        env_validator.ENV_PATH.write_text(content, encoding="utf-8")

    def _write_mensaje_with_placeholders(self):
        """Escribe mensaje_instructor.md con los 5 placeholders."""
        content = (
            "# Mensaje\n\n"
            "Estimado {{destinatario}},\n\n"
            "{{lista_bitacoras}}\n"
            "{{acta_moment}}\n\n"
            "Cordialmente,\n"
            "{{firma}}\n"
            "{{fecha_ejecucion}}\n"
        )
        doctor.MENSAJE_PATH.write_text(content, encoding="utf-8")

    # ---- check_env ----

    def test_check_env_ok(self):
        """Con las 9 variables configuradas, retorna status='ok'."""
        self._write_env_all_vars()
        result = doctor.check_env()
        self.assertEqual(result["status"], "ok")
        self.assertIn("9", result["details"])

    def test_check_env_incomplete(self):
        """Con .env vacio, retorna status='issues' con 9 missing keys."""
        env_validator.ENV_PATH.write_text("", encoding="utf-8")
        result = doctor.check_env()
        self.assertEqual(result["status"], "issues")
        self.assertEqual(len(result["missing"]), 9)

    # ---- check_context_files ----

    def test_check_context_files_ok(self):
        """Con los 3 archivos presentes, retorna status='ok'."""
        for name in ["historico_actividades.md", "memory_descriptions.md", "mensaje_instructor.md"]:
            (doctor.CONTEXTO_DIR / name).write_text("contenido", encoding="utf-8")
        result = doctor.check_context_files()
        self.assertEqual(result["status"], "ok")

    def test_check_context_files_missing(self):
        """Con 1+ archivos faltantes, retorna status='critical'."""
        # No creamos ningun archivo
        result = doctor.check_context_files()
        self.assertEqual(result["status"], "critical")
        self.assertEqual(len(result["missing"]), 3)

    # ---- check_templates ----

    def test_check_templates_ok(self):
        """Con ambos archivos presentes, retorna status='ok'."""
        (doctor.PLANTILLAS_DIR / "bitacoras.xlsx").write_bytes(b"fake-xlsx")
        (doctor.PLANTILLAS_DIR / "actas.docx").write_bytes(b"fake-docx")
        result = doctor.check_templates()
        self.assertEqual(result["status"], "ok")

    def test_check_templates_missing(self):
        """Con archivos faltantes, retorna status='critical' con sugerencia."""
        result = doctor.check_templates()
        self.assertEqual(result["status"], "critical")
        self.assertEqual(len(result["missing"]), 2)
        self.assertIn("suggestion", result)
        self.assertIn("reset.py", result["suggestion"])

    # ---- check_mensaje_instructor ----

    def test_check_mensaje_instructor_ok(self):
        """Con los 5 placeholders presentes, retorna status='ok'."""
        self._write_mensaje_with_placeholders()
        result = doctor.check_mensaje_instructor()
        self.assertEqual(result["status"], "ok")
        self.assertIn("5", result["details"])

    def test_check_mensaje_instructor_missing_placeholders(self):
        """Con placeholders faltantes, retorna status='issues'."""
        doctor.MENSAJE_PATH.write_text(
            "Estimado {{destinatario}},\nSolo eso.\n",
            encoding="utf-8",
        )
        result = doctor.check_mensaje_instructor()
        self.assertEqual(result["status"], "issues")
        self.assertIn("missing_placeholders", result)
        self.assertGreater(len(result["missing_placeholders"]), 0)

    def test_check_mensaje_instructor_file_missing(self):
        """Si el archivo no existe, retorna status='critical'."""
        # No creamos el archivo
        result = doctor.check_mensaje_instructor()
        self.assertEqual(result["status"], "critical")

    # ---- check_bitacoras_pendientes ----

    def test_check_bitacoras_pendientes(self):
        """Cuando historico tiene bitacoras, retorna lista de numeros pendientes."""
        content = (
            "# Historico\n\n"
            "## Bitacora numero 1 - (08/04/2026 al 22/04/2026) [DILIGENCIADA]\n"
            "- Act 1\n"
            "## Bitacora numero 2 - (22/04/2026 al 06/05/2026)\n"
            "- Act 2\n"
            "## Bitacora numero 3 - (06/05/2026 al 20/05/2026)\n"
            "- Act 3\n"
        )
        doctor.HISTORICO_PATH.write_text(content, encoding="utf-8")
        result = doctor.check_bitacoras_pendientes()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["pending"], [2, 3])
        self.assertEqual(result["total"], 3)

    def test_check_bitacoras_pendientes_all_diligenciadas(self):
        """Cuando todas tienen [DILIGENCIADA], retorna lista vacia."""
        content = (
            "# Historico\n\n"
            "## Bitacora numero 1 - (08/04/2026 al 22/04/2026) [DILIGENCIADA]\n"
            "- Act 1\n"
            "## Bitacora numero 2 - (22/04/2026 al 06/05/2026) [DILIGENCIADA]\n"
            "- Act 2\n"
        )
        doctor.HISTORICO_PATH.write_text(content, encoding="utf-8")
        result = doctor.check_bitacoras_pendientes()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["pending"], [])

    def test_check_bitacoras_pendientes_sin_archivo(self):
        """Si el historico no existe, retorna ok con lista vacia."""
        result = doctor.check_bitacoras_pendientes()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["pending"], [])


# =============================================================================
# TestDoctorOutput — tests para formateadores de salida
# =============================================================================


class TestDoctorOutput(unittest.TestCase):
    """Tests para report_human() y report_ai()."""

    def _all_ok_checks(self):
        """Retorna un dict de checks todos en 'ok'."""
        return {
            "env": {"status": "ok", "details": "OK"},
            "context_files": {"status": "ok", "details": "OK"},
            "templates": {"status": "ok", "details": "OK"},
            "mensaje_instructor": {"status": "ok", "details": "OK"},
            "bitacoras_pendientes": {"status": "ok", "details": "OK", "pending": []},
        }

    def _critical_checks(self):
        """Retorna un dict de checks con problemas criticos."""
        return {
            "env": {"status": "ok", "details": "OK"},
            "context_files": {
                "status": "critical",
                "details": "Faltan 3 archivo(s) de contexto.",
                "missing": ["a.md", "b.md", "c.md"],
            },
            "templates": {
                "status": "critical",
                "details": "Faltan 2 plantilla(s).",
                "missing": ["x.xlsx", "y.docx"],
                "suggestion": "Ejecute reset.py",
            },
            "mensaje_instructor": {"status": "ok", "details": "OK"},
            "bitacoras_pendientes": {"status": "ok", "details": "OK", "pending": []},
        }

    def test_report_human_ok(self):
        """Cuando todo esta OK, la salida no tiene [CRITICAL] ni [ISSUES]."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            doctor.report_human(self._all_ok_checks())
        output = buf.getvalue()
        self.assertIn("DOCTOR", output)
        self.assertNotIn("[CRITICAL]", output)
        self.assertNotIn("[ISSUES]", output)
        self.assertIn("Todo OK", output)

    def test_report_human_critical(self):
        """Con problemas criticos, la salida tiene [CRITICAL] y resumen."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            doctor.report_human(self._critical_checks())
        output = buf.getvalue()
        self.assertIn("[CRITICAL]", output)
        self.assertIn("Resumen", output)
        self.assertIn("problema", output)

    def test_report_ai_structure(self):
        """report_ai produce JSON valido con status, checks, suggestions."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            doctor.report_ai(self._all_ok_checks())
        data = json.loads(buf.getvalue())
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("suggestions", data)
        self.assertEqual(data["status"], "ok")

    def test_report_ai_critical(self):
        """Con checks criticos, report_ai produce status='critical'."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            doctor.report_ai(self._critical_checks())
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], "critical")
        self.assertGreater(len(data["suggestions"]), 0)


# =============================================================================
# TestDoctorIntegration — tests de integracion con subproceso
# =============================================================================


class TestDoctorIntegration(unittest.TestCase):
    """Tests end-to-end ejecutando doctor.py como subproceso."""

    def test_doctor_human_mode_runs(self):
        """Ejecuta doctor.py sin flags; verifica exit code y titulo."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "doctor.py")],
            capture_output=True,
            text=True,
        )
        self.assertIn(result.returncode, [0, 1, 2])
        self.assertIn("DOCTOR", result.stdout)

    def test_doctor_ai_mode_runs(self):
        """Ejecuta doctor.py --ai-mode; verifica JSON con claves esperadas."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "doctor.py"), "--ai-mode"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("suggestions", data)


if __name__ == "__main__":
    unittest.main()
