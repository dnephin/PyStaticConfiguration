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
    url="https://github.com/dnephin/PyStaticConfiguration",
    description='A python library for loading static configuration',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
    ],
    extras_require={
        'yaml': ['pyyaml'],
    },
    packages=['staticconf'],
    install_requires=['six'],
)
