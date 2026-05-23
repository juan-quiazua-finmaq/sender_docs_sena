"""
Pruebas unitarias para email_module.py

Cubre: construir_asunto (nueva firma con lista), construir_cuerpo (nueva firma),
       enviar_email (mock SMTP), reintentos automáticos, reintentar_envio_manual,
       y carga de .env.

Autor: Tester Agent
Fecha: 2026-05-23
Sesión: session_004
"""

import unittest
from unittest.mock import patch, MagicMock, call
import smtplib
import os
import sys

# Asegurar que scripts/ está en sys.path para importar email_module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import email_module


class TestConstruirAsunto(unittest.TestCase):
    """Tests para la función construir_asunto() con nueva firma por lote."""

    def test_construir_asunto_una_bitacora(self):
        """Verifica el formato del asunto con una sola bitácora."""
        bitacoras_info = [
            {'numero': 3, 'fecha_inicio': '01/05/2026', 'fecha_fin': '15/05/2026'},
        ]
        resultado = email_module.construir_asunto(bitacoras_info, acta_moment=None)
        esperado = "Bitácoras 3 — Período 01/05/2026 al 15/05/2026"
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_dos_bitacoras(self):
        """Verifica el formato del asunto con dos bitácoras."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '01/04/2026', 'fecha_fin': '15/04/2026'},
            {'numero': 2, 'fecha_inicio': '16/04/2026', 'fecha_fin': '30/04/2026'},
        ]
        resultado = email_module.construir_asunto(bitacoras_info, acta_moment=None)
        esperado = "Bitácoras 1 y 2 — Período 01/04/2026 al 30/04/2026"
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_tres_bitacoras(self):
        """Verifica el formato del asunto con tres bitácoras."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '01/04/2026', 'fecha_fin': '15/04/2026'},
            {'numero': 2, 'fecha_inicio': '16/04/2026', 'fecha_fin': '30/04/2026'},
            {'numero': 3, 'fecha_inicio': '01/05/2026', 'fecha_fin': '15/05/2026'},
        ]
        resultado = email_module.construir_asunto(bitacoras_info, acta_moment=None)
        esperado = "Bitácoras 1, 2 y 3 — Período 01/04/2026 al 15/05/2026"
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_bitacoras_y_acta(self):
        """Verifica el asunto con bitácoras y acta."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '01/04/2026', 'fecha_fin': '15/04/2026'},
            {'numero': 2, 'fecha_inicio': '16/04/2026', 'fecha_fin': '30/04/2026'},
        ]
        resultado = email_module.construir_asunto(bitacoras_info, acta_moment=2)
        esperado = (
            "Bitácoras 1 y 2 y Acta Momento 2"
            " — Período 01/04/2026 al 30/04/2026"
        )
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_solo_acta(self):
        """Verifica el formato del asunto cuando solo hay acta."""
        resultado = email_module.construir_asunto([], acta_moment=3)
        esperado = "Acta Momento 3"
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_vacio(self):
        """Verifica el asunto cuando no hay bitácoras ni acta."""
        resultado = email_module.construir_asunto([], acta_moment=None)
        esperado = "Documentos SENA - Automatización"
        self.assertEqual(resultado, esperado)


class TestConstruirCuerpo(unittest.TestCase):
    """Tests para la función construir_cuerpo() con nueva firma por lote."""

    def test_construir_cuerpo_una_bitacora(self):
        """Verifica el cuerpo del mensaje con una bitácora."""
        bitacoras_info = [
            {'numero': 3, 'fecha_inicio': '01/05/2026', 'fecha_fin': '15/05/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        # Debe contener el nuevo saludo personalizado
        self.assertIn("Estimado instructor Oscar Ivan Ospina Ospina", resultado)
        self.assertIn("01/05/2026", resultado)
        self.assertIn("15/05/2026", resultado)
        self.assertIn("Cordialmente", resultado)
        self.assertIn("Manuel Quiazua y Finmaq", resultado)
        # Debe listar la bitácora en formato Opción B
        self.assertIn("- Bitácora 3", resultado)
        # NO debe contener referencia al acta
        self.assertNotIn("acta correspondiente", resultado.lower())

    def test_construir_cuerpo_varias_bitacoras(self):
        """Verifica el cuerpo del mensaje con varias bitácoras."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '08/04/2026', 'fecha_fin': '22/04/2026'},
            {'numero': 2, 'fecha_inicio': '22/04/2026', 'fecha_fin': '06/05/2026'},
            {'numero': 3, 'fecha_inicio': '06/05/2026', 'fecha_fin': '20/05/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        # Debe listar cada bitácora
        self.assertIn("- Bitácora 1 (08/04/2026 al 22/04/2026)", resultado)
        self.assertIn("- Bitácora 2 (22/04/2026 al 06/05/2026)", resultado)
        self.assertIn("- Bitácora 3 (06/05/2026 al 20/05/2026)", resultado)
        self.assertIn("Reciba un cordial saludo", resultado)

    def test_construir_cuerpo_con_acta(self):
        """Verifica el cuerpo del mensaje cuando hay acta incluida."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '08/04/2026', 'fecha_fin': '22/04/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=2)
        self.assertIn("Estimado instructor Oscar Ivan Ospina Ospina", resultado)
        self.assertIn("08/04/2026", resultado)
        self.assertIn("22/04/2026", resultado)
        # DEBE contener referencia al acta
        self.assertIn("acta correspondiente al Momento 2", resultado)
        self.assertIn("Cordialmente", resultado)


class TestEnviarEmailMockSMTP(unittest.TestCase):
    """Tests para enviar_email() con mock de SMTP."""

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch"})
    @patch("email_module.smtplib.SMTP")
    def test_enviar_email_mock_smtp(self, mock_smtp_class):
        """Mock del envío SMTP: verifica la estructura del email enviado."""
        # Configurar el mock
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        exito, mensaje = email_module.enviar_email(
            destinatario="dest@test.com",
            cc="cc@test.com",
            asunto="Asunto de prueba",
            cuerpo="Cuerpo de prueba",
            adjuntos=[],
            intentos=1,
        )

        # Verificar que se retornó éxito
        self.assertTrue(exito)
        self.assertIn("exitosamente", mensaje)

        # Verificar que se creó la conexión SMTP correctamente
        mock_smtp_class.assert_called_once_with(
            "smtp.gmail.com", 587, timeout=30
        )
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            "jmqo2026@gmail.com", "test-password-16ch"
        )

        # Verificar que sendmail fue llamado con remitente, destinatarios y mensaje
        mock_server.sendmail.assert_called_once()
        sendmail_args = mock_server.sendmail.call_args[0]
        self.assertEqual(sendmail_args[0], "jmqo2026@gmail.com")  # From
        # To + Cc
        self.assertIn("dest@test.com", sendmail_args[1])
        self.assertIn("cc@test.com", sendmail_args[1])

        mock_server.quit.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_enviar_email_sin_password_retorna_error(self):
        """Si no hay GMAIL_APP_PASSWORD, retorna error sin intentar SMTP."""
        # Asegurar que no existe la variable
        os.environ.pop("GMAIL_APP_PASSWORD", None)

        exito, mensaje = email_module.enviar_email(
            destinatario="dest@test.com",
            cc="",
            asunto="Test",
            cuerpo="Test",
            adjuntos=[],
        )

        self.assertFalse(exito)
        self.assertIn("GMAIL_APP_PASSWORD", mensaje)


class TestEnviarEmailReintentos(unittest.TestCase):
    """Tests para verificar reintentos automáticos ante fallos SMTP."""

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch"})
    @patch("email_module.time.sleep")
    @patch("email_module.smtplib.SMTP")
    def test_enviar_email_reintentos_automaticos(
        self, mock_smtp_class, mock_sleep
    ):
        """Verifica que se reintentan 3 veces ante fallo de conexión."""
        # Configurar el mock para que SIEMPRE falle con OSError
        mock_smtp_class.side_effect = OSError("Connection refused")

        exito, mensaje = email_module.enviar_email(
            destinatario="dest@test.com",
            cc="",
            asunto="Test",
            cuerpo="Test",
            adjuntos=[],
            intentos=3,
        )

        # Debe fallar
        self.assertFalse(exito)
        self.assertIn("Error SMTP", mensaje)
        self.assertIn("3 intentos", mensaje)

        # Se debe haber intentado 3 veces
        self.assertEqual(mock_smtp_class.call_count, 3)

        # Se debe haber esperado 2 veces (entre intento 1->2 y 2->3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_called_with(5)

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch"})
    @patch("email_module.time.sleep")
    @patch("email_module.smtplib.SMTP")
    def test_enviar_email_reintento_exitoso_en_segundo_intento(
        self, mock_smtp_class, mock_sleep
    ):
        """Verifica que si falla el 1er intento pero el 2do funciona, retorna éxito."""
        mock_server = MagicMock()

        # 1er intento: falla, 2do intento: éxito
        mock_smtp_class.side_effect = [
            OSError("Connection refused"),
            mock_server,
        ]

        exito, mensaje = email_module.enviar_email(
            destinatario="dest@test.com",
            cc="",
            asunto="Test",
            cuerpo="Test",
            adjuntos=[],
            intentos=3,
        )

        self.assertTrue(exito)
        self.assertEqual(mock_smtp_class.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch"})
    @patch("email_module.time.sleep")
    @patch("email_module.smtplib.SMTP")
    def test_enviar_email_falla_autenticacion_3_veces(
        self, mock_smtp_class, mock_sleep
    ):
        """Verifica comportamiento ante fallo de autenticación persistente."""
        mock_smtp_class.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Authentication failed"
        )

        exito, mensaje = email_module.enviar_email(
            destinatario="dest@test.com",
            cc="",
            asunto="Test",
            cuerpo="Test",
            adjuntos=[],
            intentos=3,
        )

        self.assertFalse(exito)
        self.assertIn("autenticación", mensaje.lower())
        self.assertEqual(mock_smtp_class.call_count, 3)


class TestCargarVariablesEntorno(unittest.TestCase):
    """Tests para verificar que .env se carga correctamente."""

    def test_cargar_variables_entorno(self):
        """Verifica que las variables de entorno se cargan desde .env."""
        gmail_sender = os.getenv("GMAIL_SENDER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        email_cc = os.getenv("EMAIL_CC")
        email_modo = os.getenv("EMAIL_MODO")

        # Buscar .env en la raíz del proyecto
        env_path = os.path.join(os.path.dirname(__file__), '..', ".env")
        if os.path.exists(env_path):
            self.assertIsNotNone(gmail_sender, "GMAIL_SENDER no cargada")
            self.assertIsNotNone(gmail_password, "GMAIL_APP_PASSWORD no cargada")
            self.assertIsNotNone(email_cc, "EMAIL_CC no cargada")
            self.assertIsNotNone(email_modo, "EMAIL_MODO no cargada")

            # Valores esperados del .env
            self.assertEqual(gmail_sender, "jmqo2026@gmail.com")
            self.assertEqual(email_cc, "eivorkinkest@gmail.com")
            self.assertIn(email_modo, ["pruebas", "produccion"])
        else:
            self.skipTest("Archivo .env no encontrado; se omite verificación")

    def test_smtp_constants(self):
        """Verifica que las constantes SMTP del módulo son correctas."""
        self.assertEqual(email_module.SMTP_SERVER, "smtp.gmail.com")
        self.assertEqual(email_module.SMTP_PORT, 587)


if __name__ == "__main__":
    unittest.main()
