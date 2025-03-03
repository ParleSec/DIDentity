import pytest

@pytest.mark.asyncio
async def test_did_credential_flow(
    auth_client,
    did_client,
    credential_client,
    test_token
):
    # Create DID
    did_response = did_client.post(
        "/dids",
        json={"method": "key", "identifier": "test123"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert did_response.status_code == 200
    did_id = did_response.json()["id"]

    # Issue credential
    cred_response = credential_client.post(
        "/credentials/issue",
        json={
            "holder_did": did_id,
            "credential_data": {"name": "Test User", "degree": "BSc"}
        }
    )
    assert cred_response.status_code == 200
    assert "credential_id" in cred_response.json()