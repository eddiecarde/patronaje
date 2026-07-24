# App para celular (APK Android, offline)

`patronaje/mobile.py` + `android/` convierten el proyecto en una **app Android
instalable** que funciona **sin servidor ni internet**. Eliges **prenda, talla y
estilo** y ves al instante el patrón trazado por el **motor real de Python**: los
SVG se **pre-generan** en tiempo de compilación y viajan dentro del APK. El modo
**a medida** usa el visor 2D en vivo (motor portado a JavaScript) que recalcula el
patrón base con tus medidas en el propio dispositivo. Incluye también el **maniquí
3D**.

## Por qué offline con motor JS (y no FastAPI dentro del APK)

FastAPI y los exportadores (shapely, ezdxf, reportlab) necesitan Python; no corren
dentro de un APK. Por eso la app móvil combina:

- **Patrones pre-generados** (SVG del motor Python) para el catálogo de prendas ×
  tallas × estilos — es el trazo real del motor.
- **Motor portado a JS** (visor en vivo) para el modo **a medida**, que sí necesita
  recalcular con medidas arbitrarias.

Los archivos de producción completos (DXF R2013, DXF AAMA/ASTM, PDF 1:1, tech pack,
markers…) siguen saliendo de la **app web / CLI** con el motor Python. La app móvil
exporta **SVG** (compartible desde el diálogo nativo de Android).

## Cómo obtener el APK

El APK se compila en **GitHub Actions** (el runner tiene el Android SDK). En la web
de este entorno **no se puede compilar** porque la política de red bloquea los repos
de Google (`dl.google.com`).

1. En GitHub: pestaña **Actions → workflow «APK» → Run workflow** (o publica una
   etiqueta `vX.Y`).
2. Al terminar, descarga el artefacto **`patronaje-apk`** (contiene
   `patronaje.apk` y `patronaje-debug.apk`).
3. Pásalo al teléfono e instálalo permitiendo **«instalar apps de orígenes
   desconocidos»** (es un APK firmado con clave *debug*, apto para pruebas y uso
   personal; para Play Store hace falta firma de *release* propia).

## Compilar en tu máquina (opcional)

Con **JDK 17**, el **Android SDK** (API 34) y acceso a los repos de Google:

```bash
python -m patronaje.mobile --output android/app/src/main/assets/www
cd android
./gradlew assembleRelease           # -> app/build/outputs/apk/release/app-release.apk
```

## Estructura

```
patronaje/mobile.py                     genera la app web offline (index.html + patterns/*.svg + visores)
android/
  app/src/main/assets/www/              (generado) la app web que carga el WebView
  app/src/main/java/.../MainActivity.java  WebView + puente para compartir SVG
  app/build.gradle, build.gradle, …     proyecto Gradle (AGP 8.5, minSdk 24, targetSdk 34)
  gradlew, gradle/wrapper/…             Gradle wrapper 8.7
.github/workflows/apk.yml               compila el APK y lo sube como artefacto
```

## Probar la app web (sin compilar el APK)

La misma app web offline se puede abrir en cualquier navegador:

```bash
python -m patronaje.mobile --output app_offline
cd app_offline && python -m http.server 8080     # http://localhost:8080
```

En un móvil, desde el navegador se puede **«Añadir a la pantalla de inicio»**
(es una PWA con `manifest.webmanifest`) para usarla como app sin instalar el APK.
