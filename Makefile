# Makefile for dgxtop development

PYTHON = python3
VENV = .venv
PIP = $(VENV)/bin/pip
VENV_PYTHON = $(VENV)/bin/python

.PHONY: help venv install run clean deb-build

# Default target: show help
help:
	@echo "DGXTOP Development Commands:"
	@echo "  make venv         - Create virtual environment and install dependencies"
	@echo "  make install      - Install the package in editable mode"
	@echo "  make run          - Run dgxtop locally in the virtual environment"
	@echo "  make clean        - Clean build artifacts, caches, logs, and temporary debian files"
	@echo "  make deb-build    - Build the Debian package (.deb)"

# Create virtual environment and install dependencies
venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt setup.py
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Virtual environment created at $(VENV). Run 'source $(VENV)/bin/activate' to use it."

# Install the package in editable mode
install: venv
	$(PIP) install -e .

# Run the system monitor locally
run: venv
	$(VENV_PYTHON) -m dgxtop.main

# Clean up all temporary files and directories
clean:
	@echo "Cleaning up build artifacts and caches..."
	rm -rf $(VENV)
	rm -rf .pybuild/
	rm -rf dgxtop.egg-info/
	rm -rf build/
	rm -rf dist/
	rm -rf deb_build/
	rm -rf debian/dgxtop/
	rm -rf debian/.debhelper/
	rm -f debian/debhelper-build-stamp
	rm -f debian/dgxtop.postinst.debhelper
	rm -f debian/dgxtop.prerm.debhelper
	rm -f debian/dgxtop.substvars
	rm -f debian/files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean completed."

# Build the Debian package
deb-build:
	@echo "Building Debian package..."
	dpkg-buildpackage -us -uc -b
	@echo "Package build completed."
