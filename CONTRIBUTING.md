# Contributing to ContextOS

First off — thank you for taking the time to contribute. 🎉

---

## Code of Conduct

Be respectful. Be constructive. Be helpful.

---

## How to Contribute

### 1. Fork the repo

Click **Fork** on GitHub.

### 2. Clone your fork

```bash
git clone https://github.com/YOURUSERNAME/ContextOS.git
cd ContextOS
```

### 3. Set up environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### 4. Create a branch

```bash
git checkout -b feature/your-feature-name
```

### 5. Make your changes

### 6. Test your changes

```bash
context --help
context init "Test" "Test project"
context status
```

### 7. Commit and push

```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 8. Open a Pull Request on GitHub

---

## What to Contribute

- Bug fixes
- New CLI commands
- New integrations
- Documentation improvements
- Tests
- SDK improvements

---

## Commit Message Format
feat: add new feature
fix: fix a bug
docs: update documentation
test: add tests
refactor: refactor code
---

## Questions?

Open an issue on GitHub.