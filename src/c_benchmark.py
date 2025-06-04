from c_file_parser import FParser
from c_row import Row
from c_cell import Cell
from c_net import Net


class Benchmark:
    counter = -1

    def __init__(self, folder_path: str):
        Benchmark.counter += 1
        self.id = Benchmark.counter

        self.fp = FParser(folder_path)
        self.folder_path = folder_path
        self.name = self.folder_path.split('/')[-1]

        self.ly = None
        self.lx = None
        self.hy = None
        self.rx = None
        self.h = None
        self.w = None
        self.density = None
        self.area = None
        self.hpwl = 0.0

        self.cells = {}
        self.pins = {}
        self.macros = {}
        self.nets = {}
        self.rows = []

    def __str__(self):
        print(f'Design: {self.name}')
        print(f'ly:{self.ly} lx:{self.lx} hy:{self.hy} rx:{self.rx}')
        print(f'width:{self.w} height:{self.h}')
        print(f'HWPL:{self.hpwl}')
        return ""

    def generate_benchmark(self):
        self.generate_cells()
        self.generate_rows()
        self.generate_nets()
        self.calculate_benchmark_attributes()
        self.categorize_cells()
        self.calculate_cells_to_pins_connections()
        # self.calculate_cells_levels()

    def calculate_benchmark_attributes(self):
        self.lx = min(row.lx for row in self.rows)
        self.rx = max(row.rx for row in self.rows)
        self.ly = min(row.ly for row in self.rows)
        self.hy = max(row.hy for row in self.rows)

        self.w = self.rx - self.lx
        self.h = self.hy - self.ly

        self.calculate_density()
        self.calculate_hpwl()

    def calculate_density(self):
        d = 0.0
        for row in self.rows:
            d += row.density
        self.density = d / len(self.rows)

    def calculate_hpwl(self):
        for net in self.nets.values():
            self.hpwl += net.hpwl

    def generate_cells(self):
        cells = self.fp.read_cells()
        for cell_name in cells.keys():
            cell = Cell()
            cell.generate_cell(cell_name, cells[cell_name])
            self.cells[cell_name] = cell
        del cells

    def categorize_cells(self):
        # Must be called after rows and the calculation of die area edges
        for cell in self.cells.values():
            if cell.movetype == "terminal":
                if self.ly <= cell.ly <= self.hy and self.lx <= cell.lx <= self.rx:
                    cell.macro = True
                    self.macros[cell.name] = cell
                else:
                    cell.pin = True
                    self.pins[cell.name] = cell
                # For now do not delete the entry from cells dict, helps with nets
                # del self.cells[cell.name]

    def calculate_cells_levels(self):
        queue = []
        # Pins = lvl 0
        for pin in self.pins.values():
            pin.lvl = 0
            queue.append(pin)

        # BFS
        while queue:
            curr_cell = queue.pop(0)
            curr_lvl = curr_cell.lvl

            for net in curr_cell.nets.values():
                for cell in net.cells.values():
                    if cell.lvl is None:
                        cell.lvl = curr_lvl + 1
                        queue.append(cell)

    def generate_rows(self):
        rows = self.fp.read_rows()
        for row_name in rows.keys():
            row = Row()
            row.generate_row(rows[row_name], list(self.cells.values()))
            self.rows.append(row)
        del rows

    def generate_nets(self):
        nets = self.fp.read_nets()
        for net_name in nets.keys():
            net = Net()
            net.generate_net(net_name, nets[net_name], self.cells)
            self.nets[net_name] = net
        del nets

    def calculate_cells_to_pins_connections(self):
        for net in self.nets.values():
            pin_counter = 0
            for cell in net.cells.values():
                if cell.pin:
                    pin_counter += 1
            for cell in net.cells.values():
                if cell.pin:
                    continue
                cell.pin_counter += pin_counter