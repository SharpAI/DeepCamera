# -*- mode: python -*-

block_cipher = None


a = Analysis(['../src/embedding/classifier_rest_server.py'],
             pathex=['../src/embedding'],
             binaries=[],
             datas=[],
             hiddenimports=['sklearn.neighbors.dist_metrics', 'sklearn.neighbors.kd_tree',
                'sklearn.neighbors.ball_tree', 'sklearn.neighbors.dist_metrics',
                'sklearn.neighbors.quad_tree', 'sklearn.neighbors.typedefs', 'email',
                'email.message', 'email.mime.message', 'email.mime.image', 'email.mime.text',
                'email.mime.audio', 'email.mime.base', 'email.mime.multipart', 'email.mime.nonmultipart',
                'packaging.version', 'packaging.specifiers', 'packaging.requirements', 'packaging.markers'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
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
          name='classifier',
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
               name='classifier')
