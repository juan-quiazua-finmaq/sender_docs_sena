import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def construir_asunto(bitacora_num, fecha_inicio, fecha_fin, acta_moment=None):
    """Construye el asunto dinámico según los documentos generados."""
    if bitacora_num is not None and acta_moment is not None:
        return (
            f"Bitácora {bitacora_num} y Acta Momento {acta_moment}"
            f" - Período {fecha_inicio} al {fecha_fin}"
        )
    elif bitacora_num is not None:
        return f"Bitácora {bitacora_num} - Período {fecha_inicio} al {fecha_fin}"
    elif acta_moment is not None:
        return f"Acta Momento {acta_moment}"
    else:
        return "Documentos SENA - Automatización"


def construir_cuerpo(fecha_inicio, fecha_fin, acta_moment=None):
    """Construye el cuerpo del email según la plantilla estandarizada."""
    cuerpo = f"Estimado instructor,\n\n"
    cuerpo += (
        f"Aquí está la bitácora referente al período {fecha_inicio} al {fecha_fin}."
    )
    if acta_moment is not None:
        cuerpo += (
            f"\n\nAdjunto también el acta correspondiente al Momento {acta_moment}."
        )
    cuerpo += (
        "\n\nNos gustaría saber si para la próxima semana o esta tiene"
        " disponibilidad para las correspondientes visitas."
    )
    cuerpo += "\n\nNo siendo más, agradecemos su tiempo."
    cuerpo += "\n\nCordialmente,\nManuel Quiazua y Finmaq"
    return cuerpo


def enviar_email(destinatario, cc, asunto, cuerpo, adjuntos, intentos=3):
    """Envía un correo electrónico con adjuntos usando Gmail SMTP.

    Args:
        destinatario: Dirección de correo del destinatario principal.
        cc: Dirección de correo para copia.
        asunto: Asunto del mensaje.
        cuerpo: Cuerpo del mensaje en texto plano.
        adjuntos: Lista de rutas de archivos a adjuntar.
        intentos: Número máximo de reintentos (default 3).

    Returns:
        Tuple[bool, str]: (éxito, mensaje descriptivo).
    """
    remitente = os.getenv("GMAIL_SENDER", "jmqo2026@gmail.com")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not password:
        return False, "Error: GMAIL_APP_PASSWORD no configurado en .env"

    for intento in range(1, intentos + 1):
        try:
            msg = MIMEMultipart()
            msg["From"] = remitente
            msg["To"] = destinatario
            if cc:
                msg["Cc"] = cc
            msg["Subject"] = asunto

            msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

            for filepath in adjuntos:
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(filepath)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}",
                    )
                    msg.attach(part)
                else:
                    print(
                        f"[Email] Advertencia: archivo no encontrado - {filepath}"
                    )

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.starttls()
            server.login(remitente, password)

            recipients = [destinatario]
            if cc:
                recipients.append(cc)
            server.sendmail(remitente, recipients, msg.as_string())
            server.quit()

            return True, f"Correo enviado exitosamente a {destinatario}"

        except smtplib.SMTPAuthenticationError:
            if intento < intentos:
                print(
                    f"[Email] Error de autenticación"
                    f" (intento {intento}/{intentos}). Reintentando..."
                )
                time.sleep(5)
            else:
                return (
                    False,
                    "Error de autenticación SMTP."
                    " Verifique las credenciales de correo en .env.",
                )
        except (smtplib.SMTPException, OSError) as e:
            if intento < intentos:
                print(
                    f"[Email] Error SMTP: {e}"
                    f" (intento {intento}/{intentos}). Reintentando..."
                )
                time.sleep(5)
            else:
                return (
                    False,
                    f"Error SMTP tras {intentos} intentos: {e}",
                )

    return False, "Error desconocido al enviar correo"


def reintentar_envio_manual(bitacora_num, output_dir):
    """Ofrece reintento manual tras fallos automáticos.

    Pregunta al usuario, resuelve destinatario desde .env y
    reenvía con los archivos del directorio de salida.

    Args:
        bitacora_num: Número de bitácora para el reintento.
        output_dir: Directorio donde están los archivos generados.

    Returns:
        bool: True si el reintento fue exitoso, False en caso contrario.
    """
    import glob

    respuesta = input(
        f"\n¿Desea reintentar el envío del correo"
        f" para la Bitácora {bitacora_num}? (s/n): "
    )
    if respuesta.lower() not in ["s", "si", "sí", "y", "yes"]:
        print("[Email] Reintento manual cancelado por el usuario.")
        return False

    modo = os.getenv("EMAIL_MODO", "pruebas")
    if modo == "produccion":
        destinatario = os.getenv(
            "EMAIL_DESTINATARIO_PRODUCCION", "oiospina@sena.edu.co"
        )
    else:
        destinatario = os.getenv(
            "EMAIL_DESTINATARIO_PRUEBAS", "jmqo2015@gmail.com"
        )
    cc = os.getenv("EMAIL_CC", "eivorkinkest@gmail.com")

    adjuntos = []
    for ext in ["*.xlsx", "*.docx"]:
        adjuntos.extend(glob.glob(os.path.join(output_dir, ext)))

    asunto = f"Reintento - Bitácora {bitacora_num}"
    cuerpo = "Documentos adjuntos correspondientes a la automatización SENA."

    print(f"[Email] Reintentando envío para Bitácora {bitacora_num}...")
    exito, mensaje = enviar_email(
        destinatario=destinatario,
        cc=cc,
        asunto=asunto,
        cuerpo=cuerpo,
        adjuntos=adjuntos,
        intentos=3,
    )

    if exito:
        print(f"[Email] {mensaje}")
    else:
        print(f"[Email] {mensaje}")

    return exito


def preguntar_envio_email():
    """Pregunta interactiva al usuario si desea enviar correo al finalizar.

    Returns:
        bool: True si el usuario autoriza el envío, False en caso contrario.
    """
    respuesta = input(
        "\n¿Desea enviar por correo electrónico"
        " los documentos generados al finalizar? (s/n): "
    )
    return respuesta.lower() in ["s", "si", "sí", "y", "yes"]
