from setuptools import setup

setup(
    name="networkii-cli",
    version="1.0.0",
    py_modules=['src.cli'],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'networkii=src.cli:main',
        ],
    },
) 