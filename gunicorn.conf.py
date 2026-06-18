# Gunicorn configuration for Render deployment
workers = 1
threads = 4
worker_class = "gthread"
timeout = 300
keepalive = 5
preload_app = False
