# Changelog

Todos los cambios notables de **Patronaje**. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es/1.1.0/); versionado
[SemVer](https://semver.org/lang/es/).

## [0.2.0] — 2026-07-21

### Añadido
- **Plataforma web** (`index.html`): página de inicio unificada con configurador
  (talla / cuerpo / prenda + medidas editables, prefijadas por talla o cargadas
  por JSON) que abre el patrón 2D o el maniquí 3D con la configuración aplicada
  por query-string. Barra de navegación común en los tres visores. Offline.
- **Maniquí 3D como superficie implícita** (SDF + Surface Nets): brazos, piernas,
  busto/glúteos y manos fundidos con el torso en una sola superficie continua;
  relieve de lona por triplanar; hombro con caída; perfil lateral en S.
- **LICENSE** (MIT) y **NOTICE** con la atribución de three.js (MIT).
- **CI**: instala Playwright + Chromium y ejecuta los tests de render WebGL y
  simulación del visor 3D; medición de **cobertura**.
- Workflows de **GitHub Pages** (deploy del visor) y de **release** (por tag).

### Cambiado
- El visor 3D pasó de un renderizador por software a **WebGL/PBR (three.js)** y
  luego a la superficie implícita; la simulación de caída (PBD) se conserva.

## [0.1.0]

### Añadido
- Motor paramétrico (métodos Aldrich, Müller, Bunka, Esmod), 5 prendas (camisa,
  falda, pantalón, vestido, blazer), bloque entallado con pinzas, made-to-measure.
- Exportadores CAD: DXF R2013, DXF AAMA/ASTM, SVG, PDF 1:1 y A4, AI, JSON, CSV,
  SCR; grading XS–XXL con nido; tech pack HTML; plano de corte (marker).
- Visores 2D (variantes y en vivo) y maniquí 3D (Opción A/B).
