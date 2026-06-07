# Contributing to DGXTOP

Thank you for your interest in contributing to DGXTOP! We welcome contributions from everyone and appreciate your help in making this project better.

## Ways to Contribute

We welcome all types of contributions:

- **Bug fixes** - Help us squash bugs and improve stability
- **New features** - Add new monitoring capabilities or UI improvements
- **Documentation** - Improve the README, add examples, or clarify existing docs
- **Testing** - Help expand test coverage or report issues

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/doggy8088/dgxtop.git
cd dgxtop
```

### 2. Set Up Development Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt  # If available
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Code Style

We follow **PEP 8** style guidelines for Python code. Please ensure your contributions adhere to these standards:

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 79 characters for code, 72 for docstrings
- Use meaningful variable and function names
- Add docstrings to functions and classes

You can check your code style with:

```bash
# Install flake8 if not already installed
pip install flake8

# Run style check
flake8 dgxtop/
```

## Testing Requirements

**All contributions must pass tests before being merged.**

Before submitting your pull request:

```bash
# Run the test suite
python -m pytest

# Or run specific tests
python -m pytest tests/test_specific.py
```

### Hardware Testing Requirements

- **GPU-related changes**: Must be tested on actual NVIDIA hardware with `nvidia-smi` available
- **CPU/Memory/Disk/Network changes**: Can be tested on any Linux system
- If you don't have access to DGX hardware, please note this in your PR and a maintainer will help test GPU-related functionality

## Submitting Changes

### 1. Commit Your Changes

Write clear, concise commit messages:

```bash
git add .
git commit -m "Add feature: brief description of what you added"
```

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Open a Pull Request

- Go to the original DGXTOP repository on GitHub
- Click "New Pull Request"
- Select your fork and branch
- Fill out the PR template with details about your changes
- Submit the pull request

## Pull Request Guidelines

- **One feature/fix per PR** - Keep pull requests focused and manageable
- **Update tests** - Add or update tests for any new functionality
- **Update documentation** - If your change affects usage, update the README
- **Follow the PR template** - Fill out all relevant sections

## Response Time

We aim to review all issues and pull requests **within one week**. If you haven't heard back after a week, feel free to leave a comment to bump the discussion.

## Development Tips

### Running DGXTOP Locally

```bash
# Run from source
python -m dgxtop

# Or after installing in development mode
dgxtop
```

### Project Structure

```
dgxtop/
├── main.py           # Application entry point and main loop
├── disk_monitor.py   # Disk I/O monitoring
├── system_monitor.py # CPU and memory monitoring
├── gpu_monitor.py    # NVIDIA GPU monitoring
├── network_monitor.py# Network interface monitoring
├── rich_ui.py        # Terminal UI rendering
├── config.py         # Configuration management
└── logger.py         # Logging utilities
```

## Questions?

If you have questions about contributing, feel free to:

- Open a GitHub issue with the "question" label
- Check existing issues for similar questions

## Code of Conduct

Please note that this project has a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

Thank you for contributing to DGXTOP!
