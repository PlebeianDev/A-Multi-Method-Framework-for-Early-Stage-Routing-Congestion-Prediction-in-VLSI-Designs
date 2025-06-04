class Cell:
    counter = -1

    def __init__(self):
        Cell.counter += 1
        self.id = Cell.counter

        # Input file attributes
        self.name = None
        self.ly = None
        self.lx = None
        self.w = None  # width
        self.h = None  # height
        self.movetype = None
        self.orientation = None

        # Calculated attributes
        self.hy = None
        self.rx = None
        self.pin = False
        self.macro = False
        self.lvl = None  # Connection based attribute
        self.nets = {}

        self.pin_counter = 0

    def __str__(self):
        s = (f"=== cell: {self.name} ===\n"
             f"ly: {self.ly}, lx: {self.lx}, hy: {self.hy}, rx: {self.rx}\n"
             f"w: {self.w}, h: {self.h}\n"
             f"macro: {self.macro}, pin: {self.pin}\n"
             f"nets: {self.nets.keys()}\n"
             f"=========================")
        return s

    def generate_cell(self, name: str, fl: list):
        self.name = name
        self.lx = fl[0]
        self.ly = fl[1]
        self.orientation = fl[2]
        self.w = fl[3]
        self.h = fl[4]
        if len(fl) > 5:
            self.movetype = fl[5]

        self.hy = self.ly + self.h
        self.rx = self.lx + self.w