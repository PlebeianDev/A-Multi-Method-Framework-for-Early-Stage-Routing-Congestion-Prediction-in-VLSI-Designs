import os


class FParser:
    def __init__(self, folder_path: str):
        dname = os.path.basename(folder_path)
        self.plfile = f"{folder_path}/{dname}.pl"
        self.nodesfile = f"{folder_path}/{dname}.nodes"
        self.netsfile = f"{folder_path}/{dname}.nets"
        self.sclfile = f"{folder_path}/{dname}.scl"

    def read_cells(self):
        cells = {}

        with open(self.plfile, 'r') as file:
            lines = file.readlines()

        data_lines = [line.strip() for line in lines if not line.startswith('#') and line.strip()]

        for line in data_lines:
            parts = line.split()
            if 'pl' in parts:
                continue
            if len(parts) == 5:
                parts.remove(':')
                name, x, y, orient = parts
                cells[name] = [float(x), float(y), orient]
            elif len(parts) == 3:
                name, x, y = parts
                cells[name] = [float(x), float(y), None]

        with open(self.nodesfile, 'r') as file:
            lines = file.readlines()

        data_lines = [line.strip() for line in lines if not line.startswith('#') and line.strip()]

        numnodes = None
        for line in data_lines:
            parts = line.split()
            if 'NumNodes' in parts:
                numnodes = int(parts[2])
            elif parts[0] in cells.keys():
                dims = [float(parts[1]), float(parts[2])]  # width, height
                cells[parts[0]].extend(dims)
                if len(parts) > 3:
                    cells[parts[0]].append("terminal")

        if numnodes != len(cells.keys()):
            print(cells.keys())
            print(numnodes, len(cells.keys()))
            print(f"Error: number of cells in file, different from extracted data")
            exit(1)

        return cells

    def read_nets(self):
        net_counter = -1
        nets = {}

        flag = False
        with open(self.netsfile, 'r') as file:
            for line in file:
                line = line.split()
                if 'NetDegree' in line:
                    net_counter += 1
                    flag = True
                    nets[f"n{net_counter}"] = []
                elif flag:
                    nets[f"n{net_counter}"].append(line[0])

        return nets

    def read_rows(self):
        rows = {}
        row_count = -1

        with open(self.sclfile) as file:
            for line in file:
                line = line.split()
                if 'CoreRow' in line:
                    row_count += 1
                if 'Coordinate' in line:
                    rows[row_count] = [float(line[2])]  #y
                if 'Height' in line:
                    rows[row_count].append(float(line[2]))  # Height
                if 'Sitespacing' in line:
                    rows[row_count].append(float(line[2]))
                if 'SubrowOrigin' in line:
                    rows[row_count].append(float(line[2]))
                    rows[row_count].append(float(line[5]))

        return rows