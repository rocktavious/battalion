import os
from setuptools import setup
import battalion

os.environ['PBR_VERSION'] = str(battalion.__version__)
setup(
    setup_requires=['pbr',
                    'pyversion>=0.2.3'],
    pbr=True)
