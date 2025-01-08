# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='What-Type-Of-Gamer-Are-You',
    version='0.1.0',
    description='Package for steam web app on AWS',
    long_description=readme,
    author='Acomputerguy',
    author_email='copyandpaste0@gmail.com',
    url='https://github.com/acomputerguy',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)