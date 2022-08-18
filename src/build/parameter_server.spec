# -*- mode: python -*-

block_cipher = None


a = Analysis(['../src/embedding/parameter_server.py'],
             pathex=['../src/embedding'],
             binaries=[],
             datas=[],
             hiddenimports=['email', 'email.message', 'email.mime.message', 'email.mime.image', 'email.mime.text', 'email.mime.audio', 'email.mime.base', 'email.mime.multipart', 'email.mime.nonmultipart'],
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
          name='param',
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
               name='param')
