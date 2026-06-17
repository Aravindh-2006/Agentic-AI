# Gunicorn configuration for Render deployment
# Agents take ~20-30s, SSE streams are long-lived — needs generous timeouts

workers = 2                  # 2 workers so SSE + agent pipeline don't share one worker
worker_class = "sync"        # sync is fine for Flask
timeout = 300                # 5 minutes — enough for all 7 agents to complete
keepalive = 5
max_requests = 100           # restart workers after 100 requests to prevent memory leaks
max_requests_jitter = 20
preload_app = False          # don't preload — avoids SQLite issues across forked workers
