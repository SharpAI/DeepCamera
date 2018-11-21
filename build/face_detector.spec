# -*- mode: python -*-

block_cipher = None


a = Analysis(['../src/face_detection/worker.py'],
             pathex=['../src/face_detection'],
             binaries=[],
             datas=[],
             hiddenimports=['celery.fixups.django','django', 'celery', 'celery.loaders.app', 'celery.app.amqp', 'kombu.transport.redis', 'celery.backends', 'celery.apps', 'celery.events', 'celery.worker', 'celery.bin', 'celery.concurrency', 'celery.contrib', 'celery.fixups', 'celery.security', 'celery.task', 'celery.utils', 'celery.backends.redis', 'celery.app.events'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='worker',
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
               name='worker')
