from zipfile import ZipFile
from docx import Document
from app.storage.document_store import DocumentStore

def test_generated_docx_is_valid_and_has_sections(configured):
    client, _, _ = configured
    response = client.post("/agent", json={"request":"Create an operational plan with objectives, risks, and next steps."})
    assert response.status_code == 200
    path = configured[2].get(response.json()["document_id"])
    assert path and path.exists() and path.stat().st_size > 0
    with ZipFile(path) as archive:
        assert "word/document.xml" in archive.namelist()
        assert archive.testzip() is None
    document = Document(path)
    assert len(document.paragraphs) > 5

def test_unknown_document_id_is_not_served(configured):
    client, _, _ = configured
    assert client.get("/documents/../../secret").status_code in (404, 422)

def test_download_survives_a_new_store_instance(configured):
    client, _, store = configured
    response = client.post("/agent", json={"request":"Create an operational plan with objectives, risks, and next steps."})
    assert response.status_code == 200
    body = response.json()
    restarted_store = DocumentStore(store.output_dir)
    assert restarted_store.get(body["document_id"]) is not None

    from app.api.routes import router
    router.document_store = restarted_store
    download = client.get(body["download_url"])
    assert download.status_code == 200
    assert download.content[:2] == b"PK"

def test_invalid_uuid_document_id_is_not_served(configured):
    client, _, _ = configured
    assert client.get("/documents/not-a-uuid").status_code == 404
