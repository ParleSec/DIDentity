-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create DIDs table
CREATE TABLE IF NOT EXISTS dids (
    id SERIAL PRIMARY KEY,
    did VARCHAR(255) NOT NULL UNIQUE,
    document JSONB NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create credentials table
CREATE TABLE IF NOT EXISTS credentials (
    id SERIAL PRIMARY KEY,
    credential_id VARCHAR(255) NOT NULL UNIQUE,
    issuer VARCHAR(255) NOT NULL,
    holder VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    credential JSONB NOT NULL,
    revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create verifications table
CREATE TABLE IF NOT EXISTS verifications (
    id SERIAL PRIMARY KEY,
    verification_id VARCHAR(255) NOT NULL UNIQUE,
    credential_id VARCHAR(255) NOT NULL,
    verifier VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    verification_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Optimization: Add critical indexes
-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);

-- DIDs table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dids_did ON dids(did);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dids_user_id ON dids(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dids_created_at ON dids(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dids_document_gin ON dids USING gin(document);

-- Credentials table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_credential_id ON credentials(credential_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_issuer ON credentials(issuer);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_holder ON credentials(holder);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_type ON credentials(type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_revoked ON credentials(revoked) WHERE revoked = false;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_created_at ON credentials(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_credential_gin ON credentials USING gin(credential);

-- Verifications table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verifications_verification_id ON verifications(verification_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verifications_credential_id ON verifications(credential_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verifications_verifier ON verifications(verifier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verifications_status ON verifications(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verifications_time ON verifications(verification_time);

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credentials_holder_type_active ON credentials(holder, type) WHERE revoked = false;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verifications_credential_status ON verifications(credential_id, status); 