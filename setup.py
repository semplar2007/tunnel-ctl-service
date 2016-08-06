#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

# Utility function to read the README file.
def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as fp:
        return fp.read()

setup(
      name = "tunnel-ctl-service",
      version = "0.1",
      author = "Vyacheslav Kravchuk",
      author_email = "semplar2007@gmail.com",
      
      description = "An utility to remotely manage linode service",
      keywords = "service linode config",
      long_description = read("README.md"),
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: System :: Clustering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Information Technology",
      ],
      
      url = 'http://github.com/eddie-g/onestack.git',
      license = 'MIT',
      
      packages = find_packages(),
      zip_safe = False
)
