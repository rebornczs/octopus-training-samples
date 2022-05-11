# -*- coding: utf-8 -*-
from pip._internal.network.session import PipSession
from pip._internal.req import parse_requirements
from setuptools import setup

install_reqs = parse_requirements("requirements.txt", session=PipSession())
reqs = [str(ir.requirement) for ir in install_reqs]

setup(
    name="octopus_utils",
    version="1.0.0",
    description="src algorithm utils",
    author="reborn",
    packages=["octopus_utils"],
    package_data={"octopus_utils": ["resources/icon.png", "resources/song.ttf"]},
    include_package_data=True,
    install_requires=reqs
)
