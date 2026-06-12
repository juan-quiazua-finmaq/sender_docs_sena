import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

MENSAJE_INSTRUCTOR_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "contexto",
    "mensaje_instructor.md",
)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def construir_asunto(bitacoras_info, acta_moment=None):
    """Construye el asunto dinámico según los documentos generados.

    Args:
        bitacoras_info: Lista de diccionarios con 'numero', 'fecha_inicio', 'fecha_fin'.
        acta_moment: Número de momento de acta (2 o 3), opcional.

    Returns:
        str: Asunto del correo.
    """
    if bitacoras_info:
        numeros = [str(b['numero']) for b in bitacoras_info]
        if len(numeros) == 1:
            numeros_str = numeros[0]
        elif len(numeros) == 2:
            numeros_str = f"{numeros[0]} y {numeros[1]}"
        else:
            numeros_str = ", ".join(numeros[:-1]) + f" y {numeros[-1]}"

        fecha_inicio = bitacoras_info[0]['fecha_inicio']
        fecha_fin = bitacoras_info[-1]['fecha_fin']

        if acta_moment is not None:
            return (
                f"Bitácoras {numeros_str} y Acta Momento {acta_moment}"
                f" — Período {fecha_inicio} al {fecha_fin}"
            )
        else:
            return f"Bitácoras {numeros_str} — Período {fecha_inicio} al {fecha_fin}"
    elif acta_moment is not None:
        return f"Acta Momento {acta_moment}"
    else:
        return "Documentos SENA - Automatización"


def construir_cuerpo(bitacoras_info, acta_moment=None):
    """Construye el cuerpo del email usando la plantilla markdown.

    Lee el archivo contexto/mensaje_instructor.md, reemplaza los placeholders
    con los datos reales y retorna el cuerpo en texto plano.

    Args:
        bitacoras_info: Lista de diccionarios con 'numero', 'fecha_inicio', 'fecha_fin'.
        acta_moment: Número de momento de acta (2 o 3), opcional.

    Returns:
        str: Cuerpo del mensaje en texto plano.
    """
    from datetime import datetime

    if os.path.exists(MENSAJE_INSTRUCTOR_PATH):
        with open(MENSAJE_INSTRUCTOR_PATH, "r", encoding="utf-8") as f:
            contenido = f.read()
        # Extraer solo el cuerpo después del separador ---
        if "---" in contenido:
            idx = contenido.index("---")
            cuerpo = contenido[idx + 3:].strip()
        else:
            cuerpo = contenido.strip()
    else:
        cuerpo = "Estimado instructor Oscar Ivan Ospina Ospina,\n\n"
        cuerpo += (
            "Reciba un cordial saludo. Por medio del presente correo, hago entrega de las "
            "bitácoras correspondientes a mi etapa productiva, las cuales detallo a continuación:\n\n"
        )

        for b in bitacoras_info:
            cuerpo += f"- Bitácora {b['numero']} ({b['fecha_inicio']} al {b['fecha_fin']})\n"

        if acta_moment is not None:
            cuerpo += (
                f"\nAdjunto también el acta correspondiente al Momento {acta_moment} (si aplica).\n"
            )

        cuerpo += (
            "\nNos gustaría saber si para la próxima semana o esta tiene disponibilidad "
            "para las correspondientes visitas.\n"
        )
        cuerpo += "\nNo siendo más, agradecemos su tiempo y atención.\n"
        cuerpo += "\nCordialmente,\nManuel Quiazua y Finmaq"
        return cuerpo

    # Reemplazar placeholders
    lista_bitacoras = "\n".join(
        f"- Bitácora {b['numero']} ({b['fecha_inicio']} al {b['fecha_fin']})"
        for b in bitacoras_info
    )

    if acta_moment is not None:
        acta_text = (
            f"\nAdjunto también el acta correspondiente al Momento {acta_moment} (si aplica).\n"
        )
    else:
        acta_text = ""

    fecha_ejecucion = datetime.now().strftime("%d/%m/%Y")
    destinatario = "instructor Oscar Ivan Ospina Ospina"
    firma = "Manuel Quiazua y Finmaq"

    cuerpo = cuerpo.replace("{{destinatario}}", destinatario)
    cuerpo = cuerpo.replace("{{lista_bitacoras}}", lista_bitacoras)
    cuerpo = cuerpo.replace("{{acta_moment}}", acta_text)
    cuerpo = cuerpo.replace("{{firma}}", firma)
    cuerpo = cuerpo.replace("{{fecha_ejecucion}}", fecha_ejecucion)

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
    remitente = os.getenv("GMAIL_SENDER")
    if not remitente:
        raise ValueError("GMAIL_SENDER no esta configurado en .env. Agregalo antes de continuar.")
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


def reintentar_envio_manual(bitacoras_info, output_dir, adjuntos=None):
    """Ofrece reintento manual tras fallos automáticos (versión por lote).

    Pregunta al usuario, resuelve destinatario desde .env y
    reenvía con los archivos del directorio de salida.

    Args:
        bitacoras_info: Lista de diccionarios con 'numero', 'fecha_inicio', 'fecha_fin'.
        output_dir: Directorio donde están los archivos generados.
        adjuntos: Lista de rutas de archivos a adjuntar (opcional).

    Returns:
        bool: True si el reintento fue exitoso, False en caso contrario.
    """
    import glob

    cant = len(bitacoras_info)
    numeros = [str(b['numero']) for b in bitacoras_info]
    numeros_str = ", ".join(numeros)

    respuesta = input(
        f"\n¿Desea reintentar el envío del correo"
        f" para las {cant} bitácora(s) {numeros_str}? (s/n): "
    )
    if respuesta.lower() not in ["s", "si", "sí", "y", "yes"]:
        print("[Email] Reintento manual cancelado por el usuario.")
        return False

    modo = os.getenv("EMAIL_MODO", "pruebas")
    if modo == "produccion":
        destinatario = os.getenv("EMAIL_DESTINATARIO_PRODUCCION")
    else:
        destinatario = os.getenv("EMAIL_DESTINATARIO_PRUEBAS")

    if not destinatario:
        raise ValueError(
            f"EMAIL_DESTINATARIO_{'PRODUCCION' if modo == 'produccion' else 'PRUEBAS'}"
            f" no esta configurado en .env. Agregalo antes de continuar."
        )

    cc = os.getenv("EMAIL_CC")
    if not cc:
        raise ValueError("EMAIL_CC no esta configurado en .env. Agregalo antes de continuar.")

    if adjuntos is None:
        adjuntos = []
        for ext in ["*.xlsx", "*.docx"]:
            adjuntos.extend(glob.glob(os.path.join(output_dir, ext)))

    asunto = construir_asunto(bitacoras_info)
    cuerpo = "Documentos adjuntos correspondientes a la automatización SENA."

    print(f"[Email] Reintentando envío para {cant} bitácora(s) {numeros_str}...")
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
