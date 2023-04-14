from pprint import pprint
from PreProcess import PreProcess
from CFGBuilder import CFGBuilder
from SymExec import SymExec


if __name__ == '__main__':
    preProcess = PreProcess('case1.sol')
    bytecode = preProcess.compile_solidity()
    assembly = preProcess.bytecode_to_assembly()
    CFG = CFGBuilder(preProcess.disasm_filename)
    symExec = SymExec(CFG.basic_blocks)
    # print(symExec)
    symExec.full_execution()
    symExec.draw_graph()
    # print(CFG.__str__())
    # pprint(CFG.basic_blocks[0].__str__())
    # pprint(CFG.instructions)
