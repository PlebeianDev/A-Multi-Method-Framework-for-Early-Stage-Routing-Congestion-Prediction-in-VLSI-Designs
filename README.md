# A Multi-Method Framework for Early-Stage Routing Congestion Prediction in VLSI Designs


A unified, open-source Python framework for early-stage routing congestion prediction in VLSI designs. This tool integrates four complementary congestion estimation techniques and provides quantitative metrics, comparative visualizations, and statistical validation to assess congestion risk before detailed routing.

## Features

- Supports ISPD Bookshelf-format benchmarks
- Implements four congestion estimation methods:
  - Pin-density-based
  - Fanout-aware (log-weighted)
  - Rent’s Rule-based
  - Net-span (Manhattan distance)
- Modular, extensible architecture for research and production use
- Generates heatmaps and CSV reports for all methods
- Statistical analysis and correlation of congestion metrics

## Installation

1. Clone the repository:
	```sh
	git clone https://github.com/<your-username>/Routing-Congestion-Prediction.git
	cd Routing-Congestion-Prediction
	```

2. Install dependencies:
	```sh
	pip install -r requirements.txt
	```

## Usage

1. Benchmarks are not provided, as such you need to provide your benchmarks in Bookshelf Format. Place them on any directory you wish.
2. Run the main script:
	```sh
	python src/main.py
	```
	(Adjust the entry point and arguments as needed for your setup. Set the value of **path** variable under **main**, pointing to your benchmark design)

3. Outputs:
	- Congestion heatmaps (PNG)
	- Metrics and correlation CSVs
	- Log files with timestamps

## Example

```python
from src.c_benchmark import Benchmark
from src.congestion_funcs import CongestionEstimator, CongestionVisualizer

bench = Benchmark('logs/ibm01')
bench.generate_benchmark()

estimator = CongestionEstimator(bench, grid_size=10)
congestion_maps = estimator.generate_all_congestion_maps()

visualizer = CongestionVisualizer(bench)
visualizer.plot_4way_comparison(congestion_maps)
```

## Citing

If you use this framework in your research, please cite:

```
TBA
```

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 2. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Based on the methodology and results described in our academic paper.
- Uses ISPD benchmark datasets and open-source Python libraries.
