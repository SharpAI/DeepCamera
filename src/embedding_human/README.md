## workai
```
$ python upload_api.py --port=5000
```

## deepeye
### install dependence
```
$ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

or

$ pip install -r requirements.txt
```
### Run RabbitMQ
```
docker run -d -p 4369:4369 -p 5671:5671 -p 5672:5672 -p 25672:25672 rabbitmq:3.7   (PC)

or

docker run -d -p 4369:4369 -p 5671:5671 -p 5672:5672 -p 25672:25672 arm64v8/rabbitmq:3.7 (arm64)
```
### Modify IP

https://github.com/solderzzc/DeepLearning/blob/celery/FaceRecognition/facenet/src/celeryconfig.py

### start worker
```
$ WORKER_TYPE=detect celery worker --loglevel INFO -E -n detect -c 2 -Q detect
$ WORKER_TYPE=embedding celery worker --loglevel INFO -E -n embedding -c 1 -Q embedding
```

### start flower
```
celery flower
```

### start test
```
python test.py
```
