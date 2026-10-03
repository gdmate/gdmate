# Building a Python Package #

As with all things Python, there are many ways to create a Python package. There are guides to many of the individual tools and steps on the Internet, but it can be difficult to find a clear path from zero to package, so we will attempt to document how GDMATE was created here.

This guide assumes basic familiarity with Python and installing packages.

## Basic directory structure ##

The root directory contains the usual basic repository files (`README.md`,
`license.txt`, and `.gitignore`) as well as the `pyproject.toml` file that
defines the package and its development tools. The installable source code
resides in the `gdmate` directory. Additional directories contain
documentation (`docs`), Jupyter Notebooks (`notebooks`), and tests (`tests`).

Within the `gdmate` directory, the source code is contained within _modules_, which are individual `.py` files that each contain callable _functions_. These modules are organized into _packages_, which are directories containing multiple modules and an `__init__.py` file, which indicates that the modules should be treated together as a package. The principal package is `gdmate`, and each subdirectory (for example, `analysis`, `aspect_tools`, or `rheology_models`) is considered a _subpackage_ of GDMATE. Each package/subpackage needs to be installed during package setup, and the package/subpackage structure is an important consideration for imports and namespaces when using the package.

More about Python modules available [here](https://docs.python.org/3/tutorial/modules.html), and more about packaging [here](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

## Project configuration and installation ##

Python package installation is usually handled by pip, including inside conda
environments. GDMATE uses the standardized `pyproject.toml` format with
setuptools as its build backend. The Python Packaging Authority provides a
[packaging tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
that explains this format.

The file contains project metadata, supported Python versions, runtime
dependencies, optional development and documentation dependencies, and tool
configuration. For example:

```toml
[project]
requires-python = ">=3.9"
dependencies = ["matplotlib", "numpy", "pyvista", "scipy"]

[project.optional-dependencies]
dev = ["build", "nbmake", "pytest>=8", "ruff>=0.11"]
```

Running `pip install .` from the repository root installs GDMATE and its
runtime dependencies. Contributors can use `pip install -e ".[dev]"` for an
editable installation with the test, lint, and build tools.

## Imports and Namespaces ##
If all `__init__.py` files are blank, each subpackage within the Python package can be imported directly (e.g., `import gdmate.analysis`). However, if only the root package is imported (i.e., `import gdmate`), the modules within subpackages will not be accessible. Adding import statements to the base `__init__.py` file defines the namespaces for subpackages, modules, and/or functions in relation to the base package. For example, the `__init__.py` file for GDMATE contains the line:

```
from gdmate.visualization import pyvista_vis
```

As a result, when a user's script runs `import gdmate`, the `pyvista_vis` module can be accessed simply as `gdmate.pyvista_vis`. Note that this particular formulation removes the subpackage `visualization` from the namespace; `gdmate.visualization.pyvista_vis` will fail unless the import statement is `import gdmate.visualization`. Python namespaces are notoriously confusing.


## Testing ##
Setting up automated tests is essential for debugging non-functional code and ensuring compatibility with multiple versions of Python. We have a relatively simple testing workflow implemented using `pytest` and automated using GitHub Actions.

### Pytest ###
Designing tests for use with Pytest is fairly straightforward. Pytest will search a repository for directories, modules, and functions with the word "test," making it simple to run all tests just with the command `pytest`. To design a test for use with Pytest, you simply have to make functions with `assert` statements that Pytest can attempt to evaluate as true. A simple example is shown [here](https://docs.pytest.org/en/7.1.x/). In GDMATE, the tests are housed within a `tests` directory separate from the source code, and the tests can be run locally by installing Pytest in an environment with GDMATE and executing `pytest`.

We extend testing to verify the reproducible Jupyter Notebooks with the nbmake
plugin for Pytest. Notebook tests are run separately from unit tests:

```console
pytest --nbmake notebooks
```

The GitHub Actions workflow tests Python 3.9 through 3.13. It also builds the
distribution, runs Ruff, and executes the selected notebooks. These checks run
for pull requests and pushes to `main`.

## Sphinx Documentation ##
Documentation is generated using Sphinx and hosted by Read the Docs. Sphinx
configuration lives under `docs`, while `.readthedocs.yaml` defines the hosted
build environment. Documentation dependencies are declared in the `docs`
optional dependency group in `pyproject.toml`. The `autosummary` and `autodoc`
extensions generate the package API, `nbsphinx` renders Jupyter Notebooks, and
`myst-parser` renders Markdown files.
