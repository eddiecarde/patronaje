# Aplicación web (FastAPI)

`patronaje/app.py` convierte el proyecto en una **aplicación web**: expone el
**motor real de Python** detrás de una API REST y una interfaz donde eliges
prenda, talla o **medidas a medida**, método y estilo, generas el patrón y
**descargas los archivos listos para producción**. Integra los visores 2D en
vivo y el maniquí 3D.

A diferencia de los visores (que portan el motor a JavaScript para el navegador),
aquí la **fuente de verdad es Python**: los archivos descargables salen del mismo
motor que la CLI (`patronaje.cli.generate`), no de una reimplementación.

## Arrancar

```bash
pip install -r requirements.txt            # incluye fastapi + uvicorn
python -m patronaje.app                     # http://127.0.0.1:8000
# o, en desarrollo, con recarga:
uvicorn patronaje.app:app --reload
# o el script instalado:
patronaje-serve --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t patronaje .
docker run -p 8000:8000 patronaje          # http://localhost:8000
```

## Interfaz

- **Prenda**: camisa, falda, pantalón, vestido o blazer.
- **Medidas**: *por talla* (XS–XXL) o *a medida* (rellenas tus medidas; se parte
  de la tabla de la talla de referencia para los largos de prenda y se validan
  antes de trazar).
- **Método de trazado**: Aldrich, Müller & Sohn, Bunka, ESMOD, Martí, Armstrong.
- **Estilo**: la base o cualquiera de los estilos de la prenda.
- **Incluir margen de costura** (sí/no).

Al **Generar** aparecen las **métricas** (piezas, consumo a 150 cm, eficiencia de
tela), la **vista previa** del patrón, botones para abrir los **visores 2D/3D** y
**Descargar todo (ZIP)**, y la lista de **archivos descargables**: DXF R2013,
DXF AAMA/ASTM D6673, SVG, PDF 1:1 (mosaico), PDF A4, AI, JSON, CSV, SCR, tech
pack y markers 110/150/160 cm.

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/api/config` | Prendas + estilos, métodos, tabla de tallas y campos de medida. |
| `POST` | `/api/generate` | Genera el patrón y devuelve `job_id`, métricas, vista previa y lista de archivos. |
| `GET`  | `/api/file/{job_id}/{name}` | Descarga un archivo generado. |
| `GET`  | `/api/zip/{job_id}` | Descarga todos los archivos del trabajo en un ZIP. |
| `GET`  | `/viewer_live.html` · `/viewer_3d.html` | Visores 2D en vivo y maniquí 3D. |

Cuerpo de `POST /api/generate`:

```json
{
  "garment": "vestido",
  "mode": "size",                 
  "size": "M",
  "method": "aldrich",
  "style": "acampanada",
  "include_seam": true,
  "measurements": null            
}
```

Para modo `"custom"`, envía `mode: "custom"` y `measurements` con las medidas del
cuerpo; se validan y, si hay errores, la API responde **422** con las incidencias.

La documentación interactiva de la API (Swagger) está en `/docs` (la sirve
FastAPI automáticamente).

## Notas

- Cada generación crea un trabajo temporal con su `job_id`; los archivos se
  sirven desde ahí. Es apto para un despliegue de un contenedor; para producción
  con varios procesos conviene un almacenamiento compartido o limpieza periódica.
- El motor y los exportadores son los mismos que la CLI y el tech pack, así que
  el resultado es idéntico al de `python -m patronaje.cli`.
