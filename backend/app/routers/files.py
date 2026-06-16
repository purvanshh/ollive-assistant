import re
import csv
import io
import html
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from typing import Dict, Any

from backend.app.dependencies import verify_api_key

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(verify_api_key)]
)

def redact_pii(text: str) -> str:
    """
    Scans text and redacts Social Security Numbers (SSNs), 
    emails, and common phone number patterns.
    """
    # 1. Email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    # 2. SSN pattern: XXX-XX-XXXX
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    # 3. Common phone pattern: e.g. +1 555-555-5555, (555) 555-5555, 555-555-5555
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

    text = re.sub(email_pattern, "[REDACTED_EMAIL]", text)
    text = re.sub(ssn_pattern, "[REDACTED_SSN]", text)
    text = re.sub(phone_pattern, "[REDACTED_PHONE]", text)
    return text

def parse_pdf(content_bytes: bytes) -> str:
    """Extract text from PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)
    except Exception as e:
        # Fallback to regex-based raw string parsing if extraction fails
        text_chunks = re.findall(br'\((.*?)\)', content_bytes)
        extracted = []
        for chunk in text_chunks:
            try:
                s = chunk.decode('utf-8', errors='ignore')
                if len(s.strip()) > 3:
                    extracted.append(s.strip())
            except Exception:
                pass
        if extracted:
            return "\n".join(extracted)
        raise ValueError(f"Failed to parse PDF: {e}")

def parse_csv(content_bytes: bytes) -> str:
    """Extract and format rows from CSV."""
    text = content_bytes.decode('utf-8', errors='ignore')
    output = io.StringIO()
    reader = csv.reader(io.StringIO(text))
    writer = csv.writer(output)
    for row in reader:
        writer.writerow(row)
    return output.getvalue()

def parse_txt(content_bytes: bytes) -> str:
    """Extract text from TXT."""
    return content_bytes.decode('utf-8', errors='ignore')

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    redact: bool = Query(True, description="Enable PII redaction on extracted content")
) -> Dict[str, Any]:
    """
    Validate, parse, and redact PII from uploaded documents (PDF, CSV, TXT).
    Max file size: 10MB.
    """
    # 1. Validate file size up to 10MB
    content = await file.read()
    original_size = len(content)
    if original_size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10MB limit."
        )

    # 2. Magic byte / MIME type validation
    filename_lower = file.filename.lower() if file.filename else ""
    is_pdf = filename_lower.endswith(".pdf") or content.startswith(b"%PDF")
    is_csv = filename_lower.endswith(".csv") or file.content_type == "text/csv"
    is_txt = filename_lower.endswith(".txt") or file.content_type == "text/plain"

    if not (is_pdf or is_csv or is_txt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF, CSV, and TXT files are allowed."
        )

    # 3. Parse content
    try:
        if is_pdf:
            extracted_text = parse_pdf(content)
        elif is_csv:
            extracted_text = parse_csv(content)
        else:
            extracted_text = parse_txt(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error parsing file content: {e}"
        )

    # 4. Redact PII if enabled
    if redact:
        extracted_text = redact_pii(extracted_text)

    return {
        "filename": file.filename,
        "parsed_content": extracted_text,
        "original_size": original_size,
        "redacted": redact
    }
