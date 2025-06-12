import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from datetime import datetime
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import pearsonr

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
            'standard': max(c['net_demand_standard'] for row in self.routing_grid['cells'] for c in row) or 1,
            'weighted': max(c['net_demand_weighted'] for row in self.routing_grid['cells'] for c in row) or 1,
            'rents': max(c['rent_demand'] for row in self.routing_grid['cells'] for c in row) or 1,
            'span': max(c['span_demand'] for row in self.routing_grid['cells'] for c in row) or 1
        }

        methods = {
            'standard': 'net_demand_standard',
            'weighted': 'net_demand_weighted',
            'rents': 'rent_demand',
            'span': 'span_demand'
        }

        """
        TODOS: 
        1. see if the fix values must be altered later for experimentation
        2. Might provide error, see cells and dictionaries accordingly
        """
        for name, demand_key in methods.items():
            congestion_map = {
                **self.routing_grid,
                'cells':[[{
                    **cell,
                    'congestion': 0.6 * (cell[demand_key] / max_values[name]) +
                                  0.4 * (cell['pin_density'] / max_values['pin'])
                } for cell in row] for row in self.routing_grid['cells']]
            }
            self.congestion_maps[name] = congestion_map
        
        return self.congestion_maps
    

class CongestionVisualizer:
    def __init__(self, design_data):
        self.design = design_data
        self.cmap = LinearSegmentedColormap.from_list(
            'congestion', ['green', 'yellow', 'red']
        )

    def plot_4way_comparison(self, maps):
        """4-way comparison of all methods"""
        plt.figure(figsize=(16,12))
        titles = [
            "Standard (Uniform Nets)",
            "Fanout-Weighted",
            "Rent's Rule",
            "Net Span"
        ]

        for i, (method, title) in enumerate(zip(maps.keys(), titles), 1):
            plt.subplot(2,2,i)
            self._plot_single_map(maps[method])
            plt.title(title)

        plt.tight_layout()
        plt.show()
    
    def _plot_single_map(self, congestion_map):
        """Plot single congestion map"""
        rows = congestion_map['y_bins']
        cols = congestion_map['x_bins']
        data = np.zeros((rows, cols))
        
        for x in range(cols):
            for y in range(rows):
                data[y, x] = congestion_map['cells'][x][y]['congestion']
        
        plt.imshow(data, cmap=self.cmap, aspect='auto',
                  extent=[0, cols*congestion_map['grid_size'], 
                         0, rows*congestion_map['grid_size']],
                  origin='lower', vmin=0, vmax=1)
        plt.colorbar(label='Congestion Level')
        plt.xlabel('X Position (μm)')
        plt.ylabel('Y Position (μm)')
        plt.grid(True, alpha=0.3)

    
class CongestionAnalyzer:
    def __init__(self, congestion_maps, runtimes):
        self.maps = congestion_maps
        self.runtimes = runtimes
    
    def generate_comparison_report(self):
        """Generate comprehensive comparison metrics"""
        metrics = []
        
        for method, cmap in self.maps.items():
            congestion_vals = [c['congestion'] for row in cmap['cells'] for c in row]
            metrics.append({
                'Method': method,
                'Runtime (s)': self.runtimes.get(method, 0),
                'Max Congestion': max(congestion_vals),
                'Mean Congestion': np.mean(congestion_vals),
                'Std Dev': np.std(congestion_vals),
                'Hotspots (>0.8)': sum(c > 0.8 for c in congestion_vals),
                'Hotspots (>0.9)': sum(c > 0.9 for c in congestion_vals)
            })
        
        df = pd.DataFrame(metrics)
        
        # Add correlation matrix
        corr_matrix = np.zeros((len(self.maps), len(self.maps)))
        methods = list(self.maps.keys())
        for i, m1 in enumerate(methods):
            for j, m2 in enumerate(methods):
                vals1 = [c['congestion'] for row in self.maps[m1]['cells'] for c in row]
                vals2 = [c['congestion'] for row in self.maps[m2]['cells'] for c in row]
                corr_matrix[i,j] = pearsonr(vals1, vals2)[0]
        
        corr_df = pd.DataFrame(corr_matrix, index=methods, columns=methods)
        
        return {
            'metrics': df,
            'correlation': corr_df
        }
        
def setup_logging(log_file_path):
    """Redirect stdout and stderr to a log file"""
    class Logger(object):
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "a")

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)

        def flush(self):
            pass

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_file_path}/congestion_analysis_{timestamp}.log"
    
    sys.stdout = Logger(log_file)
    sys.stderr = sys.stdout  # Redirect stderr to the same file
    
    print(f"Logging initialized at {datetime.now()}")
    print(f"Log file: {log_file}")
    return log_file
