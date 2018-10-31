import os
imports = ('od',)

broker_url = 'redis://guest@localhost/0'
if os.environ is not None and 'WORKER_BROKER' in os.environ.keys():
    broker_url = os.environ['WORKER_BROKER']

result_backend = 'redis://guest@localhost/0'
worker_pool_restarts = True

task_routes = {
    'od.detect': {'queue': 'od'}
}
