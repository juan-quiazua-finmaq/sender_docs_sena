"""
test_reset.py - Tests para scripts/reset.py.

Cubre:
    - download_from_github: descarga con mock de urllib.
    - copy_from_backup: copia desde backup local.
    - reset_context: regeneracion de archivos de contexto.
    - reset_env: regeneracion de .env desde .env.example.
    - CLI: --help y ejecucion basica.

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
from unittest.mock import patch, MagicMock

# Asegurar que scripts/ esta en sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import reset  # noqa: E402


# =============================================================================
# TestResetTemplateDownload — tests de descarga y backup de plantillas
# =============================================================================


class TestResetTemplateDownload(unittest.TestCase):
    """Tests para download_from_github y copy_from_backup."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.dest = Path(self.tmpdir) / "output" / "test_file.xlsx"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("reset.urllib.request.urlopen")
    def test_download_from_github_success(self, mock_urlopen):
        """Con respuesta 200, el archivo se crea en destino."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"fake-binary-content"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = reset.download_from_github("test_file.xlsx", self.dest)

        self.assertTrue(result)
        self.assertTrue(self.dest.exists())
        self.assertEqual(self.dest.read_bytes(), b"fake-binary-content")

    @patch("reset.urllib.request.urlopen")
    def test_download_from_github_404(self, mock_urlopen):
        """Con error HTTP, retorna False y NO crea archivo."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com", code=404, msg="Not Found",
            hdrs=None, fp=None,
        )

        result = reset.download_from_github("test_file.xlsx", self.dest)

        self.assertFalse(result)
        self.assertFalse(self.dest.exists())

    def test_copy_from_backup_success(self):
        """Con archivo backup existente, la copia funciona."""
        # Configurar backup dir
        backup_dir = Path(self.tmpdir) / "plantillas_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / "test_file.xlsx"
        backup_file.write_bytes(b"backup-content")

        # Redirigir PLANTILLAS_BACKUP_DIR
        original = reset.PLANTILLAS_BACKUP_DIR
        try:
            reset.PLANTILLAS_BACKUP_DIR = backup_dir
            result = reset.copy_from_backup("test_file.xlsx", self.dest)
            self.assertTrue(result)
            self.assertTrue(self.dest.exists())
            self.assertEqual(self.dest.read_bytes(), b"backup-content")
        finally:
            reset.PLANTILLAS_BACKUP_DIR = original

    def test_copy_from_backup_missing(self):
        """Sin archivo backup, retorna False."""
        backup_dir = Path(self.tmpdir) / "plantillas_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        original = reset.PLANTILLAS_BACKUP_DIR
        try:
            reset.PLANTILLAS_BACKUP_DIR = backup_dir
            result = reset.copy_from_backup("test_file.xlsx", self.dest)
            self.assertFalse(result)
            self.assertFalse(self.dest.exists())
        finally:
            reset.PLANTILLAS_BACKUP_DIR = original


# =============================================================================
# TestResetContext — tests de regeneracion de archivos de contexto
# =============================================================================


class TestResetContext(unittest.TestCase):
    """Tests para reset_context()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Guardar originales
        self._orig_con = reset.CONTEXTO_DIR
        self._orig_hist = reset.HISTORICO_PATH
        self._orig_mem = reset.MEMORY_PATH
        self._orig_men = reset.MENSAJE_PATH

        # Redirigir a temporal
        tmp_con = Path(self.tmpdir) / "contexto"
        tmp_con.mkdir(parents=True, exist_ok=True)
        reset.CONTEXTO_DIR = tmp_con
        reset.HISTORICO_PATH = tmp_con / "historico_actividades.md"
        reset.MEMORY_PATH = tmp_con / "memory_descriptions.md"
        reset.MENSAJE_PATH = tmp_con / "mensaje_instructor.md"

    def tearDown(self):
        reset.CONTEXTO_DIR = self._orig_con
        reset.HISTORICO_PATH = self._orig_hist
        reset.MEMORY_PATH = self._orig_mem
        reset.MENSAJE_PATH = self._orig_men
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_reset_context_creates_files(self):
        """reset_context() crea los 3 archivos con contenido esperado."""
        result = reset.reset_context()
        self.assertTrue(result)

        # Verificar que los 3 archivos existen
        self.assertTrue(reset.HISTORICO_PATH.exists())
        self.assertTrue(reset.MEMORY_PATH.exists())
        self.assertTrue(reset.MENSAJE_PATH.exists())

        # Verificar contenido clave de cada archivo
        hist_content = reset.HISTORICO_PATH.read_text(encoding="utf-8")
        self.assertIn("Historico de Actividades", hist_content)
        self.assertIn("Bitacora numero 1", hist_content)

        mem_content = reset.MEMORY_PATH.read_text(encoding="utf-8")
        self.assertIn("bitacoras", mem_content)
        # Verificar que contiene JSON valido
        if "`json" in mem_content:
            json_start = mem_content.index("`json") + len("`json")
            json_end = mem_content.index("`", json_start)
            json.loads(mem_content[json_start:json_end].strip())

        men_content = reset.MENSAJE_PATH.read_text(encoding="utf-8")
        self.assertIn("{{destinatario}}", men_content)
        self.assertIn("{{lista_bitacoras}}", men_content)
        self.assertIn("{{acta_moment}}", men_content)
        self.assertIn("{{firma}}", men_content)
        self.assertIn("{{fecha_ejecucion}}", men_content)


# =============================================================================
# TestResetEnv — tests de regeneracion de .env
# =============================================================================


class TestResetEnv(unittest.TestCase):
    """Tests para reset_env()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Guardar originales
        self._orig_env = reset.ENV_PATH
        self._orig_env_ex = reset.ENV_EXAMPLE_PATH

        # Redirigir a temporal
        reset.ENV_PATH = Path(self.tmpdir) / ".env"
        reset.ENV_EXAMPLE_PATH = Path(self.tmpdir) / ".env.example"

    def tearDown(self):
        reset.ENV_PATH = self._orig_env
        reset.ENV_EXAMPLE_PATH = self._orig_env_ex
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_reset_env_creates_from_example(self):
        """Con .env.example existente, crea .env con el mismo contenido."""
        example_content = "GMAIL_SENDER=\nGMAIL_APP_PASSWORD=\n"
        reset.ENV_EXAMPLE_PATH.write_text(example_content, encoding="utf-8")

        result = reset.reset_env()

        self.assertTrue(result)
        self.assertTrue(reset.ENV_PATH.exists())
        self.assertEqual(reset.ENV_PATH.read_text(encoding="utf-8"), example_content)

    def test_reset_env_backs_up_existing(self):
        """Con .env existente, crea backup antes de sobrescribir."""
        # Crear .env.example
        example_content = "GMAIL_SENDER=new@gmail.com\n"
        reset.ENV_EXAMPLE_PATH.write_text(example_content, encoding="utf-8")

        # Crear .env existente con contenido previo
        old_content = "GMAIL_SENDER=old@gmail.com\n"
        reset.ENV_PATH.write_text(old_content, encoding="utf-8")

        result = reset.reset_env()

        self.assertTrue(result)
        # Verificar que .env fue sobrescrito
        self.assertEqual(reset.ENV_PATH.read_text(encoding="utf-8"), example_content)
        # Verificar que se creo un archivo de backup
        backup_files = list(Path(self.tmpdir).glob(".env.backup-*"))
        self.assertGreater(len(backup_files), 0)
        self.assertEqual(backup_files[0].read_text(encoding="utf-8"), old_content)

    def test_reset_env_sin_example_falla(self):
        """Sin .env.example, retorna False."""
        # No creamos .env.example
        result = reset.reset_env()
        self.assertFalse(result)
        self.assertFalse(reset.ENV_PATH.exists())


# =============================================================================
# TestResetMain — tests de CLI
# =============================================================================


class TestResetMain(unittest.TestCase):
    """Tests para la interfaz CLI de reset.py."""

    def test_reset_help(self):
        """--help muestra todas las opciones disponibles."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "reset.py"), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--templates", result.stdout)
        self.assertIn("--context", result.stdout)
        self.assertIn("--env", result.stdout)
        self.assertIn("--all", result.stdout)
        self.assertIn("--include-env", result.stdout)
        self.assertIn("--ai-mode", result.stdout)


if __name__ == "__main__":
    unittest.main()
