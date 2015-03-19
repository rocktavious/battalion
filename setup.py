import os
from setuptools import setup

setup(
    setup_requires=[
        'pbr',
        'pyversion>=0.3.0'
    ],
    pbr=True,
    auto_version="PBR",
)
