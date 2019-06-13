from setuptools import setup, find_packages


setup(
    name='gatenlp',
    version='3.2',
    description='Interface for parsing and manipulating GATE annotation documents',
    url='http://github.com/nickwbarber/gatenlp',
    author='Nick Barber',
    author_email='nickwbarber@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'lxml',
        'intervaltree'
    ],
    python_requires='>=3',
    zip_safe=False,
)
