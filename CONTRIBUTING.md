# How to contribute to GDMATE

GDMATE welcomes contributions. Please open a GitHub issue for bug reports and
feature requests so proposed work can be discussed before implementation.

## Development setup

Fork the repository, clone your fork, and create a branch for your change. Use
Python 3.10 or newer and install the package with its development dependencies:

```console
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Code development

- Organize reusable functionality as functions in modules within the `gdmate`
  package.
- Add docstrings for public functions and modules.
- Expose only intended public names from package `__init__.py` files.
- Add or update a focused test for every behavior change.
- Add an annotated notebook example when it materially helps users understand
  a feature.

Run the test and lint checks before submitting a change:

```console
pytest
ruff check .
```

The reproducible notebooks can be checked independently:

```console
pytest --nbmake notebooks/helloworld.ipynb notebooks/visualization.ipynb
```

## Pull requests

Keep changes focused and use short, descriptive, present-tense commit messages.
In the pull request, explain the reason for the change and identify the tests
that demonstrate it. GitHub Actions will run the supported Python test matrix,
Ruff, and the reproducible notebook tests.
