# Networkii

A network monitoring and statistics tool for Raspberry Pi.

## Installation

You can install the package directly from the source:

```bash
pip install .
```

## Usage

After installation, you can use the `networkii` command-line tool:

1. Show current configuration:
```bash
networkii show
```

2. Update configuration:
```bash
networkii set --ping-target 1.1.1.1 --speed-test-interval 60
```

## Development

To set up the development environment:

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install in development mode:
```bash
pip install -e .
``` 