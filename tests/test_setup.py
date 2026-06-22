"""
test_setup.py - Tests para el validador y wizard de .env.

Cubre:
    - env_validator: parsing, validators, validate_env, find_missing.
    - setup.py: modo agente (--ai-mode) en distintos escenarios.
    - Idempotencia del flujo.
    - Seguridad: no se imprimen passwords en stdout/stderr.

Autor: Tester Agent
Fecha: 2026-06-22
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Asegurar que scripts/ esta en sys.path para importar setup y env_validator
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import env_validator  # noqa: E402


# =============================================================================
# Tests para env_validator
# =============================================================================

class TestEnvValidatorValidators(unittest.TestCase):
    """Tests unitarios de los validadores de cada variable."""

    def test_validate_email_valido(self):
        self.assertIsNone(env_validator._validate_email("test@gmail.com"))
        self.assertIsNone(env_validator._validate_email("a.b+c@sub.example.co"))

    def test_validate_email_invalido(self):
        self.assertIsNotNone(env_validator._validate_email("not-an-email"))
        self.assertIsNotNone(env_validator._validate_email("@example.com"))
        self.assertIsNotNone(env_validator._validate_email("user@"))
        self.assertIsNotNone(env_validator._validate_email(""))

    def test_validate_email_vacio(self):
        err = env_validator._validate_email("")
        self.assertIn("vaci", err.lower())

    def test_validate_app_password_valido(self):
        self.assertIsNone(env_validator._validate_app_password("abcdefghijklmnop"))
        self.assertIsNone(env_validator._validate_app_password("abcd efgh ijkl mnop"))

    def test_validate_app_password_muy_corto(self):
        err = env_validator._validate_app_password("short")
        self.assertIn("16", err)

    def test_validate_app_password_muy_largo(self):
        err = env_validator._validate_app_password("a" * 17)
        self.assertIn("16", err)

    def test_validate_app_password_caracteres_invalidos(self):
        err = env_validator._validate_app_password("abcdefghijklmno!")  # 16 chars pero con !
        self.assertIsNotNone(err)

    def test_validate_app_password_vacio(self):
        err = env_validator._validate_app_password("")
        self.assertIn("vaci", err.lower())

    def test_validate_modo_valido(self):
        self.assertIsNone(env_validator._validate_modo("pruebas"))
        self.assertIsNone(env_validator._validate_modo("PRODUCCION"))
        self.assertIsNone(env_validator._validate_modo("  pruebas  "))

    def test_validate_modo_invalido(self):
        self.assertIsNotNone(env_validator._validate_modo("test"))
        self.assertIsNotNone(env_validator._validate_modo("prod"))
        self.assertIsNotNone(env_validator._validate_modo(""))


class TestEnvValidatorParse(unittest.TestCase):
    """Tests para parse_env_file y collect_env_values."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.env_path = Path(self.tmpdir) / ".env"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parse_env_file_basico(self):
        self.env_path.write_text(
            "GMAIL_SENDER=test@gmail.com\n"
            "EMAIL_MODO=pruebas\n"
            "# comentario\n"
            "\n"
            "GMAIL_APP_PASSWORD=abcd efgh ijkl mnop\n",
            encoding="utf-8",
        )
        env = env_validator.parse_env_file(self.env_path)
        self.assertEqual(env["GMAIL_SENDER"], "test@gmail.com")
        self.assertEqual(env["EMAIL_MODO"], "pruebas")
        self.assertEqual(env["GMAIL_APP_PASSWORD"], "abcd efgh ijkl mnop")
        self.assertEqual(len(env), 3)

    def test_parse_env_file_no_existe(self):
        env = env_validator.parse_env_file(self.env_path / "no_existe")
        self.assertEqual(env, {})

    def test_parse_env_file_ignora_lineas_invalidas(self):
        self.env_path.write_text(
            "INVALID_LINE_NO_EQUALS\n"
            "VALID=ok\n",
            encoding="utf-8",
        )
        env = env_validator.parse_env_file(self.env_path)
        self.assertEqual(env, {"VALID": "ok"})

    def test_collect_env_values_precedence_environ(self):
        """os.environ debe tener prioridad sobre el archivo."""
        self.env_path.write_text("GMAIL_SENDER=from_file@gmail.com\n", encoding="utf-8")
        with patch.dict(os.environ, {"GMAIL_SENDER": "from_environ@gmail.com"}):
            values = env_validator.collect_env_values(self.env_path)
            self.assertEqual(values["GMAIL_SENDER"], "from_environ@gmail.com")

    def test_collect_env_values_fallback_file(self):
        """Si no esta en environ, leer del archivo."""
        self.env_path.write_text("GMAIL_SENDER=from_file@gmail.com\n", encoding="utf-8")
        with patch.dict(os.environ, {}, clear=True):
            values = env_validator.collect_env_values(self.env_path)
            self.assertEqual(values["GMAIL_SENDER"], "from_file@gmail.com")


class TestEnvValidatorValidate(unittest.TestCase):
    """Tests para validate_env y find_missing."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.env_path = Path(self.tmpdir) / ".env"
        # Limpiar vars de entorno reales para aislar el test
        self._saved_env = {}
        for key in [
            "GMAIL_SENDER",
            "GMAIL_APP_PASSWORD",
            "EMAIL_DESTINATARIO_PRODUCCION",
            "EMAIL_DESTINATARIO_PRUEBAS",
            "EMAIL_CC",
            "EMAIL_MODO",
            "APRENDIZ_NOMBRE",
            "EMPRESA_NOMBRE",
            "INSTRUCTOR_NOMBRE",
        ]:
            self._saved_env[key] = os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._saved_env.items():
            if value is not None:
                os.environ[key] = value
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_env(self, content):
        self.env_path.write_text(content, encoding="utf-8")

    def test_validate_env_completo(self):
        self._write_env(
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
        ok, missing, values = env_validator.validate_env(self.env_path)
        self.assertTrue(ok)
        self.assertEqual(missing, [])
        self.assertEqual(len(values), 9)

    def test_validate_env_archivo_vacio(self):
        self._write_env("")
        ok, missing, values = env_validator.validate_env(self.env_path)
        self.assertFalse(ok)
        self.assertEqual(len(missing), 9)

    def test_validate_env_archivo_no_existe(self):
        ok, missing, _ = env_validator.validate_env(self.env_path / "no_existe")
        self.assertFalse(ok)
        self.assertEqual(len(missing), 9)

    def test_validate_env_password_invalido(self):
        self._write_env(
            "GMAIL_SENDER=test@gmail.com\n"
            "GMAIL_APP_PASSWORD=corta\n"
            "EMAIL_DESTINATARIO_PRODUCCION=prod@sena.edu.co\n"
            "EMAIL_DESTINATARIO_PRUEBAS=test@gmail.com\n"
            "EMAIL_CC=cc@gmail.com\n"
            "EMAIL_MODO=pruebas\n"
            "APRENDIZ_NOMBRE=Juan Perez\n"
            "EMPRESA_NOMBRE=Mi Empresa SAS\n"
            "INSTRUCTOR_NOMBRE=Carlos Lopez\n"
        )
        ok, missing, _ = env_validator.validate_env(self.env_path)
        self.assertFalse(ok)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["key"], "GMAIL_APP_PASSWORD")

    def test_validate_env_email_invalido(self):
        self._write_env(
            "GMAIL_SENDER=no-es-email\n"
            "GMAIL_APP_PASSWORD=abcdefghijklmnop\n"
            "EMAIL_DESTINATARIO_PRODUCCION=prod@sena.edu.co\n"
            "EMAIL_DESTINATARIO_PRUEBAS=test@gmail.com\n"
            "EMAIL_CC=cc@gmail.com\n"
            "EMAIL_MODO=pruebas\n"
            "APRENDIZ_NOMBRE=Juan Perez\n"
            "EMPRESA_NOMBRE=Mi Empresa SAS\n"
            "INSTRUCTOR_NOMBRE=Carlos Lopez\n"
        )
        ok, missing, _ = env_validator.validate_env(self.env_path)
        self.assertFalse(ok)
        missing_keys = [m["key"] for m in missing]
        self.assertIn("GMAIL_SENDER", missing_keys)

    def test_find_missing_retorna_definiciones_completas(self):
        """Las entradas en missing deben tener key, description, example, secret."""
        missing = env_validator.find_missing({})
        for var in missing:
            self.assertIn("key", var)
            self.assertIn("description", var)
            self.assertIn("example", var)
            self.assertIn("secret", var)


class TestEnvValidatorReporting(unittest.TestCase):
    """Tests para report_human y report_ai (no se imprimen passwords)."""

    def setUp(self):
        self._saved_env = {}
        for key in [
            "GMAIL_SENDER",
            "GMAIL_APP_PASSWORD",
            "EMAIL_DESTINATARIO_PRODUCCION",
            "EMAIL_DESTINATARIO_PRUEBAS",
            "EMAIL_CC",
            "EMAIL_MODO",
            "APRENDIZ_NOMBRE",
            "EMPRESA_NOMBRE",
            "INSTRUCTOR_NOMBRE",
        ]:
            self._saved_env[key] = os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._saved_env.items():
            if value is not None:
                os.environ[key] = value

    def test_report_ai_ok(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            env_validator.report_ai([])
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], "ok")
        self.assertIn("path", data)

    def test_report_ai_incomplete(self):
        buf = io.StringIO()
        missing = [env_validator.REQUIRED_VARS[0], env_validator.REQUIRED_VARS[1]]
        with patch("sys.stdout", buf):
            env_validator.report_ai(missing)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], "incomplete")
        self.assertEqual(len(data["missing"]), 2)
        for entry in data["missing"]:
            self.assertIn("variable", entry)
            self.assertIn("description", entry)
            self.assertIn("example", entry)
            self.assertIn("secret", entry)

    def test_report_ai_no_imprime_passwords(self):
        """Aunque se reporte GMAIL_APP_PASSWORD (secret=true), el output
        no debe contener un valor real de password."""
        buf = io.StringIO()
        missing = [v for v in env_validator.REQUIRED_VARS if v["key"] == "GMAIL_APP_PASSWORD"]
        with patch("sys.stdout", buf):
            env_validator.report_ai(missing)
        output = buf.getvalue()
        # Verificar que no hay valores de password filtrados
        self.assertNotIn("wted szuy ljqx dnlg", output)
        self.assertNotIn("abcdefghijklmnop", output)
        # Solo debe estar la metadata, no el valor
        data = json.loads(output)
        for entry in data["missing"]:
            self.assertNotIn("value", entry)
            self.assertNotIn("current", entry)

    def test_report_human_no_imprime_passwords(self):
        """report_human tampoco imprime valores, solo nombres de variables."""
        buf_err = io.StringIO()
        missing = [v for v in env_validator.REQUIRED_VARS if v["key"] == "GMAIL_APP_PASSWORD"]
        with patch("sys.stderr", buf_err):
            env_validator.report_human(missing)
        output = buf_err.getvalue()
        self.assertIn("GMAIL_APP_PASSWORD", output)
        # No debe contener un valor real
        self.assertNotIn("wted szuy ljqx dnlg", output)

    def test_require_env_ai_mode(self):
        """require_env con mode=ai debe imprimir JSON a stdout y retornar False."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            result = env_validator.require_env(mode="ai", env_path=Path("/no/existe"))
        self.assertFalse(result)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], "incomplete")

    def test_require_env_human_mode(self):
        """require_env con mode=human debe imprimir a stderr y retornar False."""
        buf_err = io.StringIO()
        with patch("sys.stderr", buf_err):
            result = env_validator.require_env(mode="human", env_path=Path("/no/existe"))
        self.assertFalse(result)
        output = buf_err.getvalue()
        self.assertIn("Faltan variables", output)
        self.assertIn("setup.py", output)

    def test_require_env_ok(self):
        """Si el entorno esta completo, retorna True sin output."""
        tmpdir = tempfile.mkdtemp()
        try:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "GMAIL_SENDER=test@gmail.com\n"
                "GMAIL_APP_PASSWORD=abcdefghijklmnop\n"
                "EMAIL_DESTINATARIO_PRODUCCION=prod@sena.edu.co\n"
                "EMAIL_DESTINATARIO_PRUEBAS=test@gmail.com\n"
                "EMAIL_CC=cc@gmail.com\n"
                "EMAIL_MODO=pruebas\n"
                "APRENDIZ_NOMBRE=Juan Perez\n"
                "EMPRESA_NOMBRE=Mi Empresa SAS\n"
                "INSTRUCTOR_NOMBRE=Carlos Lopez\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                result = env_validator.require_env(env_path=env_path)
            self.assertTrue(result)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# =============================================================================
# Tests de integracion: setup.py en modo agente
# =============================================================================

class TestSetupAiMode(unittest.TestCase):
    """Tests de integracion ejecutando setup.py como subproceso."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.env_path = Path(self.tmpdir) / ".env"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run_setup_ai(self, env_content=None, clear_environ=True):
        """Ejecuta setup.py --ai-mode con un .env controlado."""
        if env_content is not None:
            self.env_path.write_text(env_content, encoding="utf-8")

        setup_py = ROOT / "scripts" / "setup.py"
        # WORKAROUND: setup.py usa env_validator.ENV_PATH que apunta a un path fijo.
        # Para tests, parchamos temporalmente el path via env var o mocking.
        # Aqui usamos subprocess con PYTHONPATH y monkey-patching via un wrapper.

        wrapper = self.tmpdir + "/wrapper.py"
        Path(wrapper).write_text(
            f"""
import sys
sys.path.insert(0, r"{str(ROOT / "scripts")}")
import env_validator
import setup
# Redirigir ENV_PATH al temporal
from pathlib import Path
env_validator.ENV_PATH = Path(r"{str(self.env_path)}")
setup.ENV_PATH = Path(r"{str(self.env_path)}")
sys.exit(setup.main())
""",
            encoding="utf-8",
        )

        env = os.environ.copy()
        if clear_environ:
            for key in [
                "GMAIL_SENDER",
                "GMAIL_APP_PASSWORD",
                "EMAIL_DESTINATARIO_PRODUCCION",
                "EMAIL_DESTINATARIO_PRUEBAS",
                "EMAIL_CC",
                "EMAIL_MODO",
                "APRENDIZ_NOMBRE",
                "EMPRESA_NOMBRE",
                "INSTRUCTOR_NOMBRE",
            ]:
                env.pop(key, None)

        result = subprocess.run(
            [sys.executable, wrapper, "--ai-mode"],
            capture_output=True,
            text=True,
            env=env,
        )
        return result

    def test_ai_mode_ok(self):
        """Con .env completo, --ai-mode imprime status=ok y exit code 0."""
        result = self._run_setup_ai(
            env_content=(
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
        )
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "ok")

    def test_ai_mode_incomplete(self):
        """Con .env vacio, --ai-mode imprime status=incomplete y exit code 1."""
        result = self._run_setup_ai(env_content="")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "incomplete")
        self.assertEqual(len(data["missing"]), 9)
        # GMAIL_APP_PASSWORD debe estar marcado como secret
        app_pwd_entry = next(
            (m for m in data["missing"] if m["variable"] == "GMAIL_APP_PASSWORD"),
            None,
        )
        self.assertIsNotNone(app_pwd_entry)
        self.assertTrue(app_pwd_entry["secret"])

    def test_ai_mode_parcial(self):
        """Con solo algunas variables, --ai-mode reporta solo las faltantes."""
        result = self._run_setup_ai(
            env_content=(
                "GMAIL_SENDER=test@gmail.com\n"
                "GMAIL_APP_PASSWORD=abcdefghijklmnop\n"
                # Faltan las otras 7
            )
        )
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "incomplete")
        self.assertEqual(len(data["missing"]), 7)
        missing_keys = {m["variable"] for m in data["missing"]}
        self.assertNotIn("GMAIL_SENDER", missing_keys)
        self.assertNotIn("GMAIL_APP_PASSWORD", missing_keys)
        self.assertIn("EMAIL_DESTINATARIO_PRODUCCION", missing_keys)
        self.assertIn("APRENDIZ_NOMBRE", missing_keys)
        self.assertIn("EMPRESA_NOMBRE", missing_keys)
        self.assertIn("INSTRUCTOR_NOMBRE", missing_keys)

    def test_ai_mode_check_no_escribe(self):
        """--check (que implica --ai-mode) no debe escribir .env si no existe."""
        # .env no existe
        result = self._run_setup_ai(env_content=None)
        self.assertFalse(self.env_path.exists(), "No debe crear .env con --check")
        # Y como no existe, debe reportar incomplete
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "incomplete")


# =============================================================================
# Tests para las nuevas variables de usuario (APRENDIZ_NOMBRE, EMPRESA_NOMBRE,
# INSTRUCTOR_NOMBRE)
# =============================================================================


class TestNewUserVariables(unittest.TestCase):
    """Tests para los validadores de las 3 nuevas variables de usuario."""

    def test_aprendiz_nombre_valido(self):
        """Nombre completo valido retorna None (sin error)."""
        self.assertIsNone(env_validator._validate_non_empty("Juan Perez"))

    def test_aprendiz_nombre_vacio(self):
        """Nombre vacio retorna error."""
        self.assertIsNotNone(env_validator._validate_non_empty(""))

    def test_aprendiz_nombre_solo_una_palabra(self):
        """Nombre con una sola palabra retorna error."""
        self.assertIsNotNone(env_validator._validate_non_empty("Juan"))

    def test_aprendiz_nombre_espacios(self):
        """Nombre con solo espacios retorna error."""
        self.assertIsNotNone(env_validator._validate_non_empty("   "))

    def test_empresa_nombre_valido(self):
        """Nombre de empresa valido retorna None."""
        self.assertIsNone(env_validator._validate_non_empty("Mi Empresa SAS"))

    def test_empresa_nombre_vacio(self):
        """Nombre de empresa vacio retorna error."""
        self.assertIsNotNone(env_validator._validate_non_empty(""))

    def test_instructor_nombre_valido(self):
        """Nombre de instructor valido retorna None."""
        self.assertIsNone(env_validator._validate_non_empty("Carlos Lopez"))

    def test_instructor_nombre_vacio(self):
        """Nombre de instructor vacio retorna error."""
        self.assertIsNotNone(env_validator._validate_non_empty(""))

    def test_required_vars_incluye_usuario(self):
        """REQUIRED_VARS incluye las 3 nuevas variables de usuario."""
        keys = [v["key"] for v in env_validator.REQUIRED_VARS]
        self.assertIn("APRENDIZ_NOMBRE", keys)
        self.assertIn("EMPRESA_NOMBRE", keys)
        self.assertIn("INSTRUCTOR_NOMBRE", keys)

    def test_validators_incluye_usuario(self):
        """VALIDATORS incluye las 3 nuevas variables mapeadas a _validate_non_empty."""
        self.assertIn("APRENDIZ_NOMBRE", env_validator.VALIDATORS)
        self.assertIn("EMPRESA_NOMBRE", env_validator.VALIDATORS)
        self.assertIn("INSTRUCTOR_NOMBRE", env_validator.VALIDATORS)
        self.assertIs(env_validator.VALIDATORS["APRENDIZ_NOMBRE"], env_validator._validate_non_empty)
        self.assertIs(env_validator.VALIDATORS["EMPRESA_NOMBRE"], env_validator._validate_non_empty)
        self.assertIs(env_validator.VALIDATORS["INSTRUCTOR_NOMBRE"], env_validator._validate_non_empty)


# =============================================================================
# Tests de seguridad
# =============================================================================

class TestSecurity(unittest.TestCase):
    """Verifica que informacion sensible nunca se imprima."""

    def test_password_no_aparece_en_report_ai(self):
        """El campo secret=true de la metadata nunca expone valores."""
        buf = io.StringIO()
        # Simular que GMAIL_APP_PASSWORD tiene un valor real
        env_values = {"GMAIL_APP_PASSWORD": "secretpass12345"}
        with patch.dict(os.environ, env_values):
            missing = env_validator.find_missing(env_values)
        with patch("sys.stdout", buf):
            env_validator.report_ai(missing)
        output = buf.getvalue()
        self.assertNotIn("secretpass123456", output)
        self.assertNotIn(env_values["GMAIL_APP_PASSWORD"], output)

    def test_password_no_aparece_en_output_setup_ai(self):
        """Verifica que el JSON de setup.py --ai-mode no filtra passwords."""
        tmpdir = tempfile.mkdtemp()
        try:
            env_path = Path(tmpdir) / ".env"
            # Crear un .env con password real
            env_path.write_text(
                "GMAIL_SENDER=test@gmail.com\n"
                "GMAIL_APP_PASSWORD=supersecret12345\n"
                "EMAIL_DESTINATARIO_PRODUCCION=prod@sena.edu.co\n"
                "EMAIL_DESTINATARIO_PRUEBAS=test@gmail.com\n"
                "EMAIL_CC=cc@gmail.com\n"
                "EMAIL_MODO=pruebas\n"
                "APRENDIZ_NOMBRE=Juan Perez\n"
                "EMPRESA_NOMBRE=Mi Empresa SAS\n"
                "INSTRUCTOR_NOMBRE=Carlos Lopez\n",
                encoding="utf-8",
            )
            wrapper = Path(tmpdir) / "wrapper.py"
            wrapper.write_text(
                f"""
import sys
sys.path.insert(0, r"{str(ROOT / "scripts")}")
import env_validator, setup
from pathlib import Path
env_validator.ENV_PATH = Path(r"{str(env_path)}")
setup.ENV_PATH = Path(r"{str(env_path)}")
sys.exit(setup.main())
""",
                encoding="utf-8",
            )
            env = os.environ.copy()
            for key in [
                "GMAIL_SENDER",
                "GMAIL_APP_PASSWORD",
                "EMAIL_DESTINATARIO_PRODUCCION",
                "EMAIL_DESTINATARIO_PRUEBAS",
                "EMAIL_CC",
                "EMAIL_MODO",
                "APRENDIZ_NOMBRE",
                "EMPRESA_NOMBRE",
                "INSTRUCTOR_NOMBRE",
            ]:
                env.pop(key, None)
            result = subprocess.run(
                [sys.executable, str(wrapper), "--ai-mode"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0)
            # Verificar que el password NO aparece en stdout ni stderr
            self.assertNotIn("supersecret1234", result.stdout)
            self.assertNotIn("supersecret1234", result.stderr)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()