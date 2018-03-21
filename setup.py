from setuptools import setup


setup(
    name='gatenlp',
    version='3.1.1',
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
    python_requires='>=3',
    zip_safe=False,
)
