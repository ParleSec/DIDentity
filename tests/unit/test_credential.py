from credential_service.src.schemas import CredentialIssue
import pytest

def test_credential_issue_schema():
    valid_data = {
        "holder_did": "did:key:test123",
        "credential_data": {
            "name": "Test User",
            "degree": "BSc"
        }
    }
    cred = CredentialIssue(**valid_data)
    assert cred.holder_did == valid_data["holder_did"]
    assert cred.credential_data == valid_data["credential_data"]