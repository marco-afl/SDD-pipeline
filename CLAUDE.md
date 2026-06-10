# SDD-Pipeline — Claude Code Instructions

## Propósito del proyecto

Este repositorio implementa un pipeline de **Spec-Driven Development (SDD)**: un flujo de trabajo donde cada pieza de código parte de una especificación humana aprobada. El agente asiste en tres fases ordenadas: **especificación → plan → código**. Nunca salta fases ni toma decisiones de diseño de forma autónoma.

---

## Reglas de comportamiento (no negociables)

### Lo que el agente DEBE hacer
- Guiar al usuario a través de las fases SDD en orden: Story → Plan → Code.
- Hacer preguntas clarificadoras antes de redactar cualquier especificación.
- Presentar opciones de diseño con sus trade-offs y esperar aprobación explícita antes de continuar.
- Marcar claramente qué archivos son "producción" (ver sección de estructura) y pedir confirmación antes de tocarlos.
- Generar código solo contra una especificación aprobada y un plan aprobado.

### Lo que el agente NUNCA debe hacer
- Modificar archivos de producción sin aprobación humana explícita en esa misma conversación.
- Tomar decisiones de arquitectura (elección de framework, estructura de BD, patrones de diseño) sin presentarlas primero y obtener el visto bueno.
- Combinar fases: no redactar código mientras aún se define la especificación.
- Asumir requerimientos no mencionados explícitamente por el usuario.
- Hacer `git push`, desplegar, ni modificar pipelines de CI/CD sin instrucción directa.

---

## Flujo SDD

```
1. STORY  →  2. PLAN  →  3. CODE  →  4. REVIEW
```

### Fase 1 — Story (User Story)
- Recopilar: actor, objetivo, criterios de aceptación, casos límite.
- Formato de salida obligatorio: ver plantilla `story.md` más abajo.
- La story queda bloqueada hasta que el usuario escriba **"APROBADO"** o equivalente.

### Fase 2 — Plan
- Descomponer la story en tareas técnicas ordenadas.
- Identificar archivos a crear/modificar, dependencias, riesgos.
- Presentar alternativas de diseño con pros/contras cuando existan.
- El plan queda bloqueado hasta aprobación humana.

### Fase 3 — Code
- Implementar solo lo que el plan aprobado indica.
- Un PR / commit por story.
- No agregar funcionalidad extra ("mientras estoy aquí también cambio X").

### Fase 4 — Review
- Ejecutar `/code-review` antes de marcar la story como completa.
- Reportar hallazgos al usuario; no auto-corregir sin indicación.

---

## Plantillas

### story.md
```markdown
## Story: [ID] — [Título corto]

**Como** [actor]
**Quiero** [acción o capacidad]
**Para** [beneficio o resultado]

### Criterios de aceptación
- [ ] CA-1: …
- [ ] CA-2: …

### Casos límite
- …

### Fuera de scope
- …

### Estado
- [ ] Borrador  [ ] Aprobado  [ ] En desarrollo  [ ] Completo
```

### plan.md
```markdown
## Plan: [Story ID]

### Archivos involucrados
| Archivo | Acción | Entorno |
|---------|--------|---------|
| src/… | crear | dev |
| … | modificar | **producción** ⚠️ |

### Tareas
1. …
2. …

### Decisiones de diseño
| Opción | Pros | Contras | Decisión |
|--------|------|---------|----------|
| … | … | … | pendiente |

### Riesgos
- …

### Estado
- [ ] Borrador  [ ] Aprobado
```

---

## Estructura del repositorio

```
SDD-pipeline/
├── specs/          # Stories y planes aprobados (fuente de verdad)
│   ├── stories/
│   └── plans/
├── src/            # Código fuente (requiere aprobación para modificar)
├── tests/
├── .claude/        # Configuración de Claude Code
└── CLAUDE.md       # Este archivo
```

Los archivos bajo `src/` y cualquier archivo de configuración de infraestructura (`docker-compose.yml`, workflows de CI, archivos de entorno) se consideran **producción** a efectos de este pipeline.

---

## Comandos útiles de Claude Code

| Comando | Uso |
|---------|-----|
| `/code-review` | Revisar cambios antes de cerrar una story |
| `/security-review` | Revisar el branch por vulnerabilidades |
| `/plan` | Activar el agente planificador |
| `EnterPlanMode` | Diseñar sin escribir código todavía |

---

## Contexto del proyecto

- **Objetivo**: Construir y documentar un pipeline SDD reutilizable con Claude Code como motor de asistencia.
- **Estado actual**: Proyecto en fase inicial (solo README).
- **Prioridad de diseño**: Claridad del proceso sobre velocidad de entrega.
