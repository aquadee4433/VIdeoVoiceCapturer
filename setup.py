"""Setup for videovoicecapturer."""

from setuptools import setup, find_packages

setup(
    name="videovoicecapturer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "yt-dlp>=2023.12.30",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "vvc=videovoicecapturer.cli:main",
        ],
    },
    python_requires=">=3.8",
)