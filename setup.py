from setuptools import setup

import staticconf

setup(
    name="PyStaticConfiguration",
    version=staticconf.version,
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
)
