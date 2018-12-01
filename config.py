class Config(object):
    bed_width = 279.4  # 8.5x11 cardstock
    bed_height = 200

    padding = 2

    mat_thickness = .25

    height = 7
    min_offset = height

    cut = 7
    cut_offset = 1.5

    tab_snap = .5
    t = .1
    tab_height = height - cut_offset

    text_offset = .75
    text_height = height - 2 * text_offset

    min_edge_width = 2 * min_offset + cut + 2 * cut_offset
