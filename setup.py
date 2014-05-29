import os.path
from setuptools import setup

about = {}
version_path = os.path.join(os.path.dirname(__file__), 'staticconf', 'version.py')
with open(version_path) as f:
    exec(f.read(), about)

setup(
    name="PyStaticConfiguration",
    version=about['version'],
    provides=["staticconf"],
    author="Daniel Nephin",
    author_email="dnephin@gmail.com",
    url="http://github.com/dnephin/PyStaticConfiguration",
    description='A python library for loading static configuration',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
    ],
    extras_require={
        'yaml': ['pyyaml'],
    },
    packages=['staticconf'],
    install_requires=['six',],
)
