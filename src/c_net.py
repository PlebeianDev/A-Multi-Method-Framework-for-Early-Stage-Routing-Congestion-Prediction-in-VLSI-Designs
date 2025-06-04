

class Net:
    counter = -1
    def __init__(self):
        Net.counter += 1
        self.id = Net.counter

        self.name = None
        self.cells = {}
        self.netdegree = None
        self.lx = None
        self.ly = None
        self.rx = None
        self.hy = None
        self.hpwl = 0.0

    def calculate_hpwl(self):
        self.lx = min(cell.lx for cell in self.cells.values())
        self.rx = max(cell.rx for cell in self.cells.values())
        self.ly = min(cell.ly for cell in self.cells.values())
        self.hy = max(cell.hy for cell in self.cells.values())

        self.hpwl = (self.rx - self.lx) + (self.hy - self.ly)

    def calculate_hpwl_impact(self):
        # Same as calculate_hpwl() but does not change the value of attribute
        lx = min(cell.lx for cell in self.cells.values())
        rx = max(cell.rx for cell in self.cells.values())
        ly = min(cell.ly for cell in self.cells.values())
        hy = max(cell.hy for cell in self.cells.values())

        return (rx - lx) + (hy - ly)

    def generate_net(self, name: str, cells_file: list, cells_bench: dict):
        self.name = name
        for cname in cells_file:
            self.cells[cname] = cells_bench[cname]
            # Also update the corresponding cell's net dict
            cells_bench[cname].nets[self.name] = self

        self.calculate_hpwl()
        self.netdegree = len(self.cells.keys())
