"""
Pruebas unitarias para email_module.py

Cubre: construir_asunto, construir_cuerpo, enviar_email (mock SMTP),
       reintentos automáticos, preguntar_envio_email y carga de .env.

Autor: Tester Agent
Fecha: 2026-05-23
Sesión: session_003
"""

import unittest
from unittest.mock import patch, MagicMock, call
import smtplib
import os
import sys

# Asegurar que el directorio del proyecto está en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import email_module


class TestConstruirAsunto(unittest.TestCase):
    """Tests para la función construir_asunto()."""

    def test_construir_asunto_solo_bitacora(self):
        """Verifica el formato del asunto cuando solo hay bitácora."""
        resultado = email_module.construir_asunto(
            bitacora_num=3,
            fecha_inicio="2026-05-01",
            fecha_fin="2026-05-15",
            acta_moment=None,
        )
        esperado = "Bitácora 3 - Período 2026-05-01 al 2026-05-15"
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_bitacora_y_acta(self):
        """Verifica el formato del asunto con bitácora y acta."""
        resultado = email_module.construir_asunto(
            bitacora_num=5,
            fecha_inicio="2026-05-01",
            fecha_fin="2026-05-15",
            acta_moment=2,
        )
        esperado = (
            "Bitácora 5 y Acta Momento 2"
            " - Período 2026-05-01 al 2026-05-15"
        )
        self.assertEqual(resultado, esperado)

    def test_construir_asunto_solo_acta(self):
        """Verifica el formato del asunto cuando solo hay acta."""
        resultado = email_module.construir_asunto(
            bitacora_num=None,
            fecha_inicio="2026-05-01",
            fecha_fin="2026-05-15",
            acta_moment=3,
        )
        esperado = "Acta Momento 3"
        self.assertEqual(resultado, esperado)


class TestConstruirCuerpo(unittest.TestCase):
    """Tests para la función construir_cuerpo()."""

    def test_construir_cuerpo_solo_bitacora(self):
        """Verifica el cuerpo del mensaje cuando no hay acta."""
        resultado = email_module.construir_cuerpo(
            fecha_inicio="2026-05-01",
            fecha_fin="2026-05-15",
            acta_moment=None,
        )
        # Debe contener la referencia a la bitácora
        self.assertIn("Estimado instructor", resultado)
        self.assertIn("2026-05-01", resultado)
        self.assertIn("2026-05-15", resultado)
        self.assertIn("Cordialmente", resultado)
        self.assertIn("Manuel Quiazua y Finmaq", resultado)
        # NO debe contener referencia al acta
        self.assertNotIn("acta correspondiente", resultado.lower())

    def test_construir_cuerpo_con_acta(self):
        """Verifica el cuerpo del mensaje cuando hay acta incluida."""
        resultado = email_module.construir_cuerpo(
            fecha_inicio="2026-05-01",
            fecha_fin="2026-05-15",
            acta_moment=2,
        )
        self.assertIn("Estimado instructor", resultado)
        self.assertIn("2026-05-01", resultado)
        self.assertIn("2026-05-15", resultado)
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


class TestPreguntarEnvioEmail(unittest.TestCase):
    """Tests para preguntar_envio_email() con mock de input()."""

    @patch("builtins.input", return_value="s")
    def test_preguntar_envio_email_si(self, mock_input):
        """Verifica que 's' retorna True."""
        resultado = email_module.preguntar_envio_email()
        self.assertTrue(resultado)
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="n")
    def test_preguntar_envio_email_no(self, mock_input):
        """Verifica que 'n' retorna False."""
        resultado = email_module.preguntar_envio_email()
        self.assertFalse(resultado)
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="sí")
    def test_preguntar_envio_email_sí_con_acento(self, mock_input):
        """Verifica que 'sí' (con acento) también retorna True."""
        resultado = email_module.preguntar_envio_email()
        self.assertTrue(resultado)

    @patch("builtins.input", return_value="SI")
    def test_preguntar_envio_email_mayusculas(self, mock_input):
        """Verifica que 'SI' en mayúsculas retorna True."""
        resultado = email_module.preguntar_envio_email()
        self.assertTrue(resultado)


class TestCargarVariablesEntorno(unittest.TestCase):
    """Tests para verificar que .env se carga correctamente."""

    def test_cargar_variables_entorno(self):
        """Verifica que las variables de entorno se cargan desde .env."""
        # El módulo ya hizo load_dotenv() al importarse.
        # Verificar que las variables están definidas (pueden venir de
        # .env o del entorno del sistema).
        # Usamos os.getenv para no fallar si .env no existe en CI.
        gmail_sender = os.getenv("GMAIL_SENDER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        email_cc = os.getenv("EMAIL_CC")
        email_modo = os.getenv("EMAIL_MODO")

        # Si .env existe y fue cargado, estas variables deben tener valor
        env_path = os.path.join(os.path.dirname(__file__), ".env")
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
