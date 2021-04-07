# Created by matveyev at 07.04.2021

#!/usr/bin/python3

import io
import os

from setuptools import setup, find_packages
from build import build_routine

# Package meta-data.
NAME = 'OnlexmlEditor'
DESCRIPTION = 'A simple GUI editor of online.xml file for Sardana'
URL = 'https://github.com/yamedvedya/online_editor'
EMAIL = 'y.matveev@gmail.com'
AUTHOR = 'Yury Matveev'
REQUIRES_PYTHON = '>=3.5'
VERSION = '2.0'

# What packages are required for this module to be executed?
REQUIRED = ['PyQt5', 'psutil']

# What packages are optional?
EXTRAS = {}


# The rest you shouldn't have to touch too much :)
# ------------------------------------------------

here = os.path.abspath(os.path.dirname(__file__))


# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except IOError:
    long_description = DESCRIPTION


# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages("src", exclude=('tests',)),
    package_dir={'': 'src'},
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='GPLv3',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering'
    ],
)

build_routine()

