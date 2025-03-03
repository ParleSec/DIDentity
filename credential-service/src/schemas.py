from pydantic import BaseModel

class CredentialIssue(BaseModel):
    holder_did: str
    credential_data: dict