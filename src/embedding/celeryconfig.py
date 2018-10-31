import os
imports = ('upload_api-v2',)

broker_url = 'redis://redis/0'
if os.environ is not None and 'WORKER_BROKER' in os.environ.keys():
    broker_url = os.environ['WORKER_BROKER']

REDIS_ADDRESS = os.getenv('REDIS_ADDRESS','redis')

result_backend = 'redis://'+REDIS_ADDRESS+'/0'
worker_pool_restarts = True

task_routes = {
    'upload_api-v2.extract': {'queue': 'embedding'}
}
