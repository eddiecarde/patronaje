"""Tests de la app web (FastAPI): API sobre el motor real + descargas."""
import importlib.util

import pytest

_HAS_APP = (importlib.util.find_spec("fastapi") is not None
            and importlib.util.find_spec("httpx") is not None)
pytestmark = pytest.mark.skipif(not _HAS_APP, reason="FastAPI/httpx no instalados")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from patronaje.app import app
    return TestClient(app)


def test_config_exposes_garments_methods_sizes(client):
    cfg = client.get("/api/config").json()
    ids = [g["id"] for g in cfg["garments"]]
    assert ids == ["camisa", "falda", "pantalon", "vestido", "blazer"]
    assert {"aldrich", "mueller"} <= {m["id"] for m in cfg["methods"]}
    assert cfg["size_order"] == ["XS", "S", "M", "L", "XL", "XXL"]
    # cada prenda trae sus estilos y la tabla de tallas está poblada
    assert all(len(g["styles"]) >= 1 for g in cfg["garments"])
    assert cfg["sizes"]["S"]["busto"] > 0


def test_generate_by_size_returns_real_files(client):
    r = client.post("/api/generate", json={"garment": "camisa", "mode": "size",
                                            "size": "S", "method": "aldrich"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["stats"]["piezas"] == 10
    keys = {f["key"] for f in d["files"]}
    # los formatos de producción reales están presentes
    assert {"dxf_r2013", "dxf_aama", "svg", "pdf_1a1", "json", "techpack"} <= keys
    assert d["preview"] and d["preview"].endswith(".svg")
    # se pueden descargar el archivo y el ZIP
    fr = client.get(d["files"][0]["url"])
    assert fr.status_code == 200 and len(fr.content) > 0
    zr = client.get(d["zip"])
    assert zr.status_code == 200 and zr.headers["content-type"] == "application/zip"
    assert len(zr.content) > 1000


def test_generate_other_garments_and_styles(client):
    for garment, style in [("falda", "evase"), ("pantalon", "wide"),
                           ("vestido", "acampanada"), ("blazer", "clasica")]:
        r = client.post("/api/generate", json={"garment": garment, "mode": "size",
                                               "size": "M", "method": "mueller",
                                               "style": style})
        assert r.status_code == 200, (garment, r.text)
        assert r.json()["stats"]["piezas"] >= 2


def test_made_to_measure_and_validation(client):
    cfg = client.get("/api/config").json()
    meas = dict(cfg["sizes"]["S"])
    meas["busto"], meas["cintura"] = 96, 78          # medidas propias
    r = client.post("/api/generate", json={"garment": "camisa", "mode": "custom",
                                           "size": "S", "measurements": meas})
    assert r.status_code == 200, r.text
    assert r.json()["stats"]["piezas"] == 10
    # medidas incompletas/incoherentes -> 422 con incidencias
    bad = client.post("/api/generate", json={"garment": "camisa", "mode": "custom",
                                             "measurements": {"busto": 5}})
    assert bad.status_code == 422
    assert "issues" in bad.json()["detail"]


def test_home_and_viewers_served(client):
    assert client.get("/").status_code == 200
    assert "Genera tu patr" in client.get("/").text
    assert client.get("/viewer_live.html").status_code == 200
    assert client.get("/viewer_3d.html").status_code == 200


def test_bad_job_id_is_rejected(client):
    assert client.get("/api/file/notavalidjob/x.svg").status_code == 404
    assert client.get("/api/zip/..%2F..%2Fetc").status_code in (404, 400)
