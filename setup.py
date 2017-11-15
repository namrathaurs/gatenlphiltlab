from setuptools import setup


setup(
    name='gatenlp',
    version='3.0',
    description='Interface for parsing and manipulating GATE annotation documents',
    url='http://github.com/nickwbarber/gatenlp',
    author='Nick Barber',
    author_email='nickwbarber@gmail.com',
    license='MIT',
    packages=['gatenlp'],
    install_requires=[
        'lxml',
        'intervaltree'
    ],
    zip_safe=False
)
