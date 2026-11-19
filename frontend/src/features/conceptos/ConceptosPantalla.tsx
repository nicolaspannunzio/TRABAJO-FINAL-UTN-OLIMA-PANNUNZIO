import { ConceptosLista } from './ConceptosLista'

// HU-05: catálogo de conceptos reutilizables en todas las propiedades.
export function ConceptosPantalla() {
  return (
    <div>
      <h1>Conceptos</h1>
      <ConceptosLista />
    </div>
  )
}