export function Cargando({ mensaje = 'Cargando…' }: { mensaje?: string }) {
  return (
    <p role="status" aria-live="polite">
      {mensaje} <small>(si el servidor estaba inactivo, puede tardar unos segundos)</small>
    </p>
  )
}