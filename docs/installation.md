# Installation

AutoFrame uses [pixi](https://pixi.sh) for dependency management, which makes installation and development straightforward.

## Prerequisites

You'll need:

- **Python 3.12+** 
- **pixi** (recommended) or pip
- **MongoDB** (if using MongoDB data sources)

## Install pixi (Recommended)

First, install pixi if you haven't already:

=== "macOS"

    ```bash
    curl -fsSL https://pixi.sh/install.sh | bash
    ```

=== "conda/mamba"

    ```bash
    conda install -c conda-forge pixi
    ```

=== "Other platforms"

    See [pixi installation docs](https://pixi.sh/latest/installation/)

## Install AutoFrame

### Development Installation

For development or to get the latest features:

```bash
git clone https://github.com/jesserobertson/autoframe.git
cd autoframe
pixi install
```

This installs AutoFrame in development mode with all dependencies.

### Production Installation (Future)

Once released to PyPI:

```bash
pip install autoframe
```

## Verify Installation

Test that everything works:

```bash
pixi run python -c "
import autoframe as af
print(f'AutoFrame {af.__version__} installed successfully!')

# Test basic functionality
docs = [{'name': 'test', 'value': 42}]
result = af.to_dataframe(docs)
print(f'Basic test: {\"✅ PASS\" if result.is_ok() else \"❌ FAIL\"}')
"
```

## Optional Dependencies

### Polars Support

AutoFrame includes polars support by default, but you can disable it:

```bash
pixi add autoframe  # Includes polars
# or for pandas-only
pip install autoframe --no-deps && pip install pandas logerr pymongo tenacity
```

### Visualization (for Quality Reports)

For enhanced quality reports with visualizations:

```bash
pixi add matplotlib seaborn
```

## MongoDB Setup

If you're using MongoDB data sources, you'll need a MongoDB instance:

### Local Development

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Using homebrew (macOS)
brew install mongodb-community
brew services start mongodb-community
```

### Cloud Options

- [MongoDB Atlas](https://www.mongodb.com/atlas) (cloud)
- [MongoDB Cloud Manager](https://cloud.mongodb.com/)

## Next Steps

- [Quick Start Guide](quickstart.md) - Your first AutoFrame pipeline
- [Examples](examples.md) - Real-world usage patterns
- [Core Concepts](concepts.md) - Understanding AutoFrame's functional approach