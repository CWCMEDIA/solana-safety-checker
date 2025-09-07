"""Setup script for sol-safety-check."""

from setuptools import setup, find_packages

setup(
    name="sol-safety-check",
    version="0.1.0",
    description="A comprehensive Solana token safety checker CLI tool",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "asyncio-throttle>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sol-safety-check=sol_safety_check.cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
