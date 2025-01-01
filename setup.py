from setuptools import setup, find_packages

setup(
    name="networkii",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'networkii=src.cli:main',
        ],
    },
) 