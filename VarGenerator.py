class VarGenerator:
    def __init__(self):
        self.data_count = 0
        self.address_count = 0

    def gen_data(self):
        self.data_count += 1
        return f'data_{self.data_count}'

    def gen_address(self):
        self.data_count += 1
        return f'address_{self.data_count}'