import streamlit as st
import requests
import json
from datetime import datetime
import uuid
from typing import Dict, Any
from api_client import DIDentityClient
from utils import format_json, get_service_status, create_sample_credential_data

# Page configuration
st.set_page_config(
    page_title="DIDentity Platform Demo",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize client
if 'client' not in st.session_state:
    st.session_state.client = DIDentityClient()

# Session state initialization
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'created_dids' not in st.session_state:
    st.session_state.created_dids = []
if 'issued_credentials' not in st.session_state:
    st.session_state.issued_credentials = []

def main():
    st.title("🆔 DIDentity Platform Demo")
    st.markdown("**Decentralized Identity Management Platform**")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("🎯 Navigation")
        page = st.selectbox(
            "Choose a demo section:",
            [
                "🏠 Dashboard",
                "👤 Authentication",
                "🆔 DID Management", 
                "📜 Credential Management",
                "✅ Verification Service",
                "📊 Service Health",
                "📖 API Documentation"
            ]
        )
        
        # User status
        st.markdown("---")
        if st.session_state.access_token:
            st.success(f"✅ Logged in as: {st.session_state.current_user}")
            if st.button("🚪 Logout"):
                st.session_state.access_token = None
                st.session_state.current_user = None
                st.rerun()
        else:
            st.info("🔒 Not authenticated")

    # Route to different pages
    if page.startswith("🏠"):
        show_dashboard()
    elif page.startswith("👤"):
        show_authentication()
    elif page.startswith("🆔"):
        show_did_management()
    elif page.startswith("📜"):
        show_credential_management()
    elif page.startswith("✅"):
        show_verification()
    elif page.startswith("📊"):
        show_service_health()
    elif page.startswith("📖"):
        show_api_docs()

def show_dashboard():
    st.header("🏠 Platform Dashboard")
    
    # Service overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Auth Service", "🟢 Active", help="User authentication & JWT tokens")
        
    with col2:
        st.metric("DID Service", "🟢 Active", help="Decentralized identifier management")
        
    with col3:
        st.metric("Credential Service", "🟢 Active", help="Verifiable credential issuance")
        
    with col4:
        st.metric("Verification Service", "🟢 Active", help="Credential verification")
    
    st.markdown("---")
    
    # Platform overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 What is DIDentity?")
        st.markdown("""
        **DIDentity** is a comprehensive decentralized identity management platform that provides:
        
        - **🔐 Authentication**: Secure user registration and login with JWT tokens
        - **🆔 DID Management**: Create and resolve decentralized identifiers
        - **📜 Credential Issuance**: Issue verifiable digital credentials
        - **✅ Verification**: Verify the authenticity of credentials
        - **📊 Monitoring**: Real-time health monitoring and metrics
        """)
        
        if not st.session_state.access_token:
            st.info("👈 Start by authenticating in the Authentication section to explore all features!")
        else:
            st.success("🎉 You're authenticated! Explore all the platform features.")
    
    with col2:
        st.subheader("📈 Quick Stats")
        
        # Display session stats
        stats_data = {
            "DIDs Created": len(st.session_state.created_dids),
            "Credentials Issued": len(st.session_state.issued_credentials),
            "Session Active": "Yes" if st.session_state.access_token else "No"
        }
        
        for key, value in stats_data.items():
            st.metric(key, value)
    
    # Recent activity
    if st.session_state.created_dids or st.session_state.issued_credentials:
        st.subheader("📋 Recent Activity")
        
        if st.session_state.created_dids:
            with st.expander("Recent DIDs"):
                for did in st.session_state.created_dids[-3:]:
                    st.code(did, language="text")
        
        if st.session_state.issued_credentials:
            with st.expander("Recent Credentials"):
                for cred in st.session_state.issued_credentials[-3:]:
                    st.code(cred, language="text")

def show_authentication():
    st.header("👤 Authentication Service")
    st.markdown("Manage user registration, login, and JWT token operations.")
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login/Register", "🔑 Token Management", "👥 User Info"])
    
    with tab1:
        if not st.session_state.access_token:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📝 Register New User")
                with st.form("register_form"):
                    reg_username = st.text_input("Username", key="reg_username")
                    reg_email = st.text_input("Email", key="reg_email")
                    reg_password = st.text_input("Password", type="password", key="reg_password")
                    
                    if st.form_submit_button("Register"):
                        if reg_username and reg_email and reg_password:
                            try:
                                result = st.session_state.client.register_user(
                                    reg_username, reg_email, reg_password
                                )
                                st.success("✅ Registration successful!")
                                st.json(result)
                            except Exception as e:
                                st.error(f"❌ Registration failed: {str(e)}")
                        else:
                            st.warning("⚠️ Please fill all fields")
            
            with col2:
                st.subheader("🔑 Login")
                with st.form("login_form"):
                    login_username = st.text_input("Username", key="login_username")
                    login_password = st.text_input("Password", type="password", key="login_password")
                    
                    if st.form_submit_button("Login"):
                        if login_username and login_password:
                            try:
                                result = st.session_state.client.login_user(login_username, login_password)
                                st.session_state.access_token = result["access_token"]
                                st.session_state.current_user = login_username
                                st.success("✅ Login successful!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Login failed: {str(e)}")
                        else:
                            st.warning("⚠️ Please fill all fields")
        else:
            st.success(f"✅ Already authenticated as: {st.session_state.current_user}")
    
    with tab2:
        if st.session_state.access_token:
            st.subheader("🔑 Token Operations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Current Access Token:**")
                st.code(st.session_state.access_token[:50] + "..." if len(st.session_state.access_token) > 50 else st.session_state.access_token)
                
                if st.button("🔄 Refresh Token"):
                    try:
                        # Note: This would need refresh token implementation
                        st.info("🔄 Token refresh functionality would be implemented here")
                    except Exception as e:
                        st.error(f"❌ Token refresh failed: {str(e)}")
            
            with col2:
                if st.button("🚪 Revoke Token"):
                    try:
                        st.session_state.client.revoke_token(st.session_state.access_token)
                        st.session_state.access_token = None
                        st.session_state.current_user = None
                        st.success("✅ Token revoked successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Token revocation failed: {str(e)}")
        else:
            st.info("🔒 Please authenticate first to manage tokens")
    
    with tab3:
        if st.session_state.access_token:
            st.subheader("👤 Current User Information")
            user_info = {
                "Username": st.session_state.current_user,
                "Token Status": "Active",
                "Login Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Token Preview": st.session_state.access_token[:20] + "..."
            }
            
            for key, value in user_info.items():
                st.text(f"{key}: {value}")
        else:
            st.info("🔒 Please authenticate to view user information")

def show_did_management():
    st.header("🆔 DID Management Service")
    st.markdown("Create and resolve Decentralized Identifiers (DIDs).")
    
    if not st.session_state.access_token:
        st.warning("🔒 Please authenticate first to manage DIDs")
        return
    
    tab1, tab2, tab3 = st.tabs(["➕ Create DID", "🔍 Resolve DID", "📋 My DIDs"])
    
    with tab1:
        st.subheader("➕ Create New DID")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("create_did_form"):
                did_method = st.selectbox(
                    "DID Method",
                    ["did:key", "did:web", "did:ethr", "did:example"],
                    help="Choose the DID method type"
                )
                
                controller = st.text_input(
                    "Controller (optional)", 
                    help="Leave empty to use the DID itself as controller"
                )
                
                if st.form_submit_button("🚀 Create DID"):
                    try:
                        result = st.session_state.client.create_did(did_method, controller or None)
                        
                        new_did = result["did"]
                        st.session_state.created_dids.append(new_did)
                        
                        st.success(f"✅ DID created successfully!")
                        st.json(result)
                        
                    except Exception as e:
                        st.error(f"❌ DID creation failed: {str(e)}")
        
        with col2:
            st.info("""
            **DID Methods:**
            - `key`: Cryptographic key-based
            - `web`: Web-based identifiers  
            - `ethr`: Ethereum blockchain
            - `example`: Example/testing method
            """)
    
    with tab2:
        st.subheader("🔍 Resolve DID")
        
        with st.form("resolve_did_form"):
            did_to_resolve = st.text_input(
                "DID to Resolve",
                placeholder="did:example:123456789abcdefghi",
                help="Enter a DID to retrieve its document"
            )
            
            if st.form_submit_button("🔍 Resolve"):
                if did_to_resolve:
                    try:
                        result = st.session_state.client.resolve_did(did_to_resolve)
                        st.success("✅ DID resolved successfully!")
                        st.json(result)
                    except Exception as e:
                        st.error(f"❌ DID resolution failed: {str(e)}")
                else:
                    st.warning("⚠️ Please enter a DID to resolve")
    
    with tab3:
        st.subheader("📋 Created DIDs in This Session")
        
        if st.session_state.created_dids:
            for i, did in enumerate(st.session_state.created_dids):
                with st.expander(f"DID #{i+1}: {did[:30]}..."):
                    st.code(did, language="text")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔍 Resolve", key=f"resolve_{i}"):
                            try:
                                result = st.session_state.client.resolve_did(did)
                                st.json(result)
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col2:
                        if st.button(f"📋 Copy", key=f"copy_{i}"):
                            st.code(did)
        else:
            st.info("🔍 No DIDs created in this session yet. Create one above!")

def show_credential_management():
    st.header("📜 Credential Management Service")
    st.markdown("Issue verifiable credentials for DIDs.")
    
    if not st.session_state.access_token:
        st.warning("🔒 Please authenticate first to manage credentials")
        return
    
    tab1, tab2 = st.tabs(["📝 Issue Credential", "📋 Issued Credentials"])
    
    with tab1:
        st.subheader("📝 Issue New Credential")
        
        if not st.session_state.created_dids:
            st.warning("⚠️ You need to create a DID first before issuing credentials!")
            st.info("👆 Use the navigation in the sidebar to go to DID Management first.")
            return
        
        with st.form("issue_credential_form"):
            holder_did = st.selectbox(
                "Holder DID",
                st.session_state.created_dids,
                help="Select the DID that will hold this credential"
            )
            
            credential_type = st.selectbox(
                "Credential Type",
                ["EducationCredential", "EmploymentCredential", "IdentityCredential", "CertificationCredential"],
                help="Type of credential to issue"
            )
            
            # Dynamic credential data based on type
            credential_data = {}
            
            if credential_type == "EducationCredential":
                credential_data = {
                    "name": st.text_input("Graduate Name", "John Doe"),
                    "degree": st.text_input("Degree", "Bachelor of Science"),
                    "institution": st.text_input("Institution", "University of Technology"),
                    "graduationDate": st.date_input("Graduation Date").isoformat(),
                    "gpa": st.slider("GPA", 0.0, 4.0, 3.5)
                }
            elif credential_type == "EmploymentCredential":
                credential_data = {
                    "employeeName": st.text_input("Employee Name", "Jane Smith"),
                    "position": st.text_input("Position", "Software Engineer"),
                    "company": st.text_input("Company", "Tech Corp"),
                    "startDate": st.date_input("Start Date").isoformat(),
                    "salary": st.number_input("Annual Salary", 50000, 200000, 75000)
                }
            elif credential_type == "IdentityCredential":
                credential_data = {
                    "fullName": st.text_input("Full Name", "Alex Johnson"),
                    "dateOfBirth": st.date_input("Date of Birth").isoformat(),
                    "nationality": st.text_input("Nationality", "US"),
                    "idNumber": st.text_input("ID Number", f"ID{uuid.uuid4().hex[:8].upper()}")
                }
            else:  # CertificationCredential
                credential_data = {
                    "certificationName": st.text_input("Certification", "AWS Solutions Architect"),
                    "issuingOrganization": st.text_input("Issuing Organization", "Amazon Web Services"),
                    "certificationDate": st.date_input("Certification Date").isoformat(),
                    "expirationDate": st.date_input("Expiration Date").isoformat(),
                    "certificationId": st.text_input("Certification ID", f"CERT{uuid.uuid4().hex[:8].upper()}")
                }
            
            if st.form_submit_button("🎫 Issue Credential"):
                try:
                    result = st.session_state.client.issue_credential(holder_did, credential_data)
                    
                    credential_id = result["credential_id"]
                    st.session_state.issued_credentials.append(credential_id)
                    
                    st.success("✅ Credential issued successfully!")
                    st.json(result)
                    
                except Exception as e:
                    st.error(f"❌ Credential issuance failed: {str(e)}")
    
    with tab2:
        st.subheader("📋 Issued Credentials")
        
        if st.session_state.issued_credentials:
            for i, cred_id in enumerate(st.session_state.issued_credentials):
                with st.expander(f"Credential #{i+1}: {cred_id[:30]}..."):
                    st.code(cred_id, language="text")
                    
                    if st.button(f"✅ Verify This Credential", key=f"verify_cred_{i}"):
                        try:
                            result = st.session_state.client.verify_credential(cred_id)
                            st.json(result)
                        except Exception as e:
                            st.error(f"Verification failed: {str(e)}")
        else:
            st.info("📝 No credentials issued in this session yet. Issue one above!")

def show_verification():
    st.header("✅ Verification Service")
    st.markdown("Verify the authenticity of credentials.")
    
    if not st.session_state.access_token:
        st.warning("🔒 Please authenticate first to verify credentials")
        return
    
    tab1, tab2 = st.tabs(["🔍 Verify Credential", "📊 Verification Results"])
    
    with tab1:
        st.subheader("🔍 Verify Credential")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("verify_credential_form"):
                credential_id = st.text_input(
                    "Credential ID",
                    placeholder="cred:12345678-1234-1234-1234-123456789abc",
                    help="Enter the credential ID to verify"
                )
                
                if st.session_state.issued_credentials:
                    st.write("Or select from recently issued credentials:")
                    selected_cred = st.selectbox(
                        "Recent Credentials",
                        [""] + st.session_state.issued_credentials,
                        format_func=lambda x: f"{x[:30]}..." if x else "Select credential..."
                    )
                    if selected_cred:
                        credential_id = selected_cred
                
                if st.form_submit_button("✅ Verify Credential"):
                    if credential_id:
                        try:
                            result = st.session_state.client.verify_credential(credential_id)
                            
                            st.success("✅ Credential verification completed!")
                            
                            # Display verification result in a nice format
                            status = result.get("status", "unknown")
                            if status == "valid":
                                st.success(f"🎉 Status: {status.upper()}")
                            else:
                                st.error(f"❌ Status: {status.upper()}")
                            
                            # Show credential details
                            with st.expander("📋 Credential Details"):
                                st.json(result.get("credential_data", {}))
                            
                            with st.expander("🆔 Holder DID Information"):
                                st.write(f"**DID:** {result.get('holder_did', 'N/A')}")
                                st.json(result.get("did_document", {}))
                            
                        except Exception as e:
                            st.error(f"❌ Verification failed: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter a credential ID")
        
        with col2:
            st.info("""
            **Verification Process:**
            1. 🔍 Lookup credential in database
            2. 🆔 Verify holder DID exists  
            3. 🔐 Check credential integrity
            4. ✅ Return verification status
            
            **Verification Status:**
            - ✅ `valid`: Credential is authentic
            - ❌ `invalid`: Credential failed checks
            - ⚠️ `expired`: Credential has expired
            """)
    
    with tab2:
        st.subheader("📊 Verification Statistics")
        
        # Mock verification stats for demo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Verifications", len(st.session_state.issued_credentials))
        
        with col2:
            st.metric("Success Rate", "100%")
        
        with col3:
            st.metric("Average Response Time", "125ms")

def show_service_health():
    st.header("📊 Service Health Monitor")
    st.markdown("Monitor the health and status of all DIDentity services.")
    
    # Check all services
    services = ["auth-service", "did-service", "credential-service", "verification-service"]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🏥 Service Status")
        
        for service in services:
            with st.container():
                col_status, col_name, col_action = st.columns([1, 2, 1])
                
                with col_status:
                    # Mock health check - in real implementation would call actual health endpoints
                    st.success("🟢")
                
                with col_name:
                    st.write(f"**{service.replace('-', ' ').title()}**")
                    st.write("Status: Healthy")
                
                with col_action:
                    if st.button(f"Check", key=f"health_{service}"):
                        try:
                            # Mock health check
                            st.info(f"✅ {service} is healthy")
                        except Exception as e:
                            st.error(f"❌ {service} health check failed: {str(e)}")
                
                st.markdown("---")
    
    with col2:
        st.subheader("📈 System Metrics")
        
        # Mock metrics
        metrics = {
            "Uptime": "99.9%",
            "Response Time": "< 100ms", 
            "Active Users": "1" if st.session_state.access_token else "0",
            "Total DIDs": str(len(st.session_state.created_dids)),
            "Total Credentials": str(len(st.session_state.issued_credentials))
        }
        
        for metric, value in metrics.items():
            st.metric(metric, value)
        
        # Refresh button
        if st.button("🔄 Refresh Metrics"):
            st.rerun()

def show_api_docs():
    st.header("📖 API Documentation")
    st.markdown("Interactive API documentation and examples.")
    
    service = st.selectbox(
        "Select Service",
        ["Auth Service", "DID Service", "Credential Service", "Verification Service"]
    )
    
    if service == "Auth Service":
        st.subheader("🔐 Auth Service API")
        
        endpoints = {
            "POST /signup": {
                "description": "Register a new user",
                "example": {
                    "username": "johndoe",
                    "email": "john@example.com", 
                    "password": "securepassword"
                }
            },
            "POST /login": {
                "description": "Authenticate user and get tokens",
                "example": {
                    "username": "johndoe",
                    "password": "securepassword"
                }
            },
            "POST /token/refresh": {
                "description": "Refresh access token",
                "example": {
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                }
            }
        }
        
        for endpoint, details in endpoints.items():
            with st.expander(endpoint):
                st.write(details["description"])
                st.code(json.dumps(details["example"], indent=2), language="json")
    
    elif service == "DID Service":
        st.subheader("🆔 DID Service API")
        
        endpoints = {
            "POST /dids": {
                "description": "Create a new DID",
                "example": {
                    "method": "did:key",
                    "controller": "optional-controller-did"
                }
            },
            "GET /dids/{did}": {
                "description": "Resolve a DID to get its document",
                "example": "GET /dids/did:example:123456789abcdefghi"
            }
        }
        
        for endpoint, details in endpoints.items():
            with st.expander(endpoint):
                st.write(details["description"])
                if isinstance(details["example"], dict):
                    st.code(json.dumps(details["example"], indent=2), language="json")
                else:
                    st.code(details["example"])
    
    elif service == "Credential Service":
        st.subheader("📜 Credential Service API")
        
        endpoints = {
            "POST /credentials/issue": {
                "description": "Issue a verifiable credential",
                "example": {
                    "holder_did": "did:example:123456789abcdefghi",
                    "credential_data": {
                        "name": "John Doe",
                        "degree": "Bachelor of Science",
                        "institution": "University of Technology"
                    }
                }
            }
        }
        
        for endpoint, details in endpoints.items():
            with st.expander(endpoint):
                st.write(details["description"])
                st.code(json.dumps(details["example"], indent=2), language="json")
    
    elif service == "Verification Service":
        st.subheader("✅ Verification Service API")
        
        endpoints = {
            "POST /credentials/verify": {
                "description": "Verify a credential",
                "example": {
                    "credential_id": "cred:12345678-1234-1234-1234-123456789abc"
                }
            }
        }
        
        for endpoint, details in endpoints.items():
            with st.expander(endpoint):
                st.write(details["description"])
                st.code(json.dumps(details["example"], indent=2), language="json")
    
    # Live API testing
    st.markdown("---")
    st.subheader("🧪 Live API Testing")
    st.info("Use the interactive sections above to test the actual APIs!")

if __name__ == "__main__":
    main() 