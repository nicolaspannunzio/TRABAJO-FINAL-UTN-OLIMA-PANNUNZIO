import { PropiedadesLista } from './PropiedadesLista'
import { PropietariosLista } from './PropietariosLista'

// HU-03: los datos maestros del reparto. Propiedades y propietarios comparten pantalla
// (y la ruta /propiedades), así no hace falta tocar el árbol de rutas compartido.
export function PropiedadesPantalla() {
  return (
    <div>
      <h1>Propiedades y propietarios</h1>
      <PropiedadesLista />
      <PropietariosLista />
    </div>
  )
}
