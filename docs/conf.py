# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Copy GDMATE notebooks into the docs directory
import shutil
import sys
from pathlib import Path

docs_directory = Path(__file__).resolve().parent
repository_root = docs_directory.parent
nbdir = repository_root / "notebooks"
docdir = docs_directory / "notebooks"

try:
    shutil.copytree(nbdir,docdir)
except FileExistsError:
    shutil.rmtree(docdir)
    shutil.copytree(nbdir, docdir)

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
sys.path.insert(0, str(repository_root))

# -- Project information -----------------------------------------------------

project = "GDMATE"
author = "Dylan Vasey, John Naliboff, Lorraine Hwang, Haoyuan Li, Arushi Saxena"
copyright = f"2026, {author}"
release = "0.1.0"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

autosummary_generate = True
nbsphinx_execute = "never"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []
