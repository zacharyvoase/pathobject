# -*- coding: utf-8 -*-

import os
import re
from distutils.core import setup


rel_file = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

def read_from(filename):
    fp = open(filename)
    try:
        return fp.read()
    finally:
        fp.close()

def get_version():
    data = read_from(rel_file('src', 'pathobject.py'))
    return re.search(r'__version__ = "([^"]+)"', data).group(1)


setup(
    name            = 'pathobject',
    version         = get_version(),
    description     = "An update of Jason Orendorff's path.py.",
    author          = 'Zachary Voase',
    author_email    = 'z@zacharyvoase.com',
    url             = 'http://github.com/zacharyvoase/pathobject',
    package_dir     = {'': 'src'},
    py_modules      = ['pathobject'],
)
