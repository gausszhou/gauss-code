# gauss-code

A Python project managed with uv.

## Description
This is a basic Python project template using uv for dependency management.

## Installation

1. Ensure uv is installed on your system
2. Clone this repository
3. Navigate to the project directory
4. Install dependencies:

```bash
uv sync
```

## Usage

To run the main script:

```bash
uv run python src/main.py
```

To run tests:

```bash
uv run pytest
```

## Project Structure
```
gauss-code/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
├── src/
│   ├── __init__.py
│   └── main.py
└── tests/
    ├── __init__.py
    └── test_main.py
```
