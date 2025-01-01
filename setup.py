from setuptools import setup, find_packages

setup(
    name="networkii-cli",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'netifaces',
        'speedtest-cli',
        'pillow',
        'rpi-lgpio',
    ],
    entry_points={
        "console_scripts": [
            "networkii=cli:main",
        ],
    }
)