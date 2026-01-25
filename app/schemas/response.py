from pydantic import BaseModel
from typing import Any

class APIResponse(BaseModel):
    success: bool
    data: Any | None = None
    errors: str | None = None