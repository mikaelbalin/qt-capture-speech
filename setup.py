"""
Setup script for Qt Camera Speech Recognition Application
"""

from setuptools import setup, find_packages
import os


# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    with open(requirements_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Read README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


setup(
    name="qt-camera-speech",
    version="2.0.0",
    description="Qt application for camera capture and speech recognition",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/qt-capture-speech",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "qt-camera-speech=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Graphics :: Capture :: Digital Camera",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    keywords="qt camera speech recognition opencv google-cloud",
)
