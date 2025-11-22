"""
Browser Isolation System - Setup Configuration

Installation package for the Browser Isolation System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="browser-isolation",
    version="1.0.0",
    author="Browser Isolation Team",
    author_email="contact@example.com",
    description="Zero-Trust Remote Browser Isolation System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/browser_isolation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/browser_isolation/issues",
        "Source": "https://github.com/yourusername/browser_isolation",
        "Documentation": "https://github.com/yourusername/browser_isolation#readme",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "isolationctl=cli.isolationctl:cli",
            "browser-isolation-api=api.server:start_server",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.html", "*.txt"],
    },
    keywords=[
        "security",
        "browser",
        "isolation",
        "rbi",
        "zero-trust",
        "malware-protection",
        "xss-prevention",
        "web-security",
        "sandbox",
        "dom-sanitization",
    ],
    zip_safe=False,
)

