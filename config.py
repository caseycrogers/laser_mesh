class Config(object):
    bed_width = 279.4  # 8.5x11 cardstock
    bed_height = 200

    padding = 2

    mat_thickness = .25

    height = 7
    offset = .1

    cut = 7
    cut_offset = 1.5

    tab_snap = .5
    t = .1
    tab_height = height - 2 * cut_offset

    text_offset = .75
    text_height = height - 2 * text_offset

    min_double_tab_width = 2 * offset + 2 * cut + 3 * cut_offset
    min_single_tab_width = 2 * offset + cut + 2 * cut_offset
