from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Database metrics
db_operation_duration_seconds = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["operation"]
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache"]
)

# Event metrics
events_created_total = Counter(
    "events_created_total",
    "Total number of events created"
)

events_updated_total = Counter(
    "events_updated_total",
    "Total number of events updated"
)

active_events = Gauge(
    "active_events",
    "Number of active events"
)

def setup_metrics(app):
    """Setup Prometheus metrics for the application."""
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="fastapi_inprogress",
        inprogress_labels=True,
    )

    # Add default metrics
    instrumentator.add(metrics.default())

    # Instrument the app
    instrumentator.instrument(app).expose(app) 