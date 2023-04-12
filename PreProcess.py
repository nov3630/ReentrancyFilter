import subprocess
import re


class PreProcess:
    def __init__(self, filename):
        self.filename = filename
        self.bytecode = ''
        self.bytecode_filename = f'{self.filename}.bin.runtime'
        self.disasm = ''
        self.disasm_filename = f'{self.filename}.disasm'

    # Compile Solidity code and get the bytecode
    def compile_solidity(self):
        # Compile Solidity code to get and bytecode
        proc = subprocess.run(['solc', '--bin-runtime', self.filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Get the bytecode from the compiled output
        output = proc.stdout.decode('utf-8').strip().split()
        bytecode = output[-1]

        # remove the hash part
        bytecode = re.sub(r"a165627a7a72305820\S{64}0029$", "", bytecode)

        with open(self.bytecode_filename, 'w', encoding='utf-8') as f:
            f.write(bytecode)

        self.bytecode = bytecode
        return bytecode

    def bytecode_to_assembly(self):
        proc = subprocess.run(['evm', 'disasm', self.bytecode_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        disasm = proc.stdout.decode('utf-8').strip().split('\n')[1:]

        with open(self.disasm_filename, 'w', encoding='utf-8') as f:
            for line in disasm:
                f.write(line + '\n')

        self.disasm = disasm
        return disasm