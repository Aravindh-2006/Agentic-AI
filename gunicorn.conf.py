# Gunicorn configuration for Render deployment
# Using 1 worker with long timeout — free tier has 512MB RAM
# 2 workers would exceed memory limit and cause silent thread kills

workers = 1                  # 1 worker only — free tier RAM constraint
threads = 4                  # use threads instead of workers for concurrency
worker_class = "gthread"     # gthread supports both SSE and background threads
timeout = 300                # 5 minutes for all 7 agents to complete
keepalive = 5
preload_app = False
