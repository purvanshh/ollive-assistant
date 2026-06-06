import os
from fastapi import Request, HTTPException
from backend.app.database import get_db

def verify_api_key(request: Request) -> None:
    """
    Dependency that verifies the request's API Key.
    Checks X-API-Key header, Authorization Bearer token, or api_key query param.
    """
    expected_key = os.getenv("API_KEY", "test_api_key_12345")
    
    # 1. Check header X-API-Key
    api_key = request.headers.get("X-API-Key")
    
    # 2. Check header Authorization: Bearer <key>
    if not api_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ")[1]
            
    # 3. Check query param api_key
    if not api_key:
        api_key = request.query_params.get("api_key")
        
    if api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
