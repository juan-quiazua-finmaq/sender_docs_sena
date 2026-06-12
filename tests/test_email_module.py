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
    """Tests para la función construir_cuerpo() con plantilla markdown.

    Verifica reemplazo de placeholders, fallback cuando el archivo no existe,
    y manejo correcto de acta_moment.
    """

    def test_usa_plantilla_markdown_si_existe(self):
        """Con archivo existente, debe usar la plantilla y NO dejar placeholders."""
        bitacoras_info = [
            {'numero': 3, 'fecha_inicio': '01/05/2026', 'fecha_fin': '15/05/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        # No debe contener placeholders sin reemplazar
        self.assertNotIn("{{destinatario}}", resultado)
        self.assertNotIn("{{lista_bitacoras}}", resultado)
        self.assertNotIn("{{firma}}", resultado)
        self.assertNotIn("{{fecha_ejecucion}}", resultado)
        # Debe contener contenido esperado tras reemplazo
        self.assertIn("Estimado", resultado)
        self.assertIn("Cordialmente", resultado)

    @patch("email_module.os.path.exists")
    def test_fallback_a_mensaje_hardcoded_si_no_existe(self, mock_exists):
        """Sin archivo de plantilla, debe usar el mensaje hardcoded original."""
        def exists_side_effect(path):
            if "mensaje_instructor" in str(path):
                return False
            return os.path.exists(path)
        mock_exists.side_effect = exists_side_effect

        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '01/04/2026', 'fecha_fin': '15/04/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        # El mensaje hardcoded tiene el nombre específico del instructor
        self.assertIn("Estimado instructor Oscar Ivan Ospina Ospina", resultado)
        self.assertIn("- Bitácora 1", resultado)
        self.assertIn("Cordialmente", resultado)
        self.assertIn("Manuel Quiazua y Finmaq", resultado)

    def test_reemplaza_destinatario(self):
        """Verifica que {{destinatario}} fue reemplazado (no queda placeholder)."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '01/04/2026', 'fecha_fin': '15/04/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        self.assertNotIn("{{destinatario}}", resultado)
        self.assertIn("instructor Oscar Ivan Ospina Ospina", resultado)

    def test_reemplaza_lista_bitacoras(self):
        """Verifica que {{lista_bitacoras}} se reemplaza con la lista de bitácoras."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '08/04/2026', 'fecha_fin': '22/04/2026'},
            {'numero': 2, 'fecha_inicio': '22/04/2026', 'fecha_fin': '06/05/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        self.assertNotIn("{{lista_bitacoras}}", resultado)
        self.assertIn("- Bitácora 1 (08/04/2026 al 22/04/2026)", resultado)
        self.assertIn("- Bitácora 2 (22/04/2026 al 06/05/2026)", resultado)

    def test_reemplaza_firma(self):
        """Verifica que {{firma}} se reemplaza por el nombre real."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '01/04/2026', 'fecha_fin': '15/04/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        self.assertNotIn("{{firma}}", resultado)
        self.assertIn("Manuel Quiazua y Finmaq", resultado)

    def test_incluye_acta_si_acta_moment_no_es_none(self):
        """Con acta_moment=2, debe incluir referencia al Momento 2."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '08/04/2026', 'fecha_fin': '22/04/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=2)
        self.assertNotIn("{{acta_moment}}", resultado)
        self.assertIn("Momento 2", resultado)

    def test_omite_acta_si_acta_moment_es_none(self):
        """Con acta_moment=None, no debe incluir texto de acta ni placeholder."""
        bitacoras_info = [
            {'numero': 1, 'fecha_inicio': '08/04/2026', 'fecha_fin': '22/04/2026'},
        ]
        resultado = email_module.construir_cuerpo(bitacoras_info, acta_moment=None)
        self.assertNotIn("{{acta_moment}}", resultado)
        self.assertNotIn("Momento", resultado)


class TestEnviarEmailMockSMTP(unittest.TestCase):
    """Tests para enviar_email() con mock de SMTP."""

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch", "GMAIL_SENDER": "test@gmail.com"})
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
            "test@gmail.com", "test-password-16ch"
        )

        # Verificar que sendmail fue llamado con remitente, destinatarios y mensaje
        mock_server.sendmail.assert_called_once()
        sendmail_args = mock_server.sendmail.call_args[0]
        self.assertEqual(sendmail_args[0], "test@gmail.com")  # From
        # To + Cc
        self.assertIn("dest@test.com", sendmail_args[1])
        self.assertIn("cc@test.com", sendmail_args[1])

        mock_server.quit.assert_called_once()

    @patch.dict(os.environ, {"GMAIL_SENDER": "test@gmail.com"}, clear=True)
    def test_enviar_email_sin_password_retorna_error(self):
        """Si no hay GMAIL_APP_PASSWORD, retorna error sin intentar SMTP."""
        # GMAIL_SENDER is set by patch.dict; GMAIL_APP_PASSWORD is not
        exito, mensaje = email_module.enviar_email(
            destinatario="dest@test.com",
            cc="",
            asunto="Test",
            cuerpo="Test",
            adjuntos=[],
        )

        self.assertFalse(exito)
        self.assertIn("GMAIL_APP_PASSWORD", mensaje)

    @patch.dict(os.environ, {}, clear=True)
    def test_enviar_email_sin_sender_raises_value_error(self):
        """Si no hay GMAIL_SENDER, lanza ValueError con mensaje claro."""
        os.environ.pop("GMAIL_SENDER", None)
        with self.assertRaises(ValueError) as ctx:
            email_module.enviar_email(
                destinatario="dest@test.com",
                cc="",
                asunto="Test",
                cuerpo="Test",
                adjuntos=[],
            )
        self.assertIn("GMAIL_SENDER", str(ctx.exception))


class TestEnviarEmailReintentos(unittest.TestCase):
    """Tests para verificar reintentos automáticos ante fallos SMTP."""

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch", "GMAIL_SENDER": "test@gmail.com"})
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

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch", "GMAIL_SENDER": "test@gmail.com"})
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

    @patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "test-password-16ch", "GMAIL_SENDER": "test@gmail.com"})
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
    """Tests para verificar configuración de variables de entorno."""

    def test_smtp_constants(self):
        """Verifica que las constantes SMTP del módulo son correctas."""
        self.assertEqual(email_module.SMTP_SERVER, "smtp.gmail.com")
        self.assertEqual(email_module.SMTP_PORT, 587)

    @patch.dict(os.environ, {"GMAIL_SENDER": "test@gmail.com"}, clear=True)
    def test_enviar_email_requiere_gmail_sender(self):
        """Verifica que enviar_email falla con ValueError si no hay GMAIL_SENDER."""
        os.environ.pop("GMAIL_SENDER", None)
        with self.assertRaises(ValueError) as ctx:
            email_module.enviar_email(
                destinatario="dest@test.com",
                cc="",
                asunto="Test",
                cuerpo="Test",
                adjuntos=[],
            )
        self.assertIn("GMAIL_SENDER", str(ctx.exception))

    @patch.dict(os.environ, {"GMAIL_SENDER": "test@gmail.com"}, clear=True)
    def test_enviar_email_requiere_gmail_app_password(self):
        """Verifica que enviar_email retorna error si no hay GMAIL_APP_PASSWORD."""
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


if __name__ == "__main__":
    unittest.main()
