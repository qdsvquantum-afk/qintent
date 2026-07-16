project = "QIntent"
author = "QDSV / Qruba"
copyright = "2026, QDSV / Qruba"
version = "0.2"
release = "0.2.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "QIntent Documentation"
html_baseurl = "https://qdsvquantum-afk.github.io/qintent/"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/qdsvquantum-afk/qintent/",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "#0f766e",
        "color-brand-content": "#0f766e",
    },
    "dark_css_variables": {
        "color-brand-primary": "#2dd4bf",
        "color-brand-content": "#2dd4bf",
    },
}

autodoc_mock_imports = ["requests"]
napoleon_google_docstring = True
napoleon_numpy_docstring = True
