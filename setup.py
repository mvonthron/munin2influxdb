#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='munin-influxdb',
    version='1.2.2',
    description='Munin to InfluxDB/Grafana gateway',
    author='Manuel Vonthron',
    author_email='manuel.vonthron@acadis.org',
    url='http://github.com/mvonthron/munin-influxdb',
    license='BSD',
    py_modules=['munininfluxdb'],
    entry_points={
        'console_scripts': [
            'muninflux = munininfluxdb.main:main',
        ]
    },
    install_requires=[
        'influxdb >= 2.12.0',
        'python-crontab>=2.1.1',
        'requests',
        'storable >= 1.0.0',
    ],
    extras_require={
        'dev': ['pytest-cov'],
        'test': ['pytest', 'mock'],
    },
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: System :: Monitoring',
    ]
)
