# ⚡ auto_cythonizer ⚡

[![PyPI - Version](https://img.shields.io/pypi/v/auto-cythonizer.svg)](https://pypi.org/project/auto-cythonizer)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/auto-cythonizer.svg)](https://pypi.org/project/auto-cythonizer)

---

## 💻 Installation

```console
pip install auto-cythonizer
```

## 💪 Example(s)

[Find em' here](https://github.com/pro-grammer-SD/auto_cythonizer_tests)

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
-t, --target TARGET  📁 Folder to Cythonize
-o, --output OUTPUT  📦 Output directory
-i, --install        📀 Build wheel & install
-l, --lib LIB        📚 Cythonize installed library
-c, --clean CLEAN    🧹 Clean compiled files in folder
-x, --pyxview        👀 View all generated .pyx files with file sizes
```

## 📄 License

`auto-cythonizer` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
