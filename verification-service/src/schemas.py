from pydantic import BaseModel

class CredentialVerify(BaseModel):
    credential_id: str