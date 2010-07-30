#!/usr/bin/env python
import os

def build():
    py_src = file('src/python_unittests.py').read()
    vim_src = file('src/python_unittests.vim').read()
    combined_src = vim_src.replace('__PYTHON_SOURCE__', py_src)
    if not os.path.exists('ftplugin'):
        os.mkdir('ftplugin')
    file('ftplugin/python_unittests.vim', 'w').write(combined_src)

if __name__ == '__main__':
    build()
