import time
from rich.console import Console
from rich.table import Table

import demo.demo as py_demo
import build_demo.demo as cy_demo # pyright: ignore[reportMissingImports]

ITERATIONS = 50_000  # adjust for ~5 min in Python

console = Console()

def benchmark(func, n, label):
    start = time.time()
    result = func(n)
    end = time.time()
    return end-start, result

table = Table(title="Python vs Cython Benchmark")
table.add_column("Version")
table.add_column("Time (s)")
table.add_column("Result Checksum")

py_time, py_result = benchmark(py_demo.heavy_loop, ITERATIONS, "Python")
cy_time, cy_result = benchmark(cy_demo.heavy_loop, ITERATIONS, "Cython")

table.add_row("Pure Python", f"{py_time:.4f}", f"{py_result:.4f}")
table.add_row("Cython", f"{cy_time:.4f}", f"{cy_result:.4f}")

console.print(table)
