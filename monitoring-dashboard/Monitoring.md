## Monitoring Dashboard

DIDentity includes a comprehensive **Monitoring Dashboard** that provides a unified interface for monitoring all services and infrastructure components. The dashboard offers real-time visibility into system health, performance metrics, and operational status.

### 🎯 Dashboard Features

#### **Unified Service Monitoring**
- **Real-time Health Checks**: Continuous monitoring of all microservices
- **Service Status Overview**: Visual indicators for service availability
- **Port and Configuration Display**: Quick access to service endpoints
- **Automatic Refresh**: 30-second auto-refresh for live monitoring

#### **Integrated Monitoring Tools**
The dashboard provides embedded access to all monitoring tools:

- **📊 Grafana Integration**: 
  - Embedded dashboards with automatic fallback handling
  - Real-time metrics visualization
  - Interactive charts and graphs
  - Multiple view modes (embedded, kiosk, full interface)

- **📈 Prometheus Integration**:
  - Metrics collection and querying interface
  - Time-series data exploration
  - PromQL query capabilities
  - Target monitoring and health status

- **🔍 Jaeger Integration**:
  - Distributed tracing visualization
  - Service dependency mapping
  - Request flow analysis
  - Performance bottleneck detection

- **🐰 RabbitMQ Integration**:
  - Queue management and monitoring
  - Message statistics and flow
  - Connection and exchange monitoring
  - Comprehensive API statistics

#### **Advanced Connection Testing**
- **Service Health Testing**: Real-time connectivity verification
- **Detailed Statistics**: Service-specific metrics and information
- **Error Diagnostics**: Comprehensive troubleshooting guidance
- **Retry Mechanisms**: Automatic and manual retry options

#### **Smart Error Handling**
- **CORS-Aware Embedding**: Intelligent iframe handling with fallbacks
- **Connection Failure Detection**: Automatic detection of embedding issues
- **Troubleshooting Guidance**: Context-specific error resolution tips
- **Alternative Access Methods**: Direct links when embedding fails

### 🚀 Accessing the Monitoring Dashboard

1. **Start the DIDentity platform**:
   ```bash
   docker-compose up -d
   ```

2. **Open the Monitoring Dashboard**:
   ```
   http://localhost:8000
   ```

3. **Navigate through the interface**:
   - **Overview**: System-wide health summary
   - **Service Status**: Individual service monitoring
   - **Grafana**: Metrics visualization and dashboards
   - **Prometheus**: Raw metrics and query interface
   - **Jaeger**: Distributed tracing and service maps
   - **RabbitMQ**: Message queue monitoring and management

### 📋 Dashboard Sections

#### **System Overview Cards**
- **Services Status**: Shows healthy vs total services ratio
- **Monitoring Tools**: Displays monitoring infrastructure health
- **System Status**: Overall platform health indicator
- **Quick Access**: Direct links to all monitoring tools

#### **Service Health Grid**
- **Real-time Status**: Live health indicators for each service
- **Port Information**: Service endpoints and configuration
- **Database Connectivity**: Database connection status
- **Performance Indicators**: Service-specific health metrics

#### **Monitoring Tools Tabs**
Each monitoring tool has a dedicated tab with:
- **Status Information**: Service health and configuration details
- **Embedded Interface**: Direct access to the tool's interface
- **Action Buttons**: Test connections, retry embedding, open externally
- **Test Results**: Detailed connectivity and performance information

### 🔧 Troubleshooting with the Dashboard

#### **Service Issues**
- Use the **Test Connection** buttons to diagnose connectivity
- Check the **Service Health Grid** for real-time status
- Review **detailed error messages** with specific troubleshooting steps
- Access **direct links** to services when embedding fails

#### **Monitoring Tool Issues**
- **Grafana**: Multiple embed URLs with automatic fallback
- **Prometheus**: Backend health checks avoid CORS issues
- **Jaeger**: Service discovery and trace analysis
- **RabbitMQ**: Comprehensive API testing with detailed statistics

#### **Common Solutions**
```bash
# Check all services status
docker-compose ps

# View specific service logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Full system restart
docker-compose down && docker-compose up -d
```

### 🎨 Dashboard Architecture

The monitoring dashboard is built with:
- **FastAPI Backend**: Robust API for health checks and service communication
- **Modern Frontend**: Responsive design with Tailwind CSS
- **Real-time Updates**: Automatic refresh and live status monitoring
- **Error Resilience**: Comprehensive error handling and recovery mechanisms

### 📊 Monitoring Data Sources

- **Service Health**: Direct HTTP health check endpoints
- **Grafana Metrics**: Custom dashboards for DIDentity services
- **Prometheus Data**: Time-series metrics collection
- **Jaeger Traces**: Distributed request tracing
- **RabbitMQ Stats**: Queue and message statistics via Management API