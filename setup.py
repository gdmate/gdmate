"""
Setuptools module for installation
"""

from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="gdmate",  
    version="0.1.0",
    description="",
    long_description=long_description, 
    long_description_content_type="text/markdown", 
    url="https://github.com/gdmate/gdmate",
    author="",
    author_email="",
    classifiers=[ 
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="geodynamics",
    packages=["gdmate","gdmate.analysis"],
    python_requires=">=3.7, <4",
    install_requires=["numpy","scipy","matplotlib","pyvista"],
    # package_data={ 
    # },
)