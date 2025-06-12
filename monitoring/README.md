# DID Identity Services Monitoring

This directory contains the monitoring infrastructure for the DID (Decentralized Identity) services, including Grafana dashboards, Prometheus configuration, and alerting rules aligned with security monitoring best practices.

## Overview

The monitoring stack provides comprehensive observability for:
- **Security Metrics**: Authentication failures, suspicious activities, rate limiting violations
- **Service Health**: Uptime, response times, resource usage, error rates
- **API Usage Analytics**: Endpoint usage patterns, user behavior, DID operations
- **Compliance Monitoring**: Audit trails, data retention, unauthorized access attempts

## Dashboards

### 1. DID Security Metrics (`security-metrics.json`)
**Purpose**: Monitor security-related events and potential threats

**Key Panels**:
- Authentication Failures Rate
- Rate Limit Violations  
- DID Verification Failures
- Suspicious Activity Detection
- JWT Token Validation Failures
- Credential Issuance Activity
- Security Events Timeline

**Use Cases**:
- Detect brute force attacks
- Monitor for credential stuffing
- Track DID verification anomalies
- Identify suspicious user behavior patterns

### 2. Service Health & SLI/SLO (`service-health.json`)
**Purpose**: Track service availability, performance, and resource usage

**Key Panels**:
- Service Availability (SLI)
- 95th Percentile Response Time
- Memory & CPU Usage
- Service Uptime by Service
- Response Time Percentiles (50th, 95th, 99th)
- Service Success Rate

**SLI/SLO Targets**:
- Availability: 99.9% uptime
- Response Time: 95th percentile < 200ms
- Success Rate: >99.5% (non-5xx responses)
- CPU Usage: <80% average
- Memory Usage: <85% of allocated

### 3. API Usage & Analytics (`api-usage-analytics.json`)
**Purpose**: Understand API usage patterns and user behavior

**Key Panels**:
- Total Request Rate
- Active Users Count
- DID Operations Rate
- Credential Operations Rate
- API Endpoint Usage
- HTTP Status Code Distribution
- Top User Agents
- Verification Methods Usage
- Request Heatmap - Usage Patterns

**Business Insights**:
- Peak usage times
- Most popular endpoints
- User agent analysis
- Geographic usage patterns
- DID operation trends

### 4. DID Services Overview (`services.json`)
**Purpose**: High-level overview of all services with navigation links

**Key Panels**:
- HTTP Request Rate by Service
- HTTP Response Time Percentiles
- Service Status Overview (Table)
- HTTP Status Codes by Service
- Memory Usage by Service
- CPU Usage by Service

## Metrics Categories

### Core HTTP Metrics
```promql
# Request rate
rate(http_requests_total[5m])

# Response time percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m])
```

### Security Metrics
```promql
# Authentication failures
rate(auth_failures_total[5m])

# Rate limiting violations
rate(rate_limit_exceeded_total[5m])

# DID verification failures
rate(did_verification_failures_total[5m])

# Security events
rate(security_events_total[5m])
```

### DID-Specific Metrics
```promql
# DID operations
rate(did_operations_total[5m])

# Credential operations
rate(credential_operations_total[5m])

# Verification operations
rate(verification_operations_total[5m])
```

### Infrastructure Metrics
```promql
# Service uptime
up{job=~".*-service"}

# Memory usage
process_resident_memory_bytes

# CPU usage
rate(process_cpu_seconds_total[5m])
```

## Alert Rules

### Critical Alerts
- **ServiceDown**: Service unavailable for >1 minute
- **AuthenticationFailureSpike**: >5 auth failures/sec
- **VaultUnavailable**: Vault service down
- **UnauthorizedDataAccess**: Any unauthorized access attempt

### Warning Alerts
- **HighResponseTime**: 95th percentile >500ms
- **HighErrorRate**: >5% error rate
- **HighMemoryUsage**: >1GB memory usage
- **HighCPUUsage**: >80% CPU usage
- **SuspiciousActivity**: Suspicious events detected
- **RateLimitExceeded**: >10 violations/sec
- **JWTValidationFailures**: >2 failures/sec
- **DIDVerificationFailures**: >1 failure/sec

## Configuration Files

### Prometheus Configuration (`prometheus.yml`)
- Scrapes all DID services every 15 seconds
- Includes node-exporter and cAdvisor for infrastructure metrics
- Vault metrics collection with authentication
- Alert manager integration

### Grafana Provisioning
- **Datasources**: Prometheus and Jaeger configuration
- **Dashboards**: Automatic dashboard provisioning
- **Alerts**: Dashboard-based alerting rules

## Best Practices

### Security Monitoring
1. **Monitor authentication patterns** - Track failed login attempts, unusual access patterns
2. **Rate limiting effectiveness** - Ensure rate limits are properly configured and enforced
3. **DID verification integrity** - Monitor for verification failures that could indicate attacks
4. **Audit trail completeness** - Ensure all critical operations are logged and monitored

### Performance Monitoring  
1. **SLI/SLO tracking** - Define and monitor service level indicators
2. **Resource utilization** - Prevent resource exhaustion
3. **Response time monitoring** - Track latency across percentiles
4. **Error rate monitoring** - Distinguish between client and server errors

### Operational Monitoring
1. **Service dependencies** - Monitor Vault, databases, external services
2. **Data integrity** - Monitor for data corruption or inconsistencies
3. **Compliance tracking** - Ensure regulatory requirements are met
4. **Capacity planning** - Use trends for infrastructure scaling decisions

## Alerting Strategy

### Severity Levels
- **Critical**: Immediate action required (service down, security breach)
- **Warning**: Investigation needed within business hours
- **Informational**: Awareness only, no immediate action required

### Alert Routing
```yaml
# Example alert manager configuration
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      alert_type: security
    receiver: 'security-team'
```

## Troubleshooting

### Common Issues
1. **Missing metrics**: Check service `/metrics` endpoints
2. **High memory usage**: Review query complexity and retention policies
3. **Slow dashboard loading**: Optimize queries and time ranges
4. **False positive alerts**: Adjust thresholds based on baseline behavior

### Debugging Queries
```promql
# Check if services are being scraped
up{job=~".*-service"}

# Verify metric availability
{__name__=~"http_.*"}

# Check for high cardinality metrics
topk(10, count by (__name__)({__name__=~".+"}))
```
