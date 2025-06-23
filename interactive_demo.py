import requests
import json
import time
import uuid
import random
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
import signal
import sys
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IdentityAPI:
    def __init__(self):
        self.base_urls = {
            "auth": "http://localhost:8004",
            "did": "http://localhost:8001",
            "credential": "http://localhost:8002",
            "verification": "http://localhost:8003"
        }
        self.token = None
        self.did = None
        self.credential_id = None

    def _handle_request(self, method: str, url: str, **kwargs) -> Dict:
        """Generic request handler with retries and error handling"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    def register_user(self, username: str, email: str, password: str) -> str:
        """Register a new user and get access token"""
        logger.info("1. Registering new user...")
        
        result = self._handle_request(
            "POST",
            f"{self.base_urls['auth']}/signup",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        self.token = result["access_token"]
        logger.info("✓ User registration successful")
        return self.token

    def create_did(self, method: str = "key", identifier: str = None) -> str:
        """Create a DID for the registered user"""
        logger.info("2. Creating DID...")
        
        # The DID service only supports the 'key' method properly
        # Force method to 'key' to ensure compatibility
        method = "key"
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # For key method, the identifier needs to be in valid Base58 format
        if not identifier:
            base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            identifier = ''.join(random.choice(base58_chars) for _ in range(16))
        
        request_data = {
            "method": method,
            "identifier": identifier
        }
        
        logger.info(f"Creating DID with params: {request_data}")
        
        result = self._handle_request(
            "POST",
            f"{self.base_urls['did']}/dids",
            headers=headers,
            json=request_data
        )
        self.did = result["id"]
        logger.info(f"✓ DID created: {self.did}")
        return self.did

    def issue_credential(self, credential_data: Dict) -> str:
        """Issue a verifiable credential"""
        logger.info("3. Issuing credential...")
        
        result = self._handle_request(
            "POST",
            f"{self.base_urls['credential']}/credentials/issue",
            json={
                "holder_did": self.did,
                "credential_data": credential_data
            }
        )
        self.credential_id = result["credential_id"]
        logger.info(f"✓ Credential issued: {self.credential_id}")
        return self.credential_id

    def verify_credential(self) -> Dict:
        """Verify the issued credential"""
        logger.info("4. Verifying credential...")
        
        result = self._handle_request(
            "POST",
            f"{self.base_urls['verification']}/credentials/verify",
            json={
                "credential_id": self.credential_id
            }
        )
        logger.info("✓ Credential verification successful")
        return result

class DIDentityDemoApp:
    def __init__(self, root):
        self.root = root
        self.api = IdentityAPI()
        self.setup_ui()
        
        # Set up proper window close handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure random password that meets validation requirements"""
        import string
        
        # Ensure we have at least one character from each required category
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        special = random.choice("!@#$%^&*(),.?\":{}|<>")
        
        # Generate remaining characters from all allowed categories
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*(),.?\":{}|<>"
        remaining_length = length - 4  # We already have 4 required characters
        
        remaining_chars = ''.join(random.choice(all_chars) for _ in range(remaining_length))
        
        # Combine all characters and shuffle them
        password_chars = list(uppercase + lowercase + digit + special + remaining_chars)
        random.shuffle(password_chars)
        
        # Join to create final password
        password = ''.join(password_chars)
        
        # Verify it doesn't contain common weak patterns
        weak_patterns = ['123456', 'password', 'qwerty', 'abc123', '111111']
        password_lower = password.lower()
        
        # If it contains weak patterns, regenerate (recursive call)
        if any(pattern in password_lower for pattern in weak_patterns):
            return self.generate_secure_password(length)
            
        return password
    
    def regenerate_password(self):
        """Regenerate a new secure password"""
        new_password = self.generate_secure_password()
        self.password_var.set(new_password)
        logger.info("New secure password generated")
        
    def on_closing(self):
        """Handle window close event properly"""
        logger.info("Closing application...")
        self.root.destroy()
        
    def setup_ui(self):
        self.root.title("DIDentity Interactive Demo")
        self.root.geometry("800x700")
        self.root.minsize(800, 700)
        
        # Create style
        style = ttk.Style()
        style.theme_use("clam")  # Use 'clam', 'alt', 'default', 'classic' themes
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
        style.configure("Success.TButton", foreground="green", font=("Arial", 10, "bold"))
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))
        style.configure("Bold.TLabel", font=("Arial", 10, "bold"))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="DIDentity System Demo", 
            font=("Arial", 18, "bold"), 
            anchor="center"
        )
        title_label.pack(fill=tk.X, pady=(0, 20))
        
        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # === Step 1: User Registration ===
        self.reg_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.reg_frame, text="1. User Registration")
        
        ttk.Label(
            self.reg_frame, 
            text="Register a New User", 
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 15))
        
        # User registration form
        form_frame = ttk.Frame(self.reg_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_var = tk.StringVar(value=f"User{str(uuid.uuid4())[:5]}")
        ttk.Entry(form_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar(value=f"user_{str(uuid.uuid4())[:5]}@example.com")
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar(value=self.generate_secure_password())
        password_entry = ttk.Entry(form_frame, textvariable=self.password_var, width=30, show="*")
        password_entry.grid(row=2, column=1, sticky="w", padx=5)
        
        # Add a button to regenerate password
        ttk.Button(form_frame, text="🔄", command=self.regenerate_password, width=3).grid(row=2, column=2, padx=5)
        
        # Register button
        self.register_button = ttk.Button(form_frame, text="Register User", command=self.handle_registration)
        self.register_button.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Result frame
        result_frame = ttk.LabelFrame(self.reg_frame, text="Registration Result")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        self.reg_result_text = scrolledtext.ScrolledText(result_frame, height=10)
        self.reg_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === Step 2: DID Creation ===
        self.did_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.did_frame, text="2. DID Creation")
        
        ttk.Label(
            self.did_frame, 
            text="Create Decentralized Identifier (DID)", 
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 15))
        
        # DID creation form
        did_form_frame = ttk.Frame(self.did_frame)
        did_form_frame.pack(fill=tk.X)
        
        ttk.Label(did_form_frame, text="DID Method:").grid(row=0, column=0, sticky="w", pady=5)
        self.did_method_var = tk.StringVar(value="key")
        method_combo = ttk.Combobox(
            did_form_frame, 
            textvariable=self.did_method_var, 
            values=["key"], 
            state="readonly",
            width=10
        )
        method_combo.grid(row=0, column=1, sticky="w", padx=5)
        
        self.did_identifier_label = ttk.Label(did_form_frame, text="Identifier (optional):")
        self.did_identifier_label.grid(row=1, column=0, sticky="w", pady=5)
        self.did_identifier_var = tk.StringVar()
        self.did_identifier_entry = ttk.Entry(did_form_frame, textvariable=self.did_identifier_var, width=30)
        self.did_identifier_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        # Create DID button
        self.create_did_button = ttk.Button(
            did_form_frame, 
            text="Create DID", 
            command=self.handle_did_creation,
            state="disabled"
        )
        self.create_did_button.grid(row=2, column=0, columnspan=2, pady=15)
        
        # DID visualization and result
        did_viz_frame = ttk.Frame(self.did_frame)
        did_viz_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left: DID visualization
        did_visual_frame = ttk.LabelFrame(did_viz_frame, text="DID Visualization")
        did_visual_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.did_canvas_frame = ttk.Frame(did_visual_frame)
        self.did_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right: DID result
        did_result_frame = ttk.LabelFrame(did_viz_frame, text="DID Details")
        did_result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.did_result_text = scrolledtext.ScrolledText(did_result_frame, height=10)
        self.did_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === Step 3: Credential Issuance ===
        self.cred_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.cred_frame, text="3. Credential Issuance")
        
        ttk.Label(
            self.cred_frame, 
            text="Issue Verifiable Credentials", 
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 15))
        
        # Credential type selector
        cred_type_frame = ttk.Frame(self.cred_frame)
        cred_type_frame.pack(fill=tk.X)
        
        ttk.Label(cred_type_frame, text="Credential Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.cred_type_var = tk.StringVar(value="Academic Degree")
        cred_type_combo = ttk.Combobox(
            cred_type_frame, 
            textvariable=self.cred_type_var, 
            values=["Academic Degree", "Professional License", "Identity Card"], 
            state="readonly",
            width=20
        )
        cred_type_combo.grid(row=0, column=1, sticky="w", padx=5)
        cred_type_combo.bind("<<ComboboxSelected>>", self.update_credential_form)
        
        # Dynamic credential form
        self.cred_form_frame = ttk.LabelFrame(self.cred_frame, text="Credential Data")
        self.cred_form_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Initial form (Academic Degree)
        self.credential_fields = {}
        self.update_credential_form()
        
        # Issue button
        self.issue_button = ttk.Button(
            self.cred_frame, 
            text="Issue Credential", 
            command=self.handle_credential_issuance,
            state="disabled"
        )
        self.issue_button.pack(pady=15)
        
        # Credential result
        cred_result_frame = ttk.LabelFrame(self.cred_frame, text="Issued Credential")
        cred_result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        self.cred_result_text = scrolledtext.ScrolledText(cred_result_frame, height=10)
        self.cred_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === Step 4: Verification ===
        self.verify_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.verify_frame, text="4. Verification")
        
        ttk.Label(
            self.verify_frame, 
            text="Verify Credentials", 
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 15))
        
        # Verification controls
        verify_control_frame = ttk.Frame(self.verify_frame)
        verify_control_frame.pack(fill=tk.X)
        
        self.verify_button = ttk.Button(
            verify_control_frame, 
            text="Verify Credential", 
            command=self.handle_verification,
            state="disabled"
        )
        self.verify_button.pack(pady=10)
        
        # Verification visualization
        verify_viz_frame = ttk.Frame(self.verify_frame)
        verify_viz_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left: Verification animation/visualization
        verify_visual_frame = ttk.LabelFrame(verify_viz_frame, text="Verification Process")
        verify_visual_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.verify_canvas_frame = ttk.Frame(verify_visual_frame)
        self.verify_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right: Verification result
        verify_result_frame = ttk.LabelFrame(verify_viz_frame, text="Verification Result")
        verify_result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.verify_result_text = scrolledtext.ScrolledText(verify_result_frame, height=10)
        self.verify_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bottom status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready to start. Begin with Step 1: User Registration")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # Help button
        help_button = ttk.Button(status_frame, text="Help", command=self.show_help)
        help_button.pack(side=tk.RIGHT)
        
    def update_credential_form(self, event=None):
        # Clear existing form
        for widget in self.cred_form_frame.winfo_children():
            widget.destroy()
        
        self.credential_fields = {}
        form_frame = ttk.Frame(self.cred_form_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        cred_type = self.cred_type_var.get()
        if cred_type == "Academic Degree":
            fields = [
                ("name", "Full Name:", "Walter White"),
                ("degree", "Degree:", "Bachelor of Chemistry"),
                ("university", "University:", "Albert University"),
                ("graduationYear", "Graduation Year:", "1994"),
                ("honors", "Honors:", "Cum Laude")
            ]
        elif cred_type == "Professional License":
            fields = [
                ("name", "Full Name:", "Walter White"),
                ("license_type", "License Type:", "Teaching"),
                ("license_number", "License Number:", "LIC-12345"),
                ("issuing_authority", "Issuing Authority:", "State Board"),
                ("valid_until", "Valid Until:", "2025-12-31")
            ]
        elif cred_type == "Identity Card":
            fields = [
                ("name", "Full Name:", "Walter White"),
                ("dob", "Date of Birth:", "1960-09-07"),
                ("nationality", "Nationality:", "American"),
                ("id_number", "ID Number:", "ID-98765"),
                ("address", "Address:", "308 Negra Arroyo Lane, Albuquerque")
            ]
        
        # Create form fields
        for i, (field_id, label, default) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=default)
            self.credential_fields[field_id] = var
            ttk.Entry(form_frame, textvariable=var, width=30).grid(row=i, column=1, sticky="w", padx=5)
    
    def handle_registration(self):
        try:
            self.status_var.set("Registering user...")
            self.root.update_idletasks()
            
            username = self.username_var.get()
            email = self.email_var.get()
            password = self.password_var.get()
            
            # Call API to register user
            token = self.api.register_user(username, email, password)
            
            # Update UI
            self.reg_result_text.delete(1.0, tk.END)
            self.reg_result_text.insert(tk.END, f"✓ Registration successful!\n\n")
            self.reg_result_text.insert(tk.END, f"Username: {username}\n")
            self.reg_result_text.insert(tk.END, f"Email: {email}\n")
            self.reg_result_text.insert(tk.END, f"Token: {token[:15]}...\n")
            
            # Enable next step
            self.create_did_button.config(state="normal")
            self.notebook.select(1)  # Move to DID tab
            self.status_var.set("User registered successfully. Now create a DID.")
            
        except Exception as e:
            self.reg_result_text.delete(1.0, tk.END)
            self.reg_result_text.insert(tk.END, f"❌ Registration failed:\n{str(e)}")
            self.status_var.set("Registration failed. Please try again.")
    
    def handle_did_creation(self):
        try:
            self.status_var.set("Creating DID...")
            self.root.update_idletasks()
            
            method = self.did_method_var.get()
            identifier = self.did_identifier_var.get() or None
            
            # Call API to create DID
            did = self.api.create_did(method, identifier)
            
            # Update UI
            self.did_result_text.delete(1.0, tk.END)
            self.did_result_text.insert(tk.END, f"✓ DID created successfully!\n\n")
            self.did_result_text.insert(tk.END, f"DID: {did}\n")
            self.did_result_text.insert(tk.END, f"Method: {method}\n")
            if method == "key" and identifier:
                self.did_result_text.insert(tk.END, f"Identifier: {identifier}\n")
            elif method == "web":
                domain = identifier or "example.com"
                self.did_result_text.insert(tk.END, f"Domain: {domain}\n")
                self.did_result_text.insert(tk.END, f"Path: identity\n")
            
            # Create DID visualization
            self.create_did_visualization(did, method)
            
            # Enable next step
            self.issue_button.config(state="normal")
            self.notebook.select(2)  # Move to Credential tab
            self.status_var.set("DID created successfully. Now issue a credential.")
            
        except Exception as e:
            self.did_result_text.delete(1.0, tk.END)
            self.did_result_text.insert(tk.END, f"❌ DID creation failed:\n{str(e)}")
            self.status_var.set("DID creation failed. Please try again.")
    
    def create_did_visualization(self, did, method):
        # Clear previous visualization
        for widget in self.did_canvas_frame.winfo_children():
            widget.destroy()
            
        # Create figure
        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor('#f0f0f0')
        
        # Draw DID structure
        parts = did.split(":")
        method_color = {"key": "green", "web": "blue", "ion": "purple"}
        color = method_color.get(method, "gray")
        
        ax.text(0.5, 0.8, "DID", fontsize=16, ha='center', weight='bold')
        ax.text(0.5, 0.7, f"did:{method}:{parts[2][:6]}...", fontsize=12, ha='center')
        
        # Draw boxes
        ax.add_patch(plt.Rectangle((0.1, 0.6), 0.8, 0.3, fill=False, edgecolor=color))
        
        # Draw key components
        ax.text(0.2, 0.45, "Public Key", fontsize=10, ha='center')
        ax.text(0.5, 0.45, "Verification Method", fontsize=10, ha='center')
        ax.text(0.8, 0.45, "DID Document", fontsize=10, ha='center')
        
        ax.add_patch(plt.Rectangle((0.1, 0.35), 0.2, 0.15, fill=True, alpha=0.2, edgecolor=color, facecolor=color))
        ax.add_patch(plt.Rectangle((0.4, 0.35), 0.2, 0.15, fill=True, alpha=0.2, edgecolor=color, facecolor=color))
        ax.add_patch(plt.Rectangle((0.7, 0.35), 0.2, 0.15, fill=True, alpha=0.2, edgecolor=color, facecolor=color))
        
        # Connect the boxes
        ax.plot([0.2, 0.5], [0.35, 0.35], 'k-', alpha=0.5)
        ax.plot([0.5, 0.8], [0.35, 0.35], 'k-', alpha=0.5)
        ax.plot([0.5, 0.5], [0.5, 0.35], 'k-', alpha=0.5)
        
        ax.axis('off')
        
        # Add canvas to the frame
        canvas = FigureCanvasTkAgg(fig, master=self.did_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def handle_credential_issuance(self):
        try:
            self.status_var.set("Issuing credential...")
            self.root.update_idletasks()
            
            # Get credential data from form
            credential_data = {key: var.get() for key, var in self.credential_fields.items()}
            
            # Add credential type
            credential_data["type"] = self.cred_type_var.get()
            
            # Call API to issue credential
            credential_id = self.api.issue_credential(credential_data)
            
            # Update UI
            self.cred_result_text.delete(1.0, tk.END)
            self.cred_result_text.insert(tk.END, f"✓ Credential issued successfully!\n\n")
            self.cred_result_text.insert(tk.END, f"Credential ID: {credential_id}\n")
            self.cred_result_text.insert(tk.END, f"Type: {credential_data['type']}\n")
            self.cred_result_text.insert(tk.END, f"Holder: {credential_data['name']}\n\n")
            self.cred_result_text.insert(tk.END, "Credential Data:\n")
            for key, value in credential_data.items():
                if key != 'name' and key != 'type':
                    self.cred_result_text.insert(tk.END, f"  {key}: {value}\n")
            
            # Enable next step
            self.verify_button.config(state="normal")
            self.notebook.select(3)  # Move to Verification tab
            self.status_var.set("Credential issued successfully. Now verify the credential.")
            
            # Create credential visualization in the verification tab
            self.create_credential_visualization()
            
        except Exception as e:
            self.cred_result_text.delete(1.0, tk.END)
            self.cred_result_text.insert(tk.END, f"❌ Credential issuance failed:\n{str(e)}")
            self.status_var.set("Credential issuance failed. Please try again.")
    
    def create_credential_visualization(self):
        # Clear previous visualization
        for widget in self.verify_canvas_frame.winfo_children():
            widget.destroy()
            
        # Create a credential card visualization
        cred_frame = ttk.Frame(self.verify_canvas_frame)
        cred_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Card header
        header_frame = ttk.Frame(cred_frame, style="Card.TFrame")
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        cred_type = self.cred_type_var.get()
        ttk.Label(
            header_frame, 
            text=cred_type, 
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Card body
        body_frame = ttk.Frame(cred_frame)
        body_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Display credential data
        row = 0
        for key, var in self.credential_fields.items():
            # Format the label
            label_text = " ".join(word.capitalize() for word in key.split("_"))
            ttk.Label(
                body_frame, 
                text=f"{label_text}:", 
                font=("Arial", 10, "bold")
            ).grid(row=row, column=0, sticky="w", padx=10, pady=3)
            
            ttk.Label(
                body_frame, 
                text=var.get(),
                font=("Arial", 10)
            ).grid(row=row, column=1, sticky="w", padx=10, pady=3)
            
            row += 1
        
        # Add verification status indicator (to be updated later)
        self.verify_status_var = tk.StringVar(value="Not Verified")
        status_frame = ttk.Frame(cred_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            status_frame, 
            text="Status: ", 
            font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        self.verify_status_label = ttk.Label(
            status_frame, 
            textvariable=self.verify_status_var,
            foreground="orange",
            font=("Arial", 11, "bold")
        )
        self.verify_status_label.pack(side=tk.LEFT)
    
    def handle_verification(self):
        try:
            self.status_var.set("Verifying credential...")
            self.root.update_idletasks()
            
            # Call API to verify credential
            result = self.api.verify_credential()
            
            # Update UI
            self.verify_result_text.delete(1.0, tk.END)
            self.verify_result_text.insert(tk.END, f"✓ Verification completed!\n\n")
            
            # Log the raw result for debugging
            logger.info(f"Verification result: {result}")
            
            # Check for validity in multiple ways:
            # 1. Look for 'valid' field (boolean)
            # 2. Look for 'status' field with value 'valid'
            # 3. Fall back to successful API call meaning valid credential
            is_valid = False
            
            if 'valid' in result:
                # Format 1: {"valid": true/false}
                is_valid = result['valid']
            elif 'status' in result and result['status'] == 'valid':
                # Format 2: {"status": "valid"}
                is_valid = True
            elif not result.get('errors') and not result.get('error'):
                # No explicit validation field but no errors either
                # Trust that a successful verification call means the credential is valid
                is_valid = True
            
            self.verify_result_text.insert(tk.END, f"Valid: {is_valid}\n")
            
            # Display additional verification details if available
            if "checks" in result:
                self.verify_result_text.insert(tk.END, "\nChecks performed:\n")
                for check, status in result["checks"].items():
                    self.verify_result_text.insert(tk.END, f"  {check}: {status}\n")
            
            # Display credential data if available
            if "credential_data" in result:
                self.verify_result_text.insert(tk.END, "\nVerified Credential Data:\n")
                for key, value in result["credential_data"].items():
                    if isinstance(value, str) and key not in ['did_document']: 
                        self.verify_result_text.insert(tk.END, f"  {key}: {value}\n")
            
            # Update status indicator in the credential visualization
            if is_valid:
                self.verify_status_var.set("Verified")
                self.verify_status_label.config(foreground="green")
            else:
                self.verify_status_var.set("Invalid")
                self.verify_status_label.config(foreground="red")
            
            self.status_var.set(f"Credential verification {'successful' if is_valid else 'failed'}.")
            messagebox.showinfo("Verification Complete", 
                               f"The credential has been {'successfully verified' if is_valid else 'found invalid'}.")
            
        except Exception as e:
            self.verify_result_text.delete(1.0, tk.END)
            self.verify_result_text.insert(tk.END, f"❌ Verification failed:\n{str(e)}")
            self.status_var.set("Verification failed. Please try again.")
    
    def show_help(self):
        help_text = """
DIDentity Demo Application

This interactive demo walks you through the core functions of the DIDentity system:

1. User Registration: Create a new user account
2. DID Creation: Generate a Decentralized Identifier for the user
3. Credential Issuance: Issue verifiable credentials to the DID
4. Verification: Verify the authenticity of the credentials

Each tab guides you through one step of the process.
        """
        messagebox.showinfo("DIDentity Demo Help", help_text)
        
    def run_complete_demo(self):
        """Run the complete demo flow automatically"""
        try:
            # Step 1: Register User
            self.handle_registration()
            
            # Step 2: Create DID
            self.root.after(1000, lambda: self._safe_step_execution(self.handle_did_creation))
            
            # Step 3: Issue Credential
            self.root.after(2000, lambda: self._safe_step_execution(self.handle_credential_issuance))
            
            # Step 4: Verify Credential
            self.root.after(3000, lambda: self._safe_step_execution(self.handle_verification))
            
            # Exit after demo completes (when using --auto flag)
            if len(sys.argv) > 1 and sys.argv[1] == "--auto":
                self.root.after(5000, self.exit_application)
            
        except Exception as e:
            messagebox.showerror("Demo Failed", f"The demo failed to run: {str(e)}")
            
    def exit_application(self):
        """Exit the application cleanly"""
        logger.info("Auto-demo completed. Exiting application...")
        self.root.quit()
        self.root.destroy()
            
    def _safe_step_execution(self, step_function):
        """Execute a demo step safely with error handling"""
        try:
            step_function()
        except Exception as e:
            logger.error(f"Step execution failed: {str(e)}")
            messagebox.showerror("Step Failed", f"This step failed to complete: {str(e)}")
            # Don't propagate the exception to allow other steps to continue if possible

    def update_did_form(self, event=None):
        """Update DID form based on selected method"""
        # This method is no longer used since we only support the key method
        pass

def main():
    try:
        # Set up signal handlers for graceful termination
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            if 'root' in locals() and root.winfo_exists():
                root.destroy()
            sys.exit(0)
            
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
        if sys.platform != 'win32':  # SIGTERM not available on Windows
            signal.signal(signal.SIGTERM, signal_handler)  # Handle termination
            
        root = tk.Tk()
        app = DIDentityDemoApp(root)
        
        # Check if we should run the automated demo
        if len(sys.argv) > 1 and sys.argv[1] == "--auto":
            root.after(500, app.run_complete_demo)
        
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
    finally:
        logger.info("Exiting application")
        # Ensure Tkinter is properly shutdown if still running
        try:
            if 'root' in locals() and root.winfo_exists():
                root.destroy()
        except:
            pass
        
if __name__ == "__main__":
    main() 