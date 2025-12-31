#!/usr/bin/env python3
"""
DRYAD.AI Python SDK Setup
"""

import os
import re
from setuptools import setup, find_packages

# Read version from __init__.py
def get_version():
    with open(os.path.join("gremlins_ai", "__init__.py"), "r") as f:
        content = f.read()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        raise RuntimeError("Unable to find version string")

# Read long description from README
def get_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "DRYAD.AI Python SDK - Official Python client for the DRYAD.AI platform"

# Read requirements
def get_requirements():
    with open("requirements.txt", "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="dryad-ai",
    version=get_version(),
    author="DRYAD.AI Team",
    author_email="support@DRYAD.AI.com",
    description="Official Python SDK for the DRYAD.AI platform",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/DRYAD_backend",
    project_urls={
        "Documentation": "https://docs.DRYAD.AI.com",
        "Source": "https://github.com/your-org/DRYAD_backend",
        "Tracker": "https://github.com/your-org/DRYAD_backend/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gremlins-ai=gremlins_ai.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gremlins_ai": ["py.typed"],
    },
    keywords=[
        "ai", "artificial-intelligence", "llm", "chatbot", "api", "sdk",
        "multi-agent", "rag", "vector-search", "multimodal", "nlp"
    ],
    zip_safe=False,
)
