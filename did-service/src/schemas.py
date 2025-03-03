from pydantic import BaseModel, Field

class DIDCreate(BaseModel):
    method: str = Field(..., pattern=r"^(key|web|ethr)$")
    identifier: str = Field(..., min_length=1, max_length=256)

class DIDDocument(BaseModel):
    id: str
    public_key: str
    authentication: list[str]