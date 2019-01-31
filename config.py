class Config(object):
    bed_width = 279.4  # Definitely not right?
    bed_height = 200

    padding = 2

    mat_thickness = 6.35  # quarter inch ply
    t = .1

    offset = mat_thickness/2.0

    text_offset = .75
    text_height = mat_thickness - 2 * text_offset

    min_edge_width = offset*2 + mat_thickness

