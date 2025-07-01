# Contributing to OWL Requirements Analysis Assistant

First off, thank you for considering contributing to the OWL Requirements Analysis Assistant! It's people like you that make OWL such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible
* Include error messages and stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* List some other tools or applications where this enhancement exists

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guide
* Include thoughtfully-worded, well-structured tests
* Document new code
* End all files with a newline

## Development Process

1. Fork the repo
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`make test`)
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Setup Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/owl.git
cd owl/community_usecase/requirements-analysis-assistant

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make install-dev

# Setup pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_specific.py

# Run with coverage report
make coverage
```

### Code Style

We use several tools to maintain code quality:

* black for code formatting
* isort for import sorting
* flake8 for style guide enforcement
* mypy for type checking
* bandit for security checks

Run all style checks with:
```bash
make lint
```

### Documentation

* Use docstrings for all public modules, functions, classes, and methods
* Follow Google style for docstrings
* Update documentation when changing functionality
* Add examples for new features

Build documentation locally:
```bash
make docs
make serve-docs  # Serves docs at http://127.0.0.1:8000
```

## Project Structure

```
.
├── src/
│   └── owl_requirements/
│       ├── agents/           # Multi-agent system implementation
│       ├── cli/             # Command-line interface
│       ├── web/             # Web interface
│       ├── core/            # Core functionality
│       ├── utils/           # Utility functions
│       └── config/          # Configuration management
├── tests/                   # Test suite
├── docs/                    # Documentation
└── ...
```

## Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

## Additional Notes

### Issue and Pull Request Labels

* `bug`: Something isn't working
* `enhancement`: New feature or request
* `documentation`: Improvements or additions to documentation
* `good first issue`: Good for newcomers
* `help wanted`: Extra attention is needed
* `question`: Further information is requested

## Recognition

Contributors will be recognized in:

* The project's README.md
* The CONTRIBUTORS.md file
* Release notes when their contributions are included

## Questions?

* Check the documentation
* Search existing issues
* Open a new issue with the `question` label

Thank you for contributing to OWL Requirements Analysis Assistant! 