"""
Setup script for DGXTOP Ubuntu
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dgxtop",
    version="1.1.0",
    author="DGXTOP Ubuntu Team",
    author_email="team@dgxtop.com",
    description=(
        "Performance monitoring CLI tool for DGX systems with volume transfer speed tracking"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/doggy8088/dgxtop",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System",
        "Administrators",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Ubuntu",
    ],
    python_requires=">=3.8",
    install_requires=[
        "psutil>=5.8.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dgxtop=dgxtop.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
