from matplotlib import pyplot as plt
from matplotlib import patches

from c_benchmark import Benchmark

class Plotter:
    def __init__(self):
        pass

    @staticmethod
    def plot_design(benchmark: Benchmark):
        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal', adjustable='datalim')
        for p in benchmark.pins.values():
            ax.add_patch(patches.Rectangle((float(p.lx), float(p.ly)), 1.0, 1.0, fill=True))
            ax.plot()
        for cell in benchmark.cells.values():
            ax.add_patch(patches.Rectangle((float(cell.lx), float(cell.ly)), cell.w, cell.h, fill=True,
                                           color="black"))
            ax.plot()
        for row in benchmark.rows:
            ax.add_patch(
                patches.Rectangle((float(row.lx), float(row.ly)), row.rx - row.lx,
                                  row.h, fill=None, color="black"))
            ax.plot()
        ax.add_patch(
            patches.Rectangle((benchmark.lx, benchmark.ly), benchmark.w, benchmark.h, fill=False))
        ax.plot()
        plt.show()