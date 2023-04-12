import re
from pprint import pprint
from VarGenerator import VarGenerator
from z3 import *
from hashlib import sha3_256


class Memory:
    def __init__(self, size):
        self.data = bytearray(size)

    def read(self, offset, size):
        return self.data[offset: offset+size]

    def write(self, offset, data):
        if offset + len(data) > len(self.data):
            # 扩展内存
            new_size = max(offset + len(data), 2 * len(self.data))
            new_data = bytearray(new_size)
            new_data[:len(self.data)] = self.data
            self.data = new_data
        # 写入数据
        self.data[offset: offset+len(data)] = data

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value


class SymExec:
    def __init__(self, basic_blocks):
        self.basic_blocks = basic_blocks
        self.stack = []
        self.memory = Memory(128)  # 初始化memory大小
        self.storage = {}  # 初始化storage为空字典
        self.call_data = bytearray()
        self.varGenerator = VarGenerator()
        self.pc = 0
        self.current_block = self.basic_blocks[0]

    def full_execution(self):
        self.execute_block(self.current_block, self.stack)

    def execute_block(self, block, stack):
        print(block.start_address)
        self.current_block = block
        self.stack = stack
        pprint(block.instructions)
        for instruction in block.instructions:
            self.execute_instruction(instruction)
            print(self.stack)
            # print(self.memory.data)

    def execute_instruction(self, instruction):
        if instruction.startswith('PUSH'):
            value = instruction.split()[1]
            self.stack.insert(0, value)
            self.pc += 1 + int(instruction.split()[0][4:])
        elif instruction == 'JUMP':
            jumpdest = int(self.stack.pop(0), 16)
            self.current_block.jump_to = jumpdest
            self.pc += 1
            stack = self.stack
            current_block = self.current_block
            for block in self.basic_blocks:
                if block.start_address == current_block.jump_to:
                    self.execute_block(block, stack)
        elif instruction == 'JUMPI':
            jumpdest = int(self.stack.pop(0), 16)
            condition = self.stack.pop(0)
            self.current_block.jump_to = jumpdest
            self.pc += 1
            stack = self.stack
            current_block = self.current_block
            for block in self.basic_blocks:
                if block.start_address == current_block.fall_to and block.start_address != current_block.start_address:
                    self.execute_block(block, stack)
                elif block.start_address == current_block.jump_to:
                    self.execute_block(block, stack)
        elif instruction == 'JUMPDEST':
            self.pc += 1
        elif instruction == 'MSTORE':
            offset = self.stack.pop(0)
            value = self.stack.pop(0)
            value_bytes = bytes.fromhex(value[2:].zfill(64))
            self.memory.write(int(offset, 16), value_bytes)
            self.pc += 1
        elif instruction == 'MSTORE8':
            offset = int(self.stack.pop(0), 16)
            value = self.stack.pop(0)
            self.memory.write(offset, bytes.fromhex(value.zfill(2)))
            self.pc += 1
        elif instruction == 'CALLDATASIZE':
            self.stack.insert(0, self.varGenerator.gen_data())
            self.pc += 1
        elif instruction == 'CALLDATALOAD':
            value = self.stack.pop(0)
            if value.startswith('0x'):
                offset = int(value, 16)
                size = 32
                data = self.call_data[offset: offset + size]
                value = int.from_bytes(data, byteorder='big')
                self.stack.insert(0, hex(value))
            else:
                self.stack.insert(0, self.varGenerator.gen_data())
            self.pc += 1
        elif instruction == 'LT':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = '0x01' if int(value1, 16) < int(value2, 16) else '0x00'
            else:
                left = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                right = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = If(ULT(left, right), BitVecVal(1, 256), BitVecVal(0, 256))
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'GT':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = '0x01' if int(value1, 16) > int(value2, 16) else '0x00'
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = If(UGT(value1, value2), BitVecVal(1, 256), BitVecVal(0, 256))
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction.startswith("SWAP"):
            num = int(instruction.split()[0][4:])
            temp_stack = []
            for _ in range(num + 1):
                temp_stack.insert(0, self.stack.pop(0))
            temp_stack[0], temp_stack[-1] = temp_stack[-1], temp_stack[0]
            for value in temp_stack:
                self.stack.insert(0, value)
            self.pc += 1
        elif instruction.startswith("DUP"):
            num = int(instruction.split()[0][3:])
            temp_stack = []
            for _ in range(num):
                temp_stack.insert(0, self.stack.pop(0))
            temp_stack.append(temp_stack[0])
            temp_stack = temp_stack[::-1]
            for value in temp_stack:
                self.stack.insert(0, value)
            self.pc += 1
        elif instruction.startswith('LOG'):
            num_topics = int(instruction[3])
            offset = self.stack.pop(0)
            size = self.stack.pop(0)
            data = self.memory.read(int(offset, 16), int(size, 16))
            topics = [self.stack.pop(0) for _ in range(num_topics)]

            # # 记录日志信息
            # log_data = data.hex()
            # for topic in topics:
            #     if topic.startswith('0x'):
            #         log_data += topic[2:].zfill(64)
            #     else:
            #         log_data += self.varGenerator.gen_data()[2:].zfill(64)
            # print(f'LOG data: {log_data}')
            self.pc += 1
        elif instruction == 'STOP':
            # self.pc += 1
            return
        elif instruction == 'ADD':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) + int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = value1 + value2
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'SUB':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) - int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = simplify(value1 - value2)
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'MUL':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) * int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = value1 * value2
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'DIV':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) // int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = value1 // value2
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'SDIV':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex((int(value1, 16) // int(value2, 16)))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = If(value2 == 0, BitVecVal(0, 256), value1 / value2)
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'MOD':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) % int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = If(value2 == 0, BitVecVal(0, 256), value1 % value2)
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'SMOD':  # 带符号求模
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(
                    (int(value1, 16) % int(value2, 16)) - (int(value1, 16) // int(value2, 16)) * int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = If(value2 == 0, BitVecVal(0, 256),
                              value1 % value2 - If(value1 < 0, If(value2 > 0, value2, -value2), 0))
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'ADDMOD':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            value3 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x') and value3.startswith('0x'):
                computed = hex((int(value1, 16) + int(value2, 16)) % int(value3, 16))
            else:
                left = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                right = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                mod = int(value3, 16) if value3.startswith('0x') else BitVec(value3, 256)
                computed = (left + right) % mod
                if isinstance(computed, z3.BitVecRef):
                    computed = z3.simplify(computed)
                    if computed.size() > 256:
                        computed = z3.Extract(255, 0, computed)
                computed = hex(computed)
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'EXP':
            exponent = self.stack.pop(0)
            base = self.stack.pop(0)
            if base.startswith('0x') and exponent.startswith('0x'):
                result = hex(pow(int(base, 16), int(exponent, 16)))
            else:
                base = int(base, 16) if base.startswith('0x') else BitVec(base, 256)
                exponent = int(exponent, 16) if exponent.startswith('0x') else BitVec(exponent, 256)
                result = simplify(pow(base, exponent))
            self.stack.insert(0, result)
            self.pc += 1
        elif instruction == 'SIGNEXTEND':  # gpt生成的
            size = int(self.stack.pop(0), 16)
            value = self.stack.pop(0)
            if value.startswith('0x'):
                value = int(value, 16)
            else:
                value = BitVec(value, 256)
            sign_bit = value & (1 << (size * 8 - 1))
            mask = (1 << (256 - size * 8)) - 1
            mask = BitVecVal(mask, 256)
            sign_bits = sign_bit * ((1 << (256 - size * 8)) - 1)
            sign_bits = BitVecVal(sign_bits, 256)
            result = (value & mask) | sign_bits
            self.stack.insert(0, hex(result))
            self.pc += 1
        elif instruction == 'EQ':  # 是否相等
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = '0x01' if int(value1, 16) == int(value2, 16) else '0x00'
            else:
                left = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                right = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = If(left == right, BitVecVal(1, 256), BitVecVal(0, 256))
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'AND':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) & int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = value1 & value2
                if isinstance(computed, BitVecRef):
                    computed = simplify(computed)
                    computed = hex(int(str(computed), 10))
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'OR':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) | int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = value1 | value2
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'XOR':
            value1 = self.stack.pop(0)
            value2 = self.stack.pop(0)
            if value1.startswith('0x') and value2.startswith('0x'):
                computed = hex(int(value1, 16) ^ int(value2, 16))
            else:
                value1 = int(value1, 16) if value1.startswith('0x') else BitVec(value1, 256)
                value2 = int(value2, 16) if value2.startswith('0x') else BitVec(value2, 256)
                computed = value1 ^ value2
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'NOT':
            value = self.stack.pop(0)
            if value.startswith('0x'):
                computed = hex((int(value, 16) ^ 0xFFFFFFFFFFFFFFFF))
            else:
                value = int(value, 16) if value.startswith('0x') else BitVec(value, 256)
                computed = value ^ BitVecVal(0xFFFFFFFFFFFFFFFF, 256)
            self.stack.insert(0, computed)
            self.pc += 1
        elif instruction == 'SHA3':
            value = self.stack.pop(0)
            if value.startswith('0x'):
                offset = int(value, 16)
                size = len(self.stack[0]) // 2
                data = self.memory.read(offset, size)
                computed = sha3_256(data).hexdigest()
                self.stack[0] = '0x' + computed
            else:
                self.stack.insert(0, self.varGenerator.gen_data())
            self.pc += 1
        elif instruction == 'SLOAD':
            key = self.stack.pop(0)
            if key.startswith('0x'):
                key = int(key, 16)
            else:
                key = BitVec(key, 256)
            if key in self.storage:
                value = self.storage[key]
            else:
                value = self.varGenerator.gen_data()
                self.storage[key] = value
            self.stack.insert(0, value)
            self.pc += 1
        elif instruction == 'SSTORE':
            key = self.stack.pop(0)
            value = self.stack.pop(0)
            if key.startswith('0x') and value.startswith('0x'):
                self.storage[int(key, 16)] = int(value, 16)
            else:
                key = BitVec(key, 256)
                value = BitVec(value, 256)
                self.storage[key] = value
            self.pc += 1
        elif instruction == 'CALLVALUE':
            self.stack.insert(0, self.varGenerator.gen_data())
            self.pc += 1
        elif instruction == 'CALLER':
            self.stack.insert(0, self.varGenerator.gen_address())
            self.pc += 1
        elif instruction == 'BALANCE':
            address = self.stack.pop(0)
            balance = self.storage.get(address, 0)
            self.stack.insert(0, balance)
            self.pc += 1
        elif instruction == 'GASPRICE':
            self.stack.insert(0, self.varGenerator.gen_data())
            self.pc += 1
        elif instruction == 'POP':
            num = int(instruction.split()[0][1])
            for _ in range(num):
                self.stack.pop(0)
            self.pc += 1
