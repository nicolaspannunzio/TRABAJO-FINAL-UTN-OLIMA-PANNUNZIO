// Tipos del checklist, tomados del contrato generado (docs/openapi.json → types/api.ts).
import type { components } from '../../types/api'

export type ChecklistAbrir = components['schemas']['ChecklistAbrir']
export type ChecklistOut = components['schemas']['ChecklistOut']
export type FilaChecklist = components['schemas']['FilaChecklist']
export type EstadoChecklist = FilaChecklist['estado']
export type PropiedadOpcion = components['schemas']['PropiedadOut']
export type NoCorrespondeOut = components['schemas']['NoCorrespondeOut']
