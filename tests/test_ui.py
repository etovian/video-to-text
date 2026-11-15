from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_static_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Video to Text" in response.text
    assert "NotebookLM" in response.text
    assert "drop-zone" in response.text

def test_static_css_and_js_served():
    resp_css = client.get("/style.css")
    assert resp_css.status_code == 200
    assert "transcript-preview" in resp_css.text

    resp_js = client.get("/app.js")
    assert resp_js.status_code == 200
    assert "listenForJobEvents" in resp_js.text
