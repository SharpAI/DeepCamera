# -*- mode: python -*-

block_cipher = None


a = Analysis(['../src/embedding/upload_api-v2.py'],
             pathex=['../src/embedding'],
             binaries=[],
             datas=[],
             hiddenimports=['django', 'celery', 'celery.loaders.app', 'celery.app.amqp', 'celery.fixups.django', 'celery.bin.celery', 'sklearn.neighbors.ball_tree', 'sklearn.neighbors.dist_metrics', 'sklearn.neighbors.kd_tree', 'sklearn.neighbors.quad_tree', 'sklearn.neighbors.typedefs', 'kombu.transport.redis', 'celery.backends', 'celery.apps', 'celery.apps.worker', 'celery.events', 'celery.worker', 'celery.bin', 'celery.concurrency', 'celery.contrib', 'celery.fixups', 'celery.security', 'celery.task', 'celery.utils', 'celery.backends.redis', 'celery.app.events', 'celery.app.base.log_cls', 'celery.app.control', 'celery.app.log', 'celery.app.control', 'celery.app.task', 'celery.concurrency.prefork', 'celery.concurrency.eventlet', 'celery.concurrency.gevent', 'celery.concurrency.solo', 'celery.worker.components', 'celery.worker.autoscale', 'celery.worker.consumer', 'celery.worker.state', 'celery.worker.state.task_reserved', 'celery.worker.state.maybe_shutdown', 'celery.worker.state.reserved_requests', 'celery.worker.control', 'celery.worker.loops', 'celery.worker.request', 'celery.worker.strategy', 'celery.worker.heartbeat', 'celery.worker.pidbox', 'celery.events.state'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tvm'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
a.binaries += TOC([('libtvm.so','/data/data/com.termux/files/usr/lib/libtvm.so','BINARY'),
  ('libtvm_runtime.so','/data/data/com.termux/files/usr/lib/libtvm_runtime.so','BINARY')])
exe = EXE(pyz,
          a.scripts,
	  exclude_binaries=True,
	  name='embedding',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='embedding')
