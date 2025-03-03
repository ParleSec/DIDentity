from did_service.src.schemas import DIDCreate
import pytest

def test_did_create_schema():
    # Valid DID data
    valid_data = {
        "method": "key",
        "identifier": "test123"
    }
    did = DIDCreate(**valid_data)
    assert did.method == valid_data["method"]
    assert did.identifier == valid_data["identifier"]

    # Invalid method
    with pytest.raises(ValueError):
        DIDCreate(method="invalid", identifier="test123")