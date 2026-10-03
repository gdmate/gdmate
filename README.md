# GDMATE - GeoDynamic Modeling Analysis Toolkit and Education
[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/gdmate/gdmate/HEAD)
[![Documentation Status](https://readthedocs.org/projects/gdmate/badge/?version=latest)](https://gdmate.readthedocs.io/en/latest/)

## About

GDMATE is a Python library for generating and analyzing geodynamic models, along with related education.

Documentation: [http://gdmate.readthedocs.io](http://gdmate.readthedocs.io)

Source code: [https://github.com/gdmate/gdmate](https://github.com/gdmate/gdmate)

Authors (as of 2026)
* Dylan Vasey
* John Naliboff
* Lorraine Hwang
* Haoyuan Li

## Try GDMATE

## Getting started: The GDMATE Notebooks

For the moment, the main features of GDMATE are illustrated in the suite of Jupyter Notebooks housed in the `notebooks` directory. You can run and modifty these in the Binder environment [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/gdmate/gdmate/HEAD) or in your local environment with GDMATE installed. Additional notebooks and example scripts will be added as development proceeds.

Click on the Binder badge at the top of this README to launch a Python environment with GDMATE installed in your web browser.

## Installation

GDMATE requires Python 3.9 or newer. Runtime, development, and documentation
dependencies are declared in the repository's
[pyproject.toml](https://github.com/gdmate/gdmate/blob/main/pyproject.toml).

If you aren't familiar with managing Python virtual environments, [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-envs) is a good place to start.

From the repository root, create and activate the recommended Conda
environment with:

```console
conda create --name py-gdmate python=3.13 pip
conda activate py-gdmate
```

GDMATE is still in the earliest stages of development and is not yet available from typical hosting platforms (PyPI, Anaconda, etc.). For the moment, Users need to clone this repository, then install GDMATE into a Python environment
```
git clone https://github.com/gdmate/gdmate.git
```

For ordinary users, install GDMATE together with its runtime dependencies:

```console
python -m pip install .
```

For contributors, install GDMATE in editable mode with the additional development and documentation dependencies:

```console
python -m pip install -e ".[dev,docs]"
```

Editable mode makes changes in the local source tree immediately available in
the environment without reinstalling the package. The `dev` extra provides
the testing, linting, and build tools, while the `docs` extra provides the
documentation toolchain.

## About scripting in Python

GDMATE has the advantage of being adaptable and extensible in easy scripts.
As GDMATE is a toolkit, a graphical user interface would be impractical.
Nevertheless, we hope that we have succeeded in making GDMATE accessible to
coding novices. For those of you who have little experience with Python,
here are some specific features and pitfalls of the language:

* Python uses specific indentation. A script might fail if a code block is not indented correctly. We use four spaces and no tabs. Mixing spaces and tabs can cause trouble.
* Indices should be given inside square brackets and function or method call arguments inside parentheses (different from Matlab).
* The first index of an array or list is 0 (e.g. x[0]), not 1.
* Put dots after numbers to make them floats instead of integers.

## Contributing to GDMATE
GDMATE is a community-driven, open-source Python package by and for the geodynamics community. If you have code you would like to contribute, please review our [contribution guidelines](https://gdmate.readthedocs.io/en/latest/CONTRIBUTING.html) and open a [pull request](https://docs.github.com/en/pull-requests).
