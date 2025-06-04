import time
import numpy as np

from c_benchmark import Benchmark


class CongestionEstimator:
    def __init__(self, d: Benchmark, grid_size=10):
        self.design = d
        self.grid_size = grid_size
        self.routing_grid = None
        self.congestion_maps = {}
        self.runtimes = {}

    def build_routing_grid(self):
        """Create a routing grid over the die area"""

        x_bins = int((self.design.rx - self.design.lx) / self.grid_size) + 1
        y_bins = int((self.design.hy - self.design.ly) / self.grid_size) + 1

        self.routing_grid = {
            'x_bins': x_bins,
            'y_bins': y_bins,
            'grid_size':self.grid_size,
            'min_x': self.design.lx,
            'min_y': self.design.ly,
            'cells': [[{
                'pin_density': 0,
                'net_demand_standard': 0,
                'net_demand_weighted': 0,
                'rent_demand': 0,
                'span_demand': 0
            } for _ in range(y_bins)] for _ in range(x_bins)]
        }

    def calculate_pin_density(self):
        """Calculate pin density for each grid cell"""
        if not self.routing_grid:
            self.build_routing_grid()

        for cell in self.design.cells.values():
            if cell.macro or cell.pin:
                continue

            min_col = int((cell.lx - self.routing_grid['min_x']) / self.grid_size)
            max_col = int((cell.lx + cell.w - self.routing_grid['min_x']) / self.grid_size)
            min_row = int((cell.ly - self.routing_grid['min_y']) / self.grid_size)
            max_row = int((cell.ly + cell.h - self.routing_grid['min_y']) / self.grid_size)

            overlapping_cells = (max_col - min_col + 1) * (max_row - min_row + 1)
            if overlapping_cells > 0:
                pins_per_cell = cell.pin_counter / overlapping_cells
                for col in range(min_col, max_col + 1):
                    for row in range(min_row, max_row + 1):
                        self.routing_grid['cells'][col][row]['pin_density'] += pins_per_cell

    def _process_net_demand(self, net, weight, demand_key):
        """Helper method to process net demand"""
        if not net.cells:
            return

        min_col = int((net.lx - self.routing_grid['min_x']) / self.grid_size)
        max_col = int((net.rx - self.routing_grid['min_x']) / self.grid_size)
        min_row = int((net.ly - self.routing_grid['min_y']) / self.grid_size)
        max_row = int((net.hy - self.routing_grid['min_y']) / self.grid_size)

        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                self.routing_grid['cells'][col][row][demand_key] += weight

    def estimate_net_demand_standard(self):
        """Original method: all nets contribute equally"""
        start_time = time.time()
        if not self.routing_grid:
            self.build_routing_grid()
        for net in self.design.nets.values():
            self._process_net_demand(net, weight=1.0, demand_key='net_demand_standard')
        self.runtimes['standard'] = time.time() - start_time

    def estimate_net_demand_weighted(self):
        """Weight nets by fanout (log scale)"""
        start_time = time.time()
        if not self.routing_grid:
            self.build_routing_grid()
        for net in self.design.nets.values():
            fanout = len(net.cells.keys())
            weight = np.log1p(fanout)  # log(1 + fanout)
            self._process_net_demand(net, weight, 'net_demand_weighted')
        self.runtimes['weighted'] = time.time() - start_time

    def estimate_rents_rule(self):
        start_time = time.time()
        if not self.routing_grid:
            self.build_routing_grid()

        k = 0.5  # Average interconnects per cell
        p = 0.6  # Rent exponent

        for cell in self.design.cells.values():
            connected_nets = cell.nets.values()
            fanout = len(connected_nets)
            wiring_demand = k * (fanout ** p)

            col = int((cell.lx - self.routing_grid['min_x']) / self.grid_size)
            row = int((cell.ly - self.routing_grid['min_y']) / self.grid_size)

            if 0 <= col < self.routing_grid['x_bins'] and 0 <= row < self.routing_grid['y_bins']:
                self.routing_grid['cells'][col][row]['rent_demand'] += wiring_demand

        self.runtimes['rents'] = time.time() - start_time

    def estimate_net_span(self):
        """Net span-based congestion estimation"""
        start_time = time.time()
        if not self.routing_grid:
            self.build_routing_grid()

        for net in self.design.nets.values():
            span = (net.rx - net.lx) + (net.hy - net.ly)  # Manhattan span

            min_col = int((net.lx - self.routing_grid['min_x']) / self.grid_size)
            max_col = int((net.rx - self.routing_grid['min_x']) / self.grid_size)
            min_row = int((net.ly - self.routing_grid['min_y']) / self.grid_size)
            max_row = int((net.hy - self.routing_grid['min_y']) / self.grid_size)

            for col in range(min_col, max_col + 1):
                for row in range(min_row, max_row + 1):
                    self.routing_grid['cells'][col][row]['span_demand'] += span / self.grid_size
        self.runtimes['span'] = time.time() - start_time

    def generate_all_congestion_maps(self):
        """Generate congestion maps for all methods with proper normalization"""
        self.calculate_pin_density()
        self.estimate_net_demand_standard()
        self.estimate_net_demand_weighted()
        self.estimate_rents_rule()
        self.estimate_net_span()

        # Calculate max values for normalization
        max_values = {
            'pin': max(c['pin_density'] for row in self.routing_grid['cells'] for c in row) or 1,
            'standard': 
        }