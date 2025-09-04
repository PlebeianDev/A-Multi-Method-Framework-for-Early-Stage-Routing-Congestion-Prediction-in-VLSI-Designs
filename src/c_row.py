class Row:
    """
    Represents a row in a VLSI design, containing placement and cell information.
    Provides methods to generate row attributes and calculate density.
    """
    counter = -1

    def __init__(self):
        """
        Initialize a Row object with default attributes.
        """
        Row.counter += 1
        self.id = Row.counter

        self.ly = None  # corerow
        self.hy = None
        self.lx = None  # subroworigin
        self.rx = None  # = subroworigin + numsites * sitespacing
        self.h = None
        self.sitespacing = None
        self.numsites = None
        self.density = None

        self.cells = []

    def generate_row(self, fl: list, cells_list: list):
        """
        Populate the row's attributes from parsed file data and assign cells to the row.
        Args:
            fl (list): List of row attributes (coordinates, height, spacing, etc.).
            cells_list (list): List of all cell objects in the design.
        """
        self.ly = fl[0]
        self.h = fl[1]
        self.sitespacing = fl[2]
        self.lx = fl[3]
        self.numsites = fl[4]

        self.hy = self.ly + self.h
        self.rx = self.lx + self.numsites * self.sitespacing

        self.find_cells(cells_list)
        self.calculate_density()

    def find_cells(self, cells: list):
        """
        Find and assign cells that belong to this row based on y-coordinate.
        Args:
            cells (list): List of all cell objects in the design.
        """
        for cell in cells:
            if cell.ly == self.ly:
                self.cells.append(cell)
        # Keep them sorted in ascending left x
        self.cells.sort(key=lambda c:c.lx)

    def calculate_density(self):
        """
        Calculate the density of the row as the ratio of cell area to row area.
        """
        cells_area = 0.0
        for c in self.cells:
            cells_area += c.w
        self.density = cells_area / (self.rx - self.lx)