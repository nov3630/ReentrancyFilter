from z3 import *


class VarGenerator:
    def __init__(self):
        self.data_count = 0
        self.address_count = 0
        self.memory_count = 0
        self.storage_count = 0
        self.gas_count = 0
        self.balance_count = 0

    def gen_data(self):
        self.data_count += 1
        return BitVec(f'data_{self.data_count}', 256)

    def gen_address(self):
        self.address_count += 1
        return BitVec(f'address_{self.address_count}', 256)

    def gen_memory(self):
        self.memory_count += 1
        return BitVec(f'memory_{self.memory_count}', 256)

    def gen_storage(self):
        self.storage_count += 1
        return BitVec(f'storage_{self.storage_count}', 256)

    def gen_gas(self):
        self.gas_count += 1
        return BitVec(f'gas_{self.gas_count}', 256)

    def gen_balance(self):
        self.balance_count += 1
        return BitVec(f'balance_{self.balance_count}', 256)
