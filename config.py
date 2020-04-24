class Config(object):
    font_file = '1CamBam_Stick_1.ttf'

    bed_width = 305
    bed_height = 200

    padding = .5

    mat_thickness = 3.06  # eighth inch ply
    t = .11  # compensate for the laser's kerf
    attachment_tab = .2  # Amount by which to under cut a line to leave the piece partially attached

    nail_hole_diameter = .4

    notch_depth = mat_thickness
    min_thickness = mat_thickness
    snap_size = .25*mat_thickness

    text_offset = .75
    text_height = notch_depth + min_thickness

    min_edge_width = notch_depth + mat_thickness

