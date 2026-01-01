"""
DashFleet constants and configuration defaults.
Centralized configuration to avoid hardcoded values scattered throughout codebase.
"""

# ============================================================================
# FLEET HEALTH & MONITORING THRESHOLDS
# ============================================================================

# CPU alert threshold (percentage)
CPU_ALERT = 80

# RAM alert threshold (percentage)
RAM_ALERT = 90

# Fleet entry time-to-live in seconds (how long before a machine is considered offline)
FLEET_TTL_SECONDS = 600

# Disk space alert threshold (percentage)
DISK_ALERT = 85

# ============================================================================
# RATE LIMITING
# ============================================================================

# Default rate limit for most endpoints (requests per minute)
DEFAULT_RATE_LIMIT = "100/minute"

# Rate limit for /api/fleet/report (agent metric uploads)
FLEET_REPORT_RATE_LIMIT = "30/minute"

# Rate limit for /api/action (admin actions)
ACTION_RATE_LIMIT = "10/minute"

# ============================================================================
# API RESPONSE CODES & STATUS
# ============================================================================

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

# Health score thresholds
HEALTH_SCORE_OK = 80
HEALTH_SCORE_WARN = 60

# ============================================================================
# DATABASE & PERSISTENCE
# ============================================================================

# Default database location (relative to app root)
DB_PATH = "data/fleet.db"

# Fleet state JSON backup location (relative to app root)
FLEET_STATE_JSON_PATH = "logs/fleet_state.json"

# Metrics CSV history location (relative to app root)
METRICS_CSV_PATH = "logs/metrics.csv"

# ============================================================================
# AGENT CONFIGURATION DEFAULTS
# ============================================================================

# Default interval for agent to collect and report metrics (seconds)
DEFAULT_AGENT_INTERVAL = 30

# Agent socket timeout for POST requests (seconds)
AGENT_REQUEST_TIMEOUT = 10

# ============================================================================
# FEATURE FLAGS & CONFIGURATION
# ============================================================================

# Webhook throttle minimum (seconds between webhook POSTs)
WEBHOOK_MIN_SECONDS = 300

# Download token expiration (seconds)
DOWNLOAD_TOKEN_EXPIRY = 3600  # 1 hour

# Session timeout (seconds)
SESSION_TIMEOUT = 28800  # 8 hours

# Bootstrap admin password hash rounds
BOOTSTRAP_PASSWORD_ROUNDS = 12
