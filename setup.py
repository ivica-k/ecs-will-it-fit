# !/usr/bin/env python

__version__ = "0.1.0"

from distutils.core import setup
from pathlib import Path


current_dir = Path(__file__).parent

setup(
    name="willy",
    version=__version__,
    description="Checks whether an ECS service can fit on an ECS (EC2) cluster.",
    long_description=(current_dir / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Ivica Kolenkaš",
    author_email="ivica.kolenkas@gmail.com",
    url="https://github.com/ivica-k/ecs-will-it-fit",
    python_requires=">=3.6",
    packages=["willy"],
    license="MPL2.0",
    setup_requires=["wheel"],
    install_requires=["boto3==1.34.25", "pydantic==2.5.3"],
    package_dir={"willy": "willy"},
    entry_points={
        "console_scripts": ["willy=willy.cli:cli"],
    },
)
