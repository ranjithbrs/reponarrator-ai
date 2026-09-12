import os

# Gunicorn configuration for SSE Streaming and GenAI workloads
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
threads = 8
worker_class = "gthread"
timeout = 300
keepalive = 65
capture_output = True
enable_stdio_inheritance = True
