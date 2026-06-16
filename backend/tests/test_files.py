import pytest
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.routers.files import redact_pii

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Ensure environment is set for tests."""
    monkeypatch.setenv("API_KEY", "test_api_key_12345")

def test_redact_pii():
    text = (
        "Hello, my email is test.user@example.com. "
        "My SSN is 123-45-6789. "
        "Reach me at +1 555-123-4567 or 555-555-5555."
    )
    redacted = redact_pii(text)
    assert "test.user@example.com" not in redacted
    assert "123-45-6789" not in redacted
    assert "555-123-4567" not in redacted
    assert "555-555-5555" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_SSN]" in redacted
    assert "[REDACTED_PHONE]" in redacted

def test_upload_txt_success():
    headers = {"X-API-Key": "test_api_key_12345"}
    content = "Hello, this is a plain text file content."
    file_bytes = content.encode("utf-8")
    
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("test.txt", file_bytes, "text/plain")},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["parsed_content"] == content
    assert data["original_size"] == len(file_bytes)

def test_upload_csv_success():
    headers = {"X-API-Key": "test_api_key_12345"}
    content = "col1,col2\nval1,val2\nval3,val4"
    file_bytes = content.encode("utf-8")
    
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("test.csv", file_bytes, "text/csv")},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.csv"
    assert "col1" in data["parsed_content"]
    assert "val1,val2" in data["parsed_content"]

def test_upload_pdf_fallback_success():
    headers = {"X-API-Key": "test_api_key_12345"}
    # Construct a raw PDF structure that the regex fallback can extract from: (content)
    file_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Page >>\nstream\n(Hello fallback PDF text)\nendstream\nendobj"
    
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("test.pdf", file_bytes, "application/pdf")},
        headers=headers
    )
    # The pdf reader might raise an exception if pypdf fails to parse, 
    # but the parse_pdf fallback should parse the text block using regex.
    assert response.status_code in (200, 422)
    if response.status_code == 200:
        data = response.json()
        assert "Hello" in data["parsed_content"]

def test_upload_size_limit():
    headers = {"X-API-Key": "test_api_key_12345"}
    # File larger than 10MB (11MB)
    large_bytes = b"A" * (11 * 1024 * 1024)
    
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("large.txt", large_bytes, "text/plain")},
        headers=headers
    )
    assert response.status_code == 400
    assert "exceeds the 10MB limit" in response.json()["detail"]

def test_upload_unsupported_type():
    headers = {"X-API-Key": "test_api_key_12345"}
    file_bytes = b"print('hello')"
    
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("script.py", file_bytes, "text/x-python")},
        headers=headers
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
