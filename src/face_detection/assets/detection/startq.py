import subprocess, shlex, os

if __name__ == "__main__":
    command = ''

    env = os.environ.copy()
    env['WORKER_BROKER'] = 'amqp://rabbitmq/'

    env['WORKER_TYPE'] = 'od'
    command = 'celery worker --loglevel INFO -E -n od -c 1 --autoscale=1,1 -Q od'
    od = subprocess.Popen(args=shlex.split(command), env=env)

    env['WORKER_TYPE'] = 'flower'
    command = 'celery flower'
    flower = subprocess.Popen(args=shlex.split(command), env=env)

    od.wait()
    flower.wait()
