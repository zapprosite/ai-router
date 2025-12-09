# Contributing to AI Router

First of all, thank you for considering contributing to AI Router! It's people like you that make this tool faster, smarter, and more robust.

## 🤝 How Can I Help?

### 1. Report Bugs
Found a routing error? A model failing?
- Open an Issue.
- Provide the `curl` command or prompt that caused the failure.
- Include a snippet of the logs (`make logs`).

### 2. Suggest Features
Have an idea for a massive refactor or a simple tweak?
- Check the issues board first.
- Create a new issue describing the "Why" and "What" of your idea.

### 3. Submit Pull Requests
We accept PRs! Here's the workflow:

1.  **Fork** the repo.
2.  **Create a branch** for your feature: `git checkout -b feature/amazing-logic`
3.  **Code** your heart out.
4.  **Test** your changes:
    ```bash
    make smoke    # Run E2E smoke tests
    pytest        # Run unit tests
    ```
5.  **Commit** with clear messages.
6.  **Push** and open a **Pull Request**.

## 🛠️ Development Setup

**One-Liner:**
```bash
make dev
```
This sets up the virtualenv, installs dependencies, and starts the server in reload mode.

## 📐 Coding Standards

- **Python**: We use `black` for formatting.
- **Type Hints**: Please use type hints in function signatures.
- **Docstrings**: Explain complex logic, especially in `app/router.py`.

## 🛡️ License

By contributing, you agree that your contributions will be licensed under the MIT License.
