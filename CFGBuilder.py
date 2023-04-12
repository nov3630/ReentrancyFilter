class BasicBlock:
    def __init__(self):
        self.start_address = ''
        self.end_address = ''
        self.instructions = []
        self.type = ''
        self.fall_to = ''
        self.jump_to = ''

class CFGBuilder:
    def __init__(self, disasm_file):
        self.disasm_file = disasm_file
        self.end_opcodes = ['STOP', 'JUMP', 'JUMPI', 'RETURN', 'SUICIDE', 'REVERT', 'ASSERTFAIL']
        self.basic_blocks = []
        self.start_address = None
        self.end_address = None
        self.jump_targets = {}
        self.instructions = {}

        self.get_blocks()
        self.add_fall_to()

    def get_blocks(self):
        # Parse the disasm file
        with open(self.disasm_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                address, instruction = line.strip().split(': ')
                address = int(address, 16)
                self.instructions[address] = instruction

        # Find the start and end addresses
        self.start_address = min(self.instructions.keys())
        self.end_address = max(self.instructions.keys())

        current_block = BasicBlock()
        for address, instruction in self.instructions.items():
            if current_block.start_address == '':
                current_block.start_address = address
            current_block.instructions.append(self.instructions[address])

            if instruction in self.end_opcodes:
                current_block.end_address = address
                if instruction == 'JUMPI':
                    current_block.type = 'conditional'
                self.basic_blocks.append(current_block)
                if address != self.end_address:
                    current_block = BasicBlock()

    def add_fall_to(self):
        for i in range(len(self.basic_blocks)):
            if self.basic_blocks[i].type == 'conditional':
                self.basic_blocks[i].fall_to = self.basic_blocks[i+1].start_address

    def __str__(self):
        result = ''
        for block in self.basic_blocks:
            result += f'Block {block.start_address} => {block.end_address}:\n'
            for instruction in block.instructions:
                result += '\t' + instruction + '\n'
        return result
