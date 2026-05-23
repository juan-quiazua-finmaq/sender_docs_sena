# Especificación: Capa de Email para Automatización SENA

## 1. Objetivo Principal

Agregar una capa de envío de correo electrónico (Gmail) al proceso de automatización existente, de modo que **antes de iniciar la ejecución** el Agente orquestador pregunte al usuario si desea enviar un correo al instructor de seguimiento con los documentos generados.

## 2. Configuración de Correos

| Rol | Email | Modo |
|-----|-------|------|
| Remitente | jmqo2026@gmail.com | Fijo |
| Destinatario (producción) | oiospina@sena.edu.co | Variable por entorno |
| Destinatario (pruebas) | jmqo2015@gmail.com | Variable por entorno |
| CC (monitorización) | eivorkinkest@gmail.com | Fijo |

## 3. Autenticación

- Método: App Password de Gmail
- Almacenamiento: Archivo `.env` (variable `GMAIL_APP_PASSWORD`)
- El archivo `.env` debe estar en `.gitignore`

## 4. Flujo de Usuario

1. Script inicia
2. **Preguntar antes de ejecutar**: "¿Desea enviar por correo electrónico los documentos generados al finalizar? (s/n)"
3. Si "Sí": ejecutar normal + enviar correo al finalizar
4. Si "No": ejecutar normal sin envío

## 5. Plantilla de Correo

**Asunto (varía según documentos):**
- Solo bitácora: `Bitácora <N> - Período <fecha_inicio> al <fecha_fin>`
- Bitácora + Acta: `Bitácora <N> y Acta Momento <M> - Período <fecha_inicio> al <fecha_fin>`
- Solo Acta: `Acta Momento <M>`

**Cuerpo:**
```
Estimado instructor,

Aquí está la bitácora referente al período <fecha_inicio> al <fecha_fin>.
{Si aplica: Adjunto también el acta correspondiente al Momento <M>.}

Nos gustaría saber si para la próxima semana o esta tiene disponibilidad para las correspondientes visitas.

No siendo más, agradecemos su tiempo.

Cordialmente,
Manuel Quiazua y Finmaq
```

## 6. Reintentos

- Máximo 3 intentos automáticos
- Si fallan los 3: notificar y ofrecer reintento manual para bitácora específica

## 7. Criterios de Aceptación

- [ ] Pregunta antes de ejecutar
- [ ] Envío desde jmqo2026@gmail.com
- [ ] Destinatario configurable (producción/pruebas)
- [ ] CC a eivorkinkest@gmail.com
- [ ] Cuerpo con plantilla estandarizada
- [ ] Asunto dinámico según documentos
- [ ] .env con credenciales, .gitignore actualizado
- [ ] 3 reintentos automáticos
- [ ] Opción de reintento manual tras fallos
- [ ] dry-run muestra correo simulado
