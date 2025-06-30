import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """Format dictionary as pretty JSON string"""
    return json.dumps(data, indent=indent, default=str)

def get_service_status(service_name: str) -> Dict[str, str]:
    """Get mock service status (in real implementation would call actual health endpoints)"""
    return {
        "status": "healthy",
        "uptime": "99.9%",
        "response_time": "< 100ms",
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def create_sample_credential_data(credential_type: str) -> Dict[str, Any]:
    """Create sample credential data based on type"""
    base_data = {
        "issuanceDate": datetime.now().isoformat(),
        "credentialType": credential_type,
        "issuer": "DIDentity Platform"
    }
    
    if credential_type == "EducationCredential":
        return {
            **base_data,
            "name": "John Doe",
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University of Technology",
            "graduationDate": "2023-05-15",
            "gpa": 3.8,
            "honors": "Magna Cum Laude"
        }
    elif credential_type == "EmploymentCredential":
        return {
            **base_data,
            "employeeName": "Jane Smith",
            "position": "Senior Software Engineer",
            "company": "Tech Innovations Inc.",
            "department": "Engineering",
            "startDate": "2022-01-15",
            "salary": 95000,
            "employmentType": "Full-time"
        }
    elif credential_type == "IdentityCredential":
        return {
            **base_data,
            "fullName": "Alex Johnson",
            "dateOfBirth": "1990-06-15",
            "nationality": "United States",
            "idNumber": f"ID{uuid.uuid4().hex[:8].upper()}",
            "issuingAuthority": "Department of Identity"
        }
    elif credential_type == "CertificationCredential":
        return {
            **base_data,
            "certificationName": "AWS Solutions Architect Professional",
            "issuingOrganization": "Amazon Web Services",
            "certificationDate": datetime.now().isoformat(),
            "expirationDate": (datetime.now() + timedelta(days=1095)).isoformat(),  # 3 years
            "certificationId": f"CERT{uuid.uuid4().hex[:8].upper()}",
            "level": "Professional"
        }
    else:
        return {
            **base_data,
            "title": "Generic Credential",
            "description": "A generic verifiable credential",
            "validUntil": (datetime.now() + timedelta(days=365)).isoformat()
        }

def generate_sample_did(method: str = "did:example") -> str:
    """Generate a sample DID for demonstration purposes"""
    identifier = uuid.uuid4().hex[:16]
    return f"{method}:{identifier}"

def validate_did_format(did: str) -> bool:
    """Basic DID format validation"""
    if not did.startswith("did:"):
        return False
    
    parts = did.split(":")
    if len(parts) < 3:
        return False
    
    return True

def get_credential_type_description(cred_type: str) -> str:
    """Get description for credential types"""
    descriptions = {
        "EducationCredential": "Academic achievements and educational qualifications",
        "EmploymentCredential": "Professional employment history and job details", 
        "IdentityCredential": "Personal identity information and official documentation",
        "CertificationCredential": "Professional certifications and skill validations"
    }
    return descriptions.get(cred_type, "Generic credential type")

def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return timestamp

def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string with ellipsis if too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_mock_metrics() -> Dict[str, Any]:
    """Get mock system metrics for demonstration"""
    return {
        "total_users": 1,
        "total_dids": 0,
        "total_credentials": 0,
        "total_verifications": 0,
        "system_uptime": "99.9%",
        "avg_response_time": "89ms",
        "active_sessions": 1,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    } 