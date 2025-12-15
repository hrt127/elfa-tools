# Contributing to Elfa Tools

Thank you for your interest in contributing to Elfa Tools! This document provides guidelines and instructions for contributing.

## 🎯 How to Contribute

We welcome contributions of all kinds:

- Bug reports
- Feature requests
- Code improvements
- Documentation updates
- Examples and tutorials


## 🚀 Getting Started

1. **Fork the repository**

   ```bash
   git clone https://github.com/your-username/elfa-tools.git
   cd elfa-tools
   ```

2. **Set up your development environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create a branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```


## 📝 Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and narrow (single responsibility)
- Add comments for complex logic


## 🧪 Testing

Before submitting a pull request:

- Test your changes with multiple tickers
- Verify error handling works correctly
- Check that existing functionality still works
- Test with different time windows


## 📋 Pull Request Process

1. **Update documentation** if you've changed functionality
2. **Update CHANGELOG.md** with your changes
3. **Ensure all code follows the style guidelines**
4. **Test your changes thoroughly**
5. **Create a clear PR description** explaining:
   - What changes you made
   - Why you made them
   - How to test the changes

## 🐛 Reporting Bugs

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages (if any)
- Relevant code snippets

## 💡 Feature Requests

For feature requests, please:

- Describe the feature clearly
- Explain the use case
- Discuss potential implementation approaches
- Consider backward compatibility


## 🧩 Design Principles

When contributing code, keep in mind our design philosophy:

1. **Narrow** — Each tool should do one job well
2. **Explainable** — Show source data, contributing factors, and audit trails
3. **Robust** — Fail gracefully, never crash, handle partial data
4. **Composable** — Tools should work standalone and snap together naturally
5. **Signal Layer, Not Oracle** — Provide signals and context, not answers
6. **Transparent Constraints** — Make rate limits, caching, and provenance visible

Every contribution should converge on the **Decision Moment**: a structured explanation of why now matters.

See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for the complete design philosophy, including quality standards and non-goals.

## 📚 Documentation

- Update README.md if you add new features
- Add docstrings to new functions/classes
- Update examples if behavior changes
- Keep ROADMAP.md updated if adding new modules


## ✅ Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Tests pass (if applicable)
- [ ] No new warnings or errors
- [ ] Backward compatibility maintained (if applicable)

## 🙏 Thank You

Your contributions make Elfa Tools better for everyone. We appreciate your time and effort!

