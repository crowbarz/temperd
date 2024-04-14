"""temperd setup.py."""

import setuptools
from temperd.const import VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="temperd",
    version=VERSION,
    author="Crowbar Z",
    author_email="crowbarz@outlook.com",
    description="Publish temper sensor data to MQTT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crowbarz/temperd",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.9",
    install_requires=[
        "mqtt-base @ git+https://github.com/crowbarz/mqtt-base.git",
        "temper-py @ git+https://github.com/ccwienk/temper.git@4d1d3a2e3865241dd1c44696804c24b124cb901a",
        "python-slugify==8.0.1",
    ],
    entry_points={
        "console_scripts": [
            "temperd=temperd.temperd:main",
        ]
    },
)
