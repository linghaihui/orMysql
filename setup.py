# coding=utf-8

from setuptools import setup, find_packages


def get_requirements():
    with open("requirements.txt", "r") as f:
        return [line for line in f if line and not line.startswith("#")]


setup(name="orMysql",
    version="0.0.1",
    url="https://github.com/linghaihui/orMysql",
    license="MIT",
    author="linghaihui",
    author_email="haihuiling2014@gmail.com",
    description="A simple orm",
    packages=find_packages(exclude=["tests"]),
    install_requires=get_requirements(),
    include_package_data=True,
    zip_safe=False,)
