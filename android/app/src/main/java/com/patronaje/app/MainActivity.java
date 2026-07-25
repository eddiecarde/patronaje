package com.patronaje.app;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.FileProvider;
import androidx.webkit.WebViewAssetLoader;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;

/**
 * App Patronaje: un WebView a pantalla completa que carga la app web offline
 * empaquetada en assets/www (motor de patrones pre-generado + visores 2D/3D).
 *
 * Los recursos se sirven con {@link WebViewAssetLoader} bajo un origen virtual
 * https://appassets.androidplatform.net/ en vez de file://, para que fetch()
 * (que carga index.json y los SVG de patrones) funcione: en un origen file://
 * el WebView bloquea fetch/XHR y la app se quedaría en «Cargando…».
 * No requiere red: todo el contenido va dentro del APK.
 */
public class MainActivity extends AppCompatActivity {

    private static final String BASE = "https://appassets.androidplatform.net";
    private WebView web;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }
        });

        web.addJavascriptInterface(new Bridge(), "Android");
        web.loadUrl(BASE + "/assets/www/index.html");

        // botón atrás: navega dentro del WebView antes de salir
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (web.canGoBack()) {
                    web.goBack();
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });
    }

    /** Puente JS -> Android para guardar/compartir el SVG generado. */
    private class Bridge {
        @JavascriptInterface
        public void shareSvg(String name, String content) {
            try {
                File dir = new File(getCacheDir(), "shared");
                if (!dir.exists()) dir.mkdirs();
                String safe = name.replaceAll("[^A-Za-z0-9_.-]", "_");
                if (!safe.toLowerCase().endsWith(".svg")) safe = safe + ".svg";
                File out = new File(dir, safe);
                try (FileOutputStream fos = new FileOutputStream(out)) {
                    fos.write(content.getBytes(StandardCharsets.UTF_8));
                }
                Uri uri = FileProvider.getUriForFile(
                        MainActivity.this, "com.patronaje.app.fileprovider", out);
                Intent send = new Intent(Intent.ACTION_SEND);
                send.setType("image/svg+xml");
                send.putExtra(Intent.EXTRA_STREAM, uri);
                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                runOnUiThread(() -> startActivity(
                        Intent.createChooser(send, "Compartir patrón")));
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(
                        MainActivity.this, "No se pudo compartir: " + e.getMessage(),
                        Toast.LENGTH_LONG).show());
            }
        }
    }
}
