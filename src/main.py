from c_benchmark import Benchmark


def main():
    path = "/home/plebeiandev/Documents/Benchmarks/Bookshelf_ISPD/ibm01"
    d = Benchmark(path)
    d.generate_benchmark()
    print(d)

if __name__ == "__main__":
    main()