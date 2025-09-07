"""Setup script for Splunk Community AI."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh 
        if line.strip() and not line.startswith("#") and not line.startswith("-e")
    ]

# Add catalyst_mcp as a dependency from the external git repository
requirements.append("catalyst_mcp @ git+https://github.com/billebel/catalyst_mcp.git")

setup(
    name="splunk-community-ai",
    version="1.0.0",
    author="Splunk Community AI Team",
    description="Community-driven AI platform for Splunk integration with LibreChat",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    ],
    python_requires=">=3.8",
    install_requires=requirements,
)