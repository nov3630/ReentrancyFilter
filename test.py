from z3 import *

if __name__ == '__main__':
    path_condition = [Id_1 <= Iv, init_Is >= Iv, 0 <= Id_1, Not(If(ULE(4, Id_size), 0, 1) != 0), Not(If(Extract(255, 224, Id_1) == 8527331, 1, 0) != 0), If(Extract(255, 224, Id_1) == 1805620970, 1, 0) != 0, If(Iv == 0, 1, 0) != 0]
    solver = Solver()
    solver.add(path_condition)
    res = solver.check()
    print(type(res))
    print(res == sat)
