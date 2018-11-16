# -*- mode: python -*-

block_cipher = None

import sys
sys.modules['FixTk'] = None

a = Analysis(['classifier_classify_new.py'],
             pathex=['/home/sharpai/src/embedding'],
             binaries=[],
             datas=[],
             hiddenimports=['packaging.version', 'packaging.specifiers', 'packaging.requirements', 'packaging.markers', 'sklearn.neighbors.ball_tree', 'sklearn.neighbors.dist_metrics', 'sklearn.neighbors.kd_tree', 'sklearn.neighbors.quad_tree', 'sklearn.neighbors.typedefs'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='classifier_classify_new',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
