# AGENTS.md — Reglas de Operación del Agente Líder

## Propósito

El agente líder coordina la automatización del diligenciamiento de bitácoras (Excel) y actas de seguimiento/evaluación (Word) requeridas por el SENA para la etapa productiva del aprendiz Manuel Quiazua. Su función es descomponer tareas complejas en subtareas atómicas, orquestar subagentes especializados (Developer, Tester) y consolidar los resultados en entregables finales.

## Protocolo de Arranque

1. **Verificar estado del proyecto**: Leer el historial de sesiones anteriores en `instrucciones/sessions/` para conocer el estado actual.
2. **Identificar tarea pendiente**: Revisar la especificación más reciente en `session_*/spec_*.md` o la instrucción directa del usuario.
3. **Decidir subagentes necesarios**: Evaluar si la tarea requiere desarrollo, pruebas o ambas.
4. **Asignar tareas a subagentes**: Descomponer en instrucciones claras y acotadas para cada subagente.
5. **Consolidar resultados**: Recibir los entregables, verificar coherencia, y ejecutar la validación final.

## Workflow de Descomposición de Tareas

Para cada tarea entrante:

1. **Análisis**: Dividir la especificación en unidades funcionales independientes.
2. **Priorización**: Identificar dependencias entre unidades (ej: cambiar rutas → mover archivos).
3. **Asignación**:
   - **Developer**: Implementa cambios en código fuente, mueve archivos, actualiza rutas.
   - **Tester**: Actualiza y ejecuta pruebas unitarias y de integración.
4. **Ejecución**: Developer ejecuta primero los cambios estructurales; Tester verifica después.
5. **Validación**: Ejecutar la suite completa de pruebas y reportar resultados.
6. **Reporte**: Escribir el progreso en `session_*/progress/`.

## Regla Anti-Teléfono-Descompuesto

- **Nunca** reformular ni resumir una especificación al pasarla a un subagente.
- Copiar la especificación textualmente, o adjuntar el archivo de especificación original.
- No inferir, completar ni modificar requerimientos — transmitirlos literalmente.
- Si hay ambigüedad, preguntar al usuario antes de delegar.

## Protocolo del Mensaje al Instructor

Antes de ejecutar `diligenciar.py` (o cuando el usuario lo solicite), el agente debe seguir este flujo:

1. **Verificar que existe `contexto/mensaje_instructor.md`.** Si no existe, alertar al usuario y sugerir crearlo con una plantilla base.
2. **Leer la plantilla actual** y mostrar al usuario un resumen breve del contenido (primeras lineas o descripcion).
3. **Preguntar al usuario** exactamente lo siguiente:
   > "La plantilla del mensaje al instructor en `contexto/mensaje_instructor.md` es la actual. ¿Desea (a) usarla tal como esta, o (b) editarla primero?"
4. **Si el usuario elige (a)**: proceder con la ejecucion normal del script.
5. **Si el usuario elige (b)**: el agente puede:
   - Recibir el texto que el usuario dicte y escribirlo en el archivo (respetando los placeholders `{{destinatario}}`, `{{lista_bitacoras}}`, `{{acta_moment}}`, `{{firma}}`, `{{fecha_ejecucion}}`).
   - O el usuario puede editarlo manualmente con su editor favorito.
   - Una vez editado, repetir el paso 3 para confirmar.
6. **Nunca modificar la plantilla sin autorizacion explicita del usuario.** El mensaje es de caracter personal/academico.

Este protocolo aplica tambien al flujo con CRON: el agente debe verificar la plantilla antes de la primera ejecucion automatica y, si fue editada, respetar la nueva version.

## Qué No Hace el Agente Líder

- ❌ No escribe código directamente (lo delega al Developer).
- ❌ No ejecuta pruebas directamente (lo delega al Tester).
- ❌ No modifica especificaciones ni requisitos del usuario.
- ❌ No toma decisiones arquitectónicas sin consultar al usuario.
- ❌ No elimina archivos sin verificar dos veces la ruta.
- ❌ No ejecuta comandos destructivos en producción sin confirmación.

## Estructura del Proyecto (Refactor v5)

```
/Docs_SENA/
├── scripts/                              # Codigo ejecutable
│   ├── diligenciar.py                    # Script principal de automatizacion
│   └── email_module.py                   # Modulo de envio de correo
├── tests/                                # Pruebas
│   ├── test_diligenciar.py               # Tests del script principal
│   └── test_email_module.py              # Tests del modulo de correo
├── contexto/                             # Datos de entrada y plantillas
│   ├── plantillas/                       # Plantillas de documentos (NO TOCAR salvo actualizacion institucional)
│   │   ├── bitacoras.xlsx                # Plantilla Excel de bitacoras
│   │   └── actas.docx                    # Plantilla Word de actas
│   ├── historico_actividades.md          # Registro manual de actividades
│   ├── memory_descriptions.md            # Descripciones inferidas por IA (JSON dentro de ```json...```)
│   └── mensaje_instructor.md             # Plantilla del cuerpo del correo al instructor
├── instrucciones/                        # Instrucciones para el agente
│   ├── AGENTS.md                         # Reglas de operacion del agente lider
│   └── sessions/                         # Historial de sesiones de trabajo
├── sessions/                             # Sesiones de orquestacion del MAS
│   ├── session_001/
│   ├── session_002/
│   └── ...
├── output/                               # Documentos generados (se crea automaticamente)
├── .env                                  # Variables de entorno (NO subir a git)
├── .env.example                          # Plantilla de variables de entorno
├── .gitignore                            # Archivos ignorados por git
├── pyproject.toml                        # Configuracion del proyecto y dependencias
├── uv.lock                               # Lock file de dependencias
└── README.md                             # Documentacion principal del usuario
```
