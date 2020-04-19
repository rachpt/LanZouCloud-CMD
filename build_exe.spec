# -*- mode: python ; coding: utf-8 -*-

# 本文件用于打包 Windows 程序
# 建议在虚拟环境下打包
# pyinstaller --clean -F build_exe.spec

block_cipher = None


a = Analysis(['lanzou_cmd.py'],
             pathex=['.'],
             binaries=[],
             datas=[('user.dat','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PyInstaller', 'pip', 'setuptools', 'altgraph','future','pefile', 'pywin32-ctypes'],
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
          name='lanzou-cmd',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True , icon='logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='lanzou-cmd')
