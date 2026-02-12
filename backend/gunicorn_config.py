import multiprocessing
import os

# Bind to Render's port
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Worker configuration - optimized for 512MB RAM
workers = 1
worker_class = "sync"
threads = 2
worker_connections = 100

# Timeout settings
timeout = 120
graceful_timeout = 30
keepalive = 5

# Memory management
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
