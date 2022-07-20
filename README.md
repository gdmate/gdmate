# GDMATE - GeoDynamic Modeling Analysis Toolkit and Education
[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/gdmate/gdmate/HEAD)

## About

GDMATE is a Python library for generating or analyzing geodynamic models, and fundamental related education.

Homepage:

Documentation: 

Source code: https://github.com/gdmate/gdmate

Forums:

Authors (as of 2022)
* Dylan Vasey
* John Naliboff

## Requirements

* Python 3.7+
* Python modules:
  NumPy, SciPy, Matplotlib, Pyvista

## Optional, needed for some functionality

## Installation
Installation of GDMATE is mostly platform independent.
As long as you know how to use a terminal, the process should be straightforward.
The following instructions should help, but let us know if you have any problems.

### Environment management
We strongly recommend using a python environment manager like conda or pyenv to install
gdmate and its dependencies. This is especially the case for installations on modern Mac systems.

For pyenv, we suggest you select the most recent version of python supported by GDMATE, install all of the dependencies into that environment and set the GDMATE root directory to use that environment automatically.

For conda, we suggest making a new environment for the gdmate installation, install the most recent version of python supported by GDMATE into that environment, and install all of the dependencies into that environment. Remember to activate the environment before installing new dependencies or using GDMATE.

### Dependencies
First, make sure you have a sufficiently recent version of python installed on your machine (see above for the latest requirements).  To check your version of python, type the following in a terminal:
    python --version
If your version is not recent enough, visit https://www.python.org/ to find out how to install a newer version.

Once you have checked your version of python, you should make sure you have installed the python module pip. We will use this module to install GDMATE. If you don't have it already, you can install it by opening a terminal window and typing:

    python -m ensurepip --upgrade

Mac users will also need to install Xcode, which can be found in the MacStore.

### Stable version
If you are only interested in using GDMATE (rather than developing the software), and you aren't interested in any of the latest changes, you can install the stable version with pip by typing the following into a terminal window:

    python -m pip install gdmate

Installation through conda works in a similar manner:

    conda install gdmate


This method of installation does not give you easy access to all the examples, or the test suite. These can be found in the latest release package which can be downloaded from https://github.com/gdmate/gdmate/releases.

### Development version
If you want to install the development version of GDMATE (with all the latest features), you will first need to download the source code. The best way to do this is by using git (a version control system). To install git, follow the instructions at https://git-scm.com/downloads.

Then, using a terminal, navigate to the directory into which you want to clone the GDMATE repository, and type

    git clone https://github.com/gdmate/gdmate.git

Once the repository is cloned, navigate to the top-level directory by typing `cd gdmate` in the terminal, and then install GDMATE, either in static mode: `python -m pip install .` or in development mode (if you want to develop or modify the code): `python -m pip install -e .`.

### Checking that the installation worked

To check that the installation has worked, you can run the test suite (`./test.sh`). 

A more basic check that GDMATE is installed is to navigate to the GDMATE examples directory and type:

    python example_beginner.py

If figures show up, GDMATE has been installed.

## Getting started: The GDMATE Tutorial

An introduction to the tools available in GDMATE can be found in the GDMATE
Tutorial. These are ipython notebooks that can be run from inside jupyterlab.

If you want to run these notebooks without installing GDMATE, you can access
them on binder.org via the links below.

## More detail: The Examples Suite

The GDMATE tutorials provide a basic but incomplete understanding of what
the module can do. To supplement the tutorials, GDMATE includes a
large suite of examples that provide more in-depth coverage of the
potential uses of the module.

For an up-to-date summary of all the examples, including the generated figures,
the user is referred to the GDMATE manual (http://gdmate.readthedocs.io).

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
