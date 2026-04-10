from setuptools import setup, find_packages

setup(
    name="envault",
    version="0.1.0",
    description="Securely manage and sync environment variables across multiple projects with encryption.",
    author="envault contributors",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "cryptography>=41.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "envault=envault.cli:cli",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Portable",
        "Topic :: Security :: Cryptography",
        "Topic :: Utilities",
    ],
)
