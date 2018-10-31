import subprocess, shlex, os

if __name__ == "__main__":
    command = ''
    if os.path.exists('migrate_db.py'):
        command = 'python migrate_db.py db upgrade '
    if os.path.exists('migrate_db.pyc'):
        command = 'python migrate_db.pyc db upgrade '
    if os.path.exists('migrate_db.exe'):
        command = './migrate_db.exe db upgrade '

    migrate_db = subprocess.Popen(args=shlex.split(command))
    migrate_db.wait()

    env = os.environ.copy()
    env['WORKER_BROKER'] = 'redis://redis/0'

    env['WORKER_TYPE'] = 'detect'
    command = 'celery worker --loglevel INFO -E -n detect -c 1 -Q detect'
    detect = subprocess.Popen(args=shlex.split(command), env=env)

    env['WORKER_TYPE'] = 'embedding'
    command = 'celery worker --loglevel INFO -E -n embedding -c 1 -Q embedding'
    embedding = subprocess.Popen(args=shlex.split(command), env=env)

    #env['WORKER_TYPE'] = 'flower'
    #command = 'celery flower'
    #flower = subprocess.Popen(args=shlex.split(command), env=env)

    detect.wait()
    embedding.wait()
    #flower.wait()
