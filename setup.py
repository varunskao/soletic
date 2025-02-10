from setuptools import find_packages, setup


# Define core dependencies needed for the package to run
CORE_DEPENDENCIES = [
    "python-dotenv>=1.0.1",
    "anyio>=4.8.0",
    "base58>=2.1.1",
    "black>=25.1.0",
    "certifi>=2025.1.31",
    "charset-normalizer>=3.4.1",
    "click>=8.1.8",
    "construct>=2.10.68",
    "construct-typing>=0.5.6",
    "h11>=0.14.0",
    "httpcore>=1.0.7",
    "httpx>=0.28.1",
    "idna>=3.10",
    "iniconfig>=2.0.0",
    "jsonalias>=0.1.1",
    "mypy-extensions>=1.0.0",
    "packaging>=24.2",
    "pathspec>=0.12.1",
    "platformdirs>=4.3.6",
    "pluggy>=1.5.0",
    "requests>=2.32.3",
    "setuptools>=75.8.0",
    "snakeviz>=2.2.2",
    "sniffio>=1.3.1",
    "solana>=0.36.3",
    "solders>=0.23.0",
    "tornado>=6.4.2",
    "typing_extensions>=4.12.2",
    "urllib3>=2.3.0",
    "websockets>=13.1",
]

# Define additional dependencies for development
DEV_DEPENDENCIES = [
    "pytest>=8.3",
    "black>=23.12.1",
]

setup(
    # Basic package metadata
    name="soletic",
    version="0.1.0",
    author="Soletic",
    author_email="varunskao@gmail.com.com",
    description="A lightweight data workflow SDK.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/varunskao/soletic",
    license="MIT License",
    # Package configuration
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Package data and dependencies
    include_package_data=True,
    package_data={
        "preswald": ["static/*", "static/assets/*", "templates/*"],
    },
    python_requires=">=3.7",
    # Dependencies
    install_requires=CORE_DEPENDENCIES,
    extras_require={
        "dev": DEV_DEPENDENCIES,
    },
    # Command line interface registration
    entry_points={
        "console_scripts": [
            "soletic=soletic.cli:cli",
        ],
    },
)
