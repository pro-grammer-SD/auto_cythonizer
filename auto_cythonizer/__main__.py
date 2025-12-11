import os
import shutil
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
import importlib.util
import fnmatch

console = Console()

CYTHON_DIRECTIVES = {
    "boundscheck": False,
    "wraparound": False,
    "nonecheck": False,
    "cdivision": True,
    "language_level": 3,
    "initializedcheck": False,
    "infer_types": True
}

def auto_annotate_code(py_code: str) -> str:
    lines, new_lines = py_code.splitlines(), []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if stripped.startswith("for ") and "in range" in stripped:
            var = stripped.split()[1]
            if var.isidentifier():
                indent = len(line) - len(line.lstrip())
                new_lines.append(" " * indent + f"# cdef int {var} (annotated)")
        elif stripped.startswith("def "):
            indent = len(line) - len(line.lstrip())
            new_lines.extend([
                " " * indent + "# @boundscheck(False)",
                " " * indent + "# @wraparound(False)",
                " " * indent + "# @nonecheck(False)",
                " " * indent + "# @cdivision(True)"
            ])
        new_lines.append(line)
    if "cimport cython" not in py_code:
        new_lines.insert(0, "# cimport cython")
    return "\n".join(new_lines)

def check_imports(py_file: Path):
    missing = []
    for line in py_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(("import ", "from ")):
            mod = line.split()[1].split(".")[0]
            if importlib.util.find_spec(mod) is None:
                missing.append(mod)
    return missing

def load_exclude_list(target: Path):
    patterns = []

    # Load exclude.txt
    exclude_txt = target / "exclude.txt"
    if exclude_txt.exists():
        for line in exclude_txt.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line.replace("\\", "/"))

    # Merge .gitignore if exists
    gitignore = target / ".gitignore"
    if gitignore.exists():
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line.replace("\\", "/"))

    return patterns

def is_excluded(file_path: Path, target: Path, patterns):
    rel_path = file_path.relative_to(target).as_posix()
    for pat in patterns:
        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(rel_path, f"**/{pat}"):
            return True
    return False

def scan_file(src_file: Path, out_dir: Path):
    rel_path = src_file.relative_to(src_file.parents[1]).parent
    dest_dir = out_dir / rel_path
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / (src_file.stem + ".pyx")
    annotated = auto_annotate_code(src_file.read_text(encoding="utf-8"))
    dest_file.write_text(annotated, encoding="utf-8")
    missing = check_imports(src_file)
    return dest_file, missing

def scan_and_prepare(src_dir: Path, out_dir: Path):
    patterns = load_exclude_list(src_dir)
    py_files = [f for f in src_dir.rglob("*.py") if not is_excluded(f, src_dir, patterns)]
    pyx_files, missing_modules = [], set()

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Scanning & annotating {src_dir}...📝", total=len(py_files))
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(scan_file, f, out_dir) for f in py_files]
            for fut in futures:
                dest_file, missing = fut.result()
                pyx_files.append(dest_file)
                missing_modules.update(missing)
                progress.update(task, advance=1)

    if missing_modules:
        console.print(f"[bold red]⚠️ Missing modules detected: {', '.join(missing_modules)}[/]")
    return pyx_files

def build(target: str, output_dir: str):
    out_dir = Path(output_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]🚀 Preparing to compile {target} into .so/.pyd files...[/]")
    pyx_files = scan_and_prepare(Path(target), out_dir)

    console.print(f"[yellow]🔧 Compiling .pyx files to .so/.pyd with caching and max Cython optimizations...[/]")
    from Cython.Build import cythonize
    from setuptools import setup

    pyx_files_str = [str(p) for p in pyx_files]

    ext_modules = cythonize(
        pyx_files_str,
        compiler_directives=CYTHON_DIRECTIVES,
        build_dir="cython_cache",
        cache=True
    )
    setup(script_args=["build_ext", "--inplace"], ext_modules=ext_modules)
    console.print("[bold green]✅ Compilation complete![/]")

def build_wheel_and_install():
    console.print("[blue]📦 Building wheel...[/]")
    subprocess.run([sys.executable, "-m", "build", "--wheel"], check=True)
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        console.print("[red]❌ No wheel found in dist folder![/]")
        return
    wheel_path = str(sorted(wheel_files)[-1])
    console.print(f"[green]🚀 Installing {wheel_path} via pip...[/]")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", wheel_path], check=True)
    console.print("[bold green]✅ Wheel installed successfully![/]")

def clean_output(clean_name: str):
    console.print(f"[red]🧹 Cleaning output for '{clean_name}'...[/]")
    root = Path(".").resolve()

    # Remove build and cython_cache
    if Path("build").exists():
        shutil.rmtree("build", ignore_errors=True)
    if Path("cython_cache").exists():
        shutil.rmtree("cython_cache", ignore_errors=True)

    # Remove *.so/*.pyd in root except folder named clean_name
    for f in root.glob("*"):
        if f.is_file() and f.suffix in [".so", ".pyd"]:
            f.unlink(missing_ok=True)

    # Remove any parent folder containing a subfolder named clean_name but keep clean_name folder
    for folder in root.glob(f"**/{clean_name}"):
        if folder.is_dir() and folder.name == clean_name:
            parent = folder.parent
            for item in parent.iterdir():
                if item != folder:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)

    console.print(f"[bold green]✅ Cleaned output related to '{clean_name}'[/]")

def cythonize_library(lib_name: str):
    spec = importlib.util.find_spec(lib_name)
    if not spec or not spec.origin:
        console.print(f"[red]❌ Library {lib_name} not found![/]")
        return
    src_path = Path(spec.origin).parent
    tmp_dir = Path(".cython_tmp") / lib_name
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[magenta]📂 Copying {lib_name} sources to temporary folder...[/]")
    shutil.copytree(src_path, tmp_dir, dirs_exist_ok=True)
    build(str(tmp_dir), str(tmp_dir / "build"))
    os.chdir(tmp_dir)
    build_wheel_and_install()
    os.chdir("../../")
    shutil.rmtree(tmp_dir)
    console.print(f"[bold green]🚀 {lib_name} fully Cythonized and reinstalled![/]")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="🚀 Ultimate Auto-Cythonizer CLI")
    parser.add_argument("-t", "--target", help="📂 Target folder")
    parser.add_argument("-o", "--output", default="build_lib", help="📦 Output directory")
    parser.add_argument("-i", "--install", action="store_true", help="⚙️ Build wheel and install")
    parser.add_argument("-l", "--lib", help="🌟 Name of installed library to auto-Cythonize")
    parser.add_argument("-c", "--clean", help="🧹 Clean output related to the given name")
    args = parser.parse_args()

    if args.clean:
        clean_output(args.clean)
    elif args.lib:
        cythonize_library(args.lib)
    elif args.target:
        build(args.target, args.output)
        if args.install:
            build_wheel_and_install()
    else:
        console.print("[red]❌ Please provide --target, --lib or --clean[/]")

if __name__ == "__main__":
    main()
    