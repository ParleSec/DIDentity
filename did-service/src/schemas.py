from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import re

class DIDMethod(str, Enum):
    KEY = "key"
    WEB = "web"
    ETHR = "ethr"
    SOV = "sov"
    ION = "ion"

class DIDCreate(BaseModel):
    method: DIDMethod = Field(..., description="DID method (key, web, ethr, sov, ion)")
    identifier: str = Field(..., min_length=1, max_length=256)
    controller: Optional[str] = Field(None, description="The controller of the DID")
    
    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v, info):
        method = info.data.get('method') if info.data else None
        if method == DIDMethod.KEY:
            # Base58 encoded for key method
            if not re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', v):
                raise ValueError("Key identifier must be valid Base58 format")
        elif method == DIDMethod.WEB:
            # Valid domain name for web method
            if not re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$', v):
                raise ValueError("Web identifier must be a valid domain name")
        elif method == DIDMethod.ETHR:
            # Ethereum address for ethr method
            if not re.match(r'^0x[0-9a-fA-F]{40}$', v):
                raise ValueError("Ethereum identifier must be a valid Ethereum address")
        return v

class VerificationMethod(BaseModel):
    id: str
    type: str
    controller: str
    publicKeyJwk: Optional[Dict[str, Any]] = None
    publicKeyBase58: Optional[str] = None
    publicKeyMultibase: Optional[str] = None
    blockchainAccountId: Optional[str] = None

class ServiceEndpoint(BaseModel):
    id: str
    type: str
    serviceEndpoint: Union[HttpUrl, List[HttpUrl]]
    description: Optional[str] = None

class DIDDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    context: Union[str, List[str]] = Field("https://www.w3.org/ns/did/v1", alias="@context")
    controller: Optional[str] = None
    verificationMethod: List[VerificationMethod] = []
    authentication: List[Union[str, VerificationMethod]] = []
    assertionMethod: Optional[List[Union[str, VerificationMethod]]] = None
    keyAgreement: Optional[List[Union[str, VerificationMethod]]] = None
    capabilityInvocation: Optional[List[Union[str, VerificationMethod]]] = None
    capabilityDelegation: Optional[List[Union[str, VerificationMethod]]] = None
    service: Optional[List[ServiceEndpoint]] = None

class DIDResolutionMetadata(BaseModel):
    contentType: str = "application/did+json"
    retrieved: str  # ISO8601 timestamp
    error: Optional[str] = None

class DIDDocumentMetadata(BaseModel):
    created: Optional[str] = None  # ISO8601 timestamp
    updated: Optional[str] = None  # ISO8601 timestamp
    deactivated: Optional[bool] = None
    versionId: Optional[str] = None

class DIDResolution(BaseModel):
    didResolutionMetadata: DIDResolutionMetadata
    didDocument: DIDDocument
    didDocumentMetadata: DIDDocumentMetadata