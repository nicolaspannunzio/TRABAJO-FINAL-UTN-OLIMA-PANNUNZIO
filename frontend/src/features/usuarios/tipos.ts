// Tipos de usuarios, tomados del contrato generado (docs/openapi.json → types/api.ts).
import type { components } from '../../types/api'

export type UsuarioOut = components['schemas']['UsuarioOut']
export type UsuarioCrear = components['schemas']['UsuarioCrear']
export type UsuarioActualizar = components['schemas']['UsuarioActualizar']
export type Rol = UsuarioOut['rol']
