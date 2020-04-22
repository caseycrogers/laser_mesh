class Color:
    def __init__(self, r, g, b, description):
        self.description = description
        self.r, self.g, self.b = r, g, b

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.description))


CUT_THICK = Color(0, 0, 255, "CUT_THICK")
CUT_THIN = Color(255, 0, 0, "CUT_THIN")
ENGRAVE_THICK = Color(0, 128, 0, "ENGRAVE_THICK")
ENGRAVE_THIN = Color(255, 165, 0, "ENGRAVE_THIN")
FRAME = Color(128, 128, 128, "FRAME")
DEBUG = Color(0, 0, 0, "DEBUG")