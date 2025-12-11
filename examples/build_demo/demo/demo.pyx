# cimport cython
# @boundscheck(False)
# @wraparound(False)
# @nonecheck(False)
# @cdivision(True)
def heavy_loop(n):
    total = 0.0
    # cdef int i (annotated)
    for i in range(n):
        # cdef int j (annotated)
        for j in range(50):
            total += i*j + i+j  # all arithmetic, no Python functions
    return total