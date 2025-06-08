from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
readme_path = this_directory / "README.md"

# Read README with encoding and fallback
try:
    long_description = readme_path.read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = ""

setup(
    name="ccip-sdk",
    version="0.1.124",
    description="The simplest Python SDK for Chainlink CCIP that turns complex cross-chain operations into 15 lines of code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dhananjay Pai",
    author_email="dhananjay2002pai@gmail.com",
    url="https://github.com/dhananjaypai08/ccip-sdk",
    license="MIT",
    packages=find_packages(include=["ccip_sdk", "ccip_sdk.*"]),
    include_package_data=True,
    package_data={
        "ccip_sdk": [
            "ccip_directory/*.json",
            "ccip_directory/**/*.json",
            "contracts/artifacts/contracts/CCIPContract/*.json",
        ],
    },
    install_requires=[
        "web3",
        "eth_account",
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)