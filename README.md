# ⚡ auto_cythonizer ⚡

[![PyPI - Version](https://img.shields.io/pypi/v/auto-cythonizer.svg)](https://pypi.org/project/auto-cythonizer)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/auto-cythonizer.svg)](https://pypi.org/project/auto-cythonizer)

---

## 💻 Installation

```console
pip install auto-cythonizer
```

## 💪 Example(s)
[Here ✌️](https://github.com/pro-grammer-SD/auto_cythonizer_tests)

## ✨ Features

- 🐍 Automatically converts Python `.py` files into `.pyx` and compiles them to `.so`/`.pyd` with maximum Cython optimizations.
- ⚡ Caching enabled to speed up repeated builds.
- 🏎️ Multi-threaded scanning of Python files for faster processing.
- 📝 Automatic code annotation for loops and functions to leverage Cython's performance directives.
- 🔍 Missing module detection during build.
- 🔧 Auto-detects installed Python libraries and can fully Cythonize and rebuild them.
- 🚫 Exclude files and folders during build using `exclude.txt` or `.gitignore` style patterns, including wildcards.
- 🧹 Smart cleaning system with `-c` flag that removes build artifacts while keeping the target folder intact.
- 📦 Wheel building and automatic installation with pip.

## 🚀 Usage

```console
# Compile a Python folder
auto-cythonizer -t my_project

# Compile and install
auto-cythonizer -t my_project -i

# Clean build artifacts
auto-cythonizer -c my_project

# Auto-Cythonize an installed library
auto-cythonizer -l some_library
```

## 📄 License

`auto-cythonizer` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
