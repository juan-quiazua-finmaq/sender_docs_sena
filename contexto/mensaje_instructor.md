# Plantilla del Mensaje al Instructor

> Este archivo es la plantilla del cuerpo del correo electronico que se envia al instructor SENA con los documentos de bitacoras y actas.
> 
> **El usuario puede editar este archivo libremente** para personalizar el mensaje. El script `diligenciar.py` lo leera y reemplazara los placeholders con los datos reales antes de enviar el correo.
> 
> **Placeholders disponibles:**
> - `{{destinatario}}` — Nombre del instructor destinatario
> - `{{lista_bitacoras}}` — Lista de bitacoras con sus periodos (formato markdown)
> - `{{acta_moment}}` — Numero del momento del acta (2 o 3), o vacio si no aplica
> - `{{firma}}` — Nombre del aprendiz y empresa
> - `{{fecha_ejecucion}}` — Fecha de ejecucion del script (formato DD/MM/YYYY)

---

Estimado {{destinatario}},

Reciba un cordial saludo. Por medio del presente correo, hago entrega de las bitacoras correspondientes a mi etapa productiva, las cuales detallo a continuacion:

{{lista_bitacoras}}
{{acta_moment}}

Nos gustaria saber si para la proxima semana o esta tiene disponibilidad para las correspondientes visitas.

No siendo mas, agradecemos su tiempo y atencion.

Cordialmente,
{{firma}}
