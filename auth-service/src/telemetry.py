import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from fastapi import Request

# Setup logging
logger = logging.getLogger(__name__)

# Initialize tracer
def init_tracer():
    """Initialize OpenTelemetry tracer."""
    # Check if OpenTelemetry is disabled (e.g., during tests)
    if os.environ.get("OTEL_SDK_DISABLED", "").lower() == "true":
        logger.info("OpenTelemetry is disabled via OTEL_SDK_DISABLED environment variable")
        return None
    
    try:
        # Service name is required for most exporters
        resource = Resource(attributes={
            SERVICE_NAME: os.environ.get("SERVICE_NAME", "auth-service")
        })
        
        # Create a TracerProvider with the resource
        provider = TracerProvider(resource=resource)
        
        # Create an OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.environ.get("OTLP_ENDPOINT", "jaeger:4317"),
            insecure=True
        )
        
        # Add exporter to the provider
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        
        # Set the provider as the global provider
        trace.set_tracer_provider(provider)
        
        logger.info(f"OpenTelemetry tracer initialized for {os.environ.get('SERVICE_NAME', 'auth-service')}")
        return provider
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracer: {str(e)}")
        return None

# Get a tracer
def get_tracer():
    """Get a tracer to use in the application."""
    return trace.get_tracer(__name__)

# Helper function to extract trace context from request
def extract_context_from_request(request: Request):
    """Extract trace context from request headers."""
    propagator = TraceContextTextMapPropagator()
    return propagator.extract(carrier=request.headers)

# Helper to create a span
def create_span(name, context=None, attributes=None):
    """Create a new span."""
    tracer = get_tracer()
    if context:
        return tracer.start_span(name, context=context, attributes=attributes)
    return tracer.start_span(name, attributes=attributes)

# Helper to add attributes to current span
def add_span_attributes(attributes):
    """Add attributes to the current span."""
    current_span = trace.get_current_span()
    for key, value in attributes.items():
        current_span.set_attribute(key, value)

# Helper to mark current span as error
def mark_span_error(exception):
    """Mark the current span as error."""
    current_span = trace.get_current_span()
    current_span.record_exception(exception)
    current_span.set_status(trace.StatusCode.ERROR)

# Initialize tracer on module import
provider = init_tracer() 