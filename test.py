from z3 import *
import six

if __name__ == '__main__':
    # path_condition = []
    # solver = Solver()
    # solver.add(path_condition)
    # res = solver.check()
    # print(type(res))
    # print(res == sat)
    x = isinstance(BitVec('0x01', 256), str)
    x = hex(int('0x05', 16) - int('0x02', 16))
    print(int(x, 16) == int('0x03', 16), type(x))
