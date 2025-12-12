import os
import sys
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import fnmatch
import re
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from setuptools import setup, Extension
from Cython.Build import cythonize

console = Console()

CYTHON_DIRECTIVES = {
    "boundscheck": False,
    "wraparound": False,
    "nonecheck": False,
    "cdivision": True,
    "language_level": 3,
    "initializedcheck": False,
    "infer_types": True,
    "profile": False,
    "linetrace": False,
}

STDLIB_MODULES = set(sys.stdlib_module_names)

def auto_annotate_code(py_code: str):
    if "cimport cython" not in py_code:
        return "cimport cython\n" + py_code
    return py_code

def check_imports(py_file: Path):
    import importlib
    missing = []
    try:
        for line in py_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(("import ", "from ")):
                mod = line.split()[1].split(".")[0]
                import importlib.util
                if importlib.util.find_spec(mod) is None:
                    missing.append(mod)
    except Exception:
        pass
    return missing

def load_exclude_list(target: Path):
    patterns = []
    for name in ["exclude.txt", ".gitignore"]:
        f = target / name
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line.replace("\\", "/"))
    return patterns

def is_excluded(file_path: Path, target: Path, patterns):
    rel_path = file_path.relative_to(target).as_posix()
    return any(fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(rel_path, f"**/{pat}") for pat in patterns)

def scan_file(src_file: Path, src_root: Path, out_dir: Path):
    rel_path = src_file.relative_to(src_root).parent
    dest_dir = out_dir / rel_path
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"{src_file.stem}.pyx"
    try:
        annotated = auto_annotate_code(src_file.read_text(encoding="utf-8"))
        dest_file.write_text(annotated, encoding="utf-8")
    except Exception:
        pass
    missing = check_imports(src_file)
    return dest_file, missing

def scan_and_prepare(src_dir: Path, out_dir: Path):
    patterns = load_exclude_list(src_dir)
    py_files = [f for f in src_dir.rglob("*.py") if not is_excluded(f, src_dir, patterns)]
    pyx_files, missing_modules = [], set()

    with Progress(
        SpinnerColumn(spinner_name="earth"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Scanning {src_dir}...🔥", total=len(py_files))
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(scan_file, f, src_dir, out_dir) for f in py_files]
            for fut in futures:
                dest_file, missing = fut.result()
                pyx_files.append(dest_file)
                missing_modules.update(missing)
                progress.update(task, advance=1)

    if missing_modules:
        console.print(f"[red]⚠ Missing modules: {', '.join(missing_modules)}[/]")

    return pyx_files

def fix_stdlib_shadowing(lib_path: Path):
    renamed = {}
    for folder in lib_path.rglob("*"):
        if folder.is_dir() and folder.name in STDLIB_MODULES:
            new_name = folder.name + "_safe"
            folder.rename(folder.parent / new_name)
            renamed[folder.name] = new_name
    if renamed:
        py_files = list(lib_path.rglob("*.py"))
        for f in py_files:
            try:
                txt = f.read_text(encoding="utf-8")
                for old, new in renamed.items():
                    txt = re.sub(rf"\bimport {old}\b", f"import {new}", txt)
                    txt = re.sub(rf"\bfrom {old}\b", f"from {new}", txt)
                f.write_text(txt, encoding="utf-8")
            except Exception:
                continue
    return renamed

def build(target: str, output_dir: str):
    out_dir = Path(output_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]🚀 Preparing to compile {target}...[/]")
    pyx_files = scan_and_prepare(Path(target), out_dir)

    console.print(f"[yellow]🔧 Building optimized Cython extensions...[/]")
    exts = [
        Extension("*", [str(p)],
                  extra_compile_args=["-O3", "-march=native", "-fopenmp", "-flto"],
                  extra_link_args=["-fopenmp", "-flto"])
        for p in pyx_files
    ]
    try:
        setup(script_args=["build_ext", "--inplace"],
              ext_modules=cythonize(exts,
                                    compiler_directives=CYTHON_DIRECTIVES,
                                    nthreads=os.cpu_count(), # pyright: ignore[reportArgumentType]
                                    build_dir="cycache"))
    except Exception:
        pass
    console.print("[bold green]✅ Build complete![/]")

def clean_output(target: str):
    console.print(f"[red]🧹 Cleaning compiled files in '{target}'...[/]")
    folder = Path(target)
    if not folder.exists():
        console.print(f"[yellow]⚠ Folder '{target}' does not exist[/]")
        return
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix in [".so", ".pyd"]:
            f.unlink(missing_ok=True)
    console.print(f"[bold green]✅ All compiled files removed in '{target}'[/]")

def view_pyx_file_sizes():
    pyx_files = list(Path(".").rglob("*.pyx"))
    if not pyx_files:
        console.print("[red]❌ No generated .pyx files found.[/]")
        return
    table = Table(title="📄 Generated .pyx Files with Sizes")
    table.add_column("File Path", style="cyan")
    table.add_column("File Size", justify="right", style="yellow")
    for f in pyx_files:
        size = f.stat().st_size
        table.add_row(str(f), f"{size / 1024:.2f} KB")
    console.print(table)

def ensure_pyproject_only(build_path: Path, lib_name: str, version: str):
    # Find all top-level packages (folders with __init__.py)
    packages = [p.name for p in build_path.iterdir() if (p / "__init__.py").exists()]
    setup_file = build_path / "setup.py"
    setup_file.write_text(f"""
from setuptools import setup

setup(
    name="{lib_name}",
    version="{version}",
    packages={packages},
    include_package_data=True
)
""".strip(), encoding="utf-8")

def cythonize_library(lib_name: str):
    import importlib.util
    spec = importlib.util.find_spec(lib_name)
    if not spec or not spec.origin:
        console.print(f"[red]❌ Library {lib_name} not found![/]")
        return
    src_path = Path(spec.origin).parent
    tmp = Path(".cytmp") / lib_name
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_path, tmp, dirs_exist_ok=True)

    console.print("[cyan]🔍 Fixing stdlib shadowing...[/]")
    fix_stdlib_shadowing(tmp)

    build(str(tmp), str(tmp / "build"))

    try:
        import importlib.metadata
        version = importlib.metadata.version(lib_name)
    except Exception:
        version = "0.0.1"
    ensure_pyproject_only(tmp, lib_name, version)

    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "."],
                       cwd=tmp, check=True)
        console.print(f"[bold green]🚀 {lib_name} installed successfully![/]")
    except Exception:
        console.print(f"[yellow]⚠ Installation failed[/]")

    shutil.rmtree(tmp)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="⚡ Auto-Cythonizer PRO MAX")
    parser.add_argument("-t", "--target", help="📁 Folder to Cythonize")
    parser.add_argument("-o", "--output", default="build_lib", help="📦 Output directory")
    parser.add_argument("-i", "--install", action="store_true", help="📀 Build wheel & install")
    parser.add_argument("-l", "--lib", help="📚 Cythonize installed library")
    parser.add_argument("-c", "--clean", help="🧹 Clean compiled files in folder")
    parser.add_argument("-x", "--pyxview", action="store_true", help="👀 View all generated .pyx files with file sizes")

    args = parser.parse_args()

    if args.pyxview:
        view_pyx_file_sizes()
        return
    if args.clean:
        clean_output(args.clean)
        return
    if args.lib:
        cythonize_library(args.lib)
        return
    if args.target:
        build(args.target, args.output)
        if args.install:
            try:
                subprocess.run([sys.executable, "-m", "build", "--wheel"], check=True)
            except Exception:
                console.print("[yellow]⚠ Wheel build failed[/]")
        return
    console.print("[red]❌ Provide --target, --lib, --clean, or --pyxview[/]")

if __name__ == "__main__":
    main()
    