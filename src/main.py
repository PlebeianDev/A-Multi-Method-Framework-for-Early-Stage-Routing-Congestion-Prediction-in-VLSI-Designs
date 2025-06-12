# Packages
import os

# Project imports
from c_benchmark import Benchmark
from congestion_funcs import *


def main():
    path = "/home/plebeiandev/Documents/Benchmarks/Bookshelf_ISPD/adaptec3_eplace_placed_and_legalized"
    d = Benchmark(path)
    d.generate_benchmark()
    
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = setup_logging(log_dir)
    print(f'Design: {d.name}')

    try:
        estimator = CongestionEstimator(d, grid_size=500)
        print('Calculating congestion maps...')
        congestion_maps = estimator.generate_all_congestion_maps()

        visualizer = CongestionVisualizer(d)
        print('Generating visualizations...')
        visualizer.plot_4way_comparison(congestion_maps)

        analyzer = CongestionAnalyzer(congestion_maps, estimator.runtimes)
        report = analyzer.generate_comparison_report()
        
        print("\n=== Method Comparison Metrics ===")
        print(report['metrics'].to_string())  # to_string() for better formatting
        
        print("\n=== Correlation Between Methods ===")
        print(report['correlation'].to_string())

        # Get cells where methods disagree most
        std_vals = np.array([c['congestion'] for row in congestion_maps['standard']['cells'] for c in row])
        rent_vals = np.array([c['congestion'] for row in congestion_maps['rents']['cells'] for c in row])
        divergence = np.abs(std_vals - rent_vals)
        top_divergence_indices = np.argsort(divergence)[-100:]  # Top 10 differing cells

        print("\n=== Top 10 Divergence Locations ===")
        print(top_divergence_indices)
        
        # Save reports to files
        report['metrics'].to_csv(f"{log_dir}/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        report['correlation'].to_csv(f"{log_dir}/correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        print(f"\nAnalysis complete. Logs saved to: {log_file}")
    
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        raise

    finally:
        # Ensure all output is flushed to the log file
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

if __name__ == "__main__":
    main()