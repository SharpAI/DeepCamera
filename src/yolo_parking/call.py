from celery import Celery
import os
cwd = os.getcwd()

redis_host = os.getenv("REDIS_HOST", default="localhost")
redis_port = os.getenv("REDIS_PORT", default="6379")

app = Celery('tasks')

app.conf.update(
    result_expires=60,
    task_acks_late=True,
    broker_url='redis://guest@'+redis_host+':'+redis_port+'/0',
    result_backend='redis://guest@'+redis_host+':'+redis_port+'/0'
)

app.send_task('upload_api-v2.detect', queue='detect', args=("frame-1-0000.jpg", 1, 1, 1))
app.send_task('upload_api-v2.detect', queue='detect', args=("frame-1-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-2-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-2-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-3-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-3-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))
# app.send_task('upload_api-v2.detect', queue='detect', args=("frame-4-0000.jpg", 1, 1, 1))



