# Vault Production Deployment Notes

This document provides guidance on transitioning from the development setup to a secure production deployment.

## Security Considerations for Production

### 1. Server Configuration

Replace the dev server mode with a proper server configuration:

```yaml
vault:
  image: hashicorp/vault:latest
  cap_add:
    - IPC_LOCK
  ports:
    - "8200:8200"
  volumes:
    - ./vault/config:/vault/config
    - vault-data:/vault/data
  command: server -config=/vault/config/vault.json
  healthcheck:
    test: ["CMD", "vault", "status"]
    interval: 10s
    timeout: 5s
    retries: 3
```

### 2. TLS Configuration

In production, enable TLS by updating the `vault.json` configuration:

```json
{
  "listener": {
    "tcp": {
      "address": "0.0.0.0:8200",
      "tls_cert_file": "/vault/certs/server.crt",
      "tls_key_file": "/vault/certs/server.key"
    }
  }
}
```

Add a volume mount for certificates:
```yaml
volumes:
  - ./certs:/vault/certs
```

### 3. Initialization and Unsealing

In production, Vault requires proper initialization and unsealing:

1. Initialize Vault:
   ```
   vault operator init
   ```
   This returns unseal keys and a root token. SECURELY STORE THESE.

2. Unseal Vault (must be done whenever Vault restarts):
   ```
   vault operator unseal <key1>
   vault operator unseal <key2>
   vault operator unseal <key3>
   ```

3. Consider using auto-unseal mechanisms like:
   - AWS KMS
   - GCP KMS
   - Azure Key Vault
   - HashiCorp Cloud Platform (HCP)

### 4. High Availability

For production, consider:
- Multiple Vault instances in HA mode
- Consul or etcd storage backend instead of file
- Load balancing
- Backup strategies

### 5. Audit Logging

Enable auditing to track all operations:

```
vault audit enable file file_path=/vault/logs/audit.log
```

Add a volume mount for logs:
```yaml
volumes:
  - ./logs:/vault/logs
```

### 6. Authentication Methods

Replace the root token with proper authentication methods:
- AppRole for service-to-service
- JWT/OIDC for user authentication
- Kubernetes auth for container environments

### 7. Secret Rotation

Implement regular rotation of:
- Database credentials
- JWT signing keys
- Any other sensitive material

### 8. Monitoring and Alerting

- Set up alerts for failed login attempts
- Monitor Vault health metrics
- Configure teleport for remote access

## Transitioning Steps

1. Create a parallel production environment
2. Initialize the production Vault
3. Migrate secrets and policies
4. Update service configurations to point to production Vault
5. Validate functionality
6. Switch over completely

## Additional Resources

- [Vault Production Hardening Guide](https://www.vaultproject.io/docs/concepts/production-hardening)
- [Vault Reference Architecture](https://www.vaultproject.io/docs/concepts/architecture)
- [Vault Security Documentation](https://www.vaultproject.io/docs/internals/security) 