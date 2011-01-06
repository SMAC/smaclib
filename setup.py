from setuptools import setup, find_packages


VERSION = '0.1'


setup(
    name='smac',
    version=VERSION,
    description="SMAC - Smart Multimedia Archive for Conferences",
    keywords='',
    author='Jonathan Stoppani',
    author_email='jonathan.stoppani@edu.hefr.ch',
    url='',
    license='GPLv2',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'txredis',
        'twisted',
        'lxml',
        'thrift',
        'txamqp',
    ],
)