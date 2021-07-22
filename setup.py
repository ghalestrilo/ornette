from setuptools import setup

setup(
    packages=find_packages(where='server'),
    package_dir={
        '': '.',
    },
)
