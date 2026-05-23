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

## Qué No Hace el Agente Líder

- ❌ No escribe código directamente (lo delega al Developer).
- ❌ No ejecuta pruebas directamente (lo delega al Tester).
- ❌ No modifica especificaciones ni requisitos del usuario.
- ❌ No toma decisiones arquitectónicas sin consultar al usuario.
- ❌ No elimina archivos sin verificar dos veces la ruta.
- ❌ No ejecuta comandos destructivos en producción sin confirmación.

## Estructura del Proyecto (Refactor v4)

```
/Docs_SENA/
├── scripts/                          # Código ejecutable
│   ├── diligenciar.py
│   └── email_module.py
├── tests/                            # Pruebas
│   ├── test_diligenciar.py
│   └── test_email_module.py
├── contexto/                         # Datos de entrada y plantillas
│   ├── historico_actividades.md
│   ├── memory_descriptions.md
│   ├── BitacoraMQuiazua1.xlsx
│   ├── BitacoraMQuiazua_template.xlsx
│   ├── Actas-Inicio-Medio-Final.docx
│   └── FirmeManu.png
├── instrucciones/                    # Instrucciones para el agente
│   ├── AGENTS.md
│   └── sessions/
├── output/                           # Archivos generados
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── .venv/
```
