# -*- mode: python -*-

block_cipher = None


a = Analysis(['../src/embedding/upload_api-v2.py'],
             pathex=['../src/embedding'],
             binaries=[],
             datas=[('/usr/local/lib/libmxnet.so', 'mxnet')],
             hiddenimports=['django', 'celery', 'celery.loaders.app', 'celery.app.amqp', 'celery.fixups.django', 'celery.bin.celery', 'sklearn.neighbors.ball_tree', 'sklearn.neighbors.dist_metrics', 'sklearn.neighbors.kd_tree', 'sklearn.neighbors.quad_tree', 'sklearn.neighbors.typedefs', 'kombu.transport.redis', 'celery.backends', 'celery.apps', 'celery.apps.worker', 'celery.events', 'celery.worker', 'celery.bin', 'celery.concurrency', 'celery.contrib', 'celery.fixups', 'celery.security', 'celery.task', 'celery.utils', 'celery.backends.redis', 'celery.app.events', 'celery.app.base.log_cls', 'celery.app.control', 'celery.app.log', 'celery.app.control', 'celery.app.task', 'celery.concurrency.prefork', 'celery.concurrency.eventlet', 'celery.concurrency.gevent', 'celery.concurrency.solo', 'celery.worker.components', 'celery.worker.autoscale', 'celery.worker.consumer', 'celery.worker.state', 'celery.worker.state.task_reserved', 'celery.worker.state.maybe_shutdown', 'celery.worker.state.reserved_requests', 'celery.worker.control', 'celery.worker.loops', 'celery.worker.request', 'celery.worker.strategy', 'celery.worker.heartbeat', 'celery.worker.pidbox', 'celery.events.state','mxnet',
             'mxnet.model.load_checkpoint','mxnet.cpu','mxnet.nd.array'],
             hookspath=['./hooks/'],
             runtime_hooks=[],
             excludes=[],
             #excludes=['tvm'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
#a.binaries += TOC([('libGLES_mali.so','/system/vendor/lib/egl/libGLES_mali.so','BINARY')])
#a.binaries += TOC([('libmxnet.so','/usr/local/lib/libmxnet.so','BINARY')])
#a.datas += TOC([('/usr/local/lib/libmxnet.so', 'mxnet')])
exe = EXE(pyz,
          a.scripts,
	        exclude_binaries=True,
	        name='embedding',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='embedding')
