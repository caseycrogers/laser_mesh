from color import *
from config import Config
from geometery_utils import *

import numpy as np


def render_polygon(r, polygon, render_panels, translation=np.array([0, 0])):
    adjusted_points = get_adjusted_points(polygon, Config.mat_thickness + Config.snap_size)

    cutout_width = Config.joint_depth + Config.min_thickness

    def render_cutout():
        cutout = [p + translation for p in
                  offset_polygon_2d(adjusted_points,
                                    len(adjusted_points)*[cutout_width])]
        if not cutout:
            print("Shape too small for cutout!")
        for line in adjacent_nlets(cutout, 2):
            r.add_line(line[0], line[1])

    def render_holes():
        cutout = [p + translation for p in
                  offset_polygon_2d(adjusted_points,
                                    len(adjusted_points)*[(Config.joint_depth + Config.min_thickness)/2.0])]
        for point, trip in zip(cutout[1:] + cutout[:1], adjacent_nlets(cutout, 3)):
            if (distance(trip[0], trip[1]) < 1.5*Config.min_thickness and
                    distance(trip[1], trip[2]) < 1.5*Config.min_thickness):
                continue
            r.add_circle(point, Config.nail_hole_diameter)
            r.add_circle(point, Config.nail_hole_diameter + .4, color=CUT_THIN)

    render_cutout()

    for i, edge in enumerate(polygon.edges):
        # convert to 2D coordinate space
        a_orig = polygon.flatten_point(edge.point_a)[0:2] + translation
        b_orig = polygon.flatten_point(edge.point_b)[0:2] + translation
        # we need to offset edges at convex joints to account for material thickness
        a = adjusted_points[i] + translation
        b = adjusted_points[(i + 1) % len(adjusted_points)] + translation
        mid = midpoint(a, b)
        width = distance(a, b)

        base_cs = CoordinateSystem2D(normalized(b - a), normal(b, a))

        def render_joint(joint_point):
            r.set_draw_point(joint_point)
            # reduce angles from 0 - 360 to 0 - 180 for simplicity
            joint_angle = edge.get_edge_angle if not edge.is_concave else 2 * np.pi - edge.get_edge_angle
            joint_width = Config.mat_thickness - 2*Config.t
            joint_depth = Config.joint_depth - 2*Config.t

            rot_cs = base_cs.rotated(np.pi / 2.0 - joint_angle)

            def draw_fit_joint():
                def draw_fit(cs):
                    r.draw(cs.right(.5*joint_width - Config.snap_size))
                    r.draw(cs.right(Config.snap_size) + cs.down(2*Config.snap_size))
                    r.draw(cs.down(cutout_width - joint_depth - 2*Config.snap_size))
                    r.draw(cs.right(joint_width))
                    cs = cs.flipped_y()
                    r.draw(cs.down(cutout_width - joint_depth - 2*Config.snap_size))
                    r.draw(cs.right(Config.snap_size) + cs.down(2*Config.snap_size))
                    r.draw(cs.right(.5*joint_width - Config.snap_size))

                long_edge = Config.snap_size + cutout_width + (1.5*joint_width) / np.tan(joint_angle / 2.0)
                short_edge = Config.snap_size + cutout_width - (.5*joint_width) / np.tan(joint_angle / 2.0)

                paper_joint_offset = 1.5*cutout_width

                # add index text
                r.add_text(joint_point + base_cs.right(joint_width) + base_cs.down(Config.text_offset + cutout_width - joint_depth),
                              -1*base_cs.y_vector, str(edge.index),
                              long_edge - (cutout_width - joint_depth) - Config.text_offset,
                              joint_width)

                r.move(base_cs.right(joint_width / 2.0))

                # long edges
                if render_panels:
                    r.draw(base_cs.down(long_edge - paper_joint_offset - Config.snap_size), tab=Config.attachment_tab)
                    r.draw(base_cs.left(Config.snap_size) + base_cs.up(Config.snap_size))
                    r.draw(base_cs.down(paper_joint_offset))
                    r.draw(rot_cs.right(paper_joint_offset))
                    r.draw(rot_cs.left(Config.snap_size) + rot_cs.up(Config.snap_size))
                else:
                    r.draw(base_cs.down(long_edge), tab=Config.attachment_tab)
                    r.draw(rot_cs.right(long_edge), tab=Config.attachment_tab)
                draw_fit(rot_cs.flipped_x().rotated(-.5*np.pi))
                r.draw(rot_cs.left(short_edge))
                r.draw(base_cs.up(short_edge))
                draw_fit(base_cs.flipped_x())

            def draw_glue_joint():
                long_edge = joint_depth + joint_width / np.tan(joint_angle / 2.0)

                p1 = joint_point
                p2 = p1 + base_cs.down(long_edge)
                r.add_line(p1, p2)

                p3 = p2 + rot_cs.right(long_edge)
                r.add_line(p2, p3)
                p4 = p3 + rot_cs.up(joint_width)
                r.add_line(p3, p4)
                p5 = p4 + rot_cs.left(joint_depth)
                r.add_line(p4, p5)

                p6 = p5 + base_cs.up(joint_depth)
                r.add_line(p5, p6)
                r.add_text(p5, p2 - p5, str(edge.index), distance(p2, p5) - Config.text_offset, joint_width,
                              v_center=True)
                p7 = p6 + base_cs.left(joint_width)
                r.add_line(p6, p7, tab=Config.attachment_tab)

            draw_fit_joint()

        def get_joint_bias():
            def bias(theta):
                # place joint nearer to obtuse angles, further from acute ones
                return 1 - min(theta / np.pi, 1)
            mate = edge.get_edge_mate
            # invert the ratios for the angles on the right relative to this edge
            bias_from_left = np.average([bias(edge.angle_a), 1 - bias(edge.angle_b),
                                         1 - bias(mate.angle_a), bias(mate.angle_b)])
            return bias_from_left

        def render_edge():
            notch_width = Config.mat_thickness - 2*Config.t
            # joint center needs to be positioned respective to the original side otherwise
            # mating joints will not line up properly depending on their respective offsets
            # pick the joint point biased towards the centers of the offset polygon edges
            biased_point = a_orig + base_cs.right(distance(a_orig, b_orig) * get_joint_bias())
            joint_center = nearest_point_on_line(a, b, biased_point)
            if distance(a, joint_center) + notch_width / 2.0 > distance(a, b):
                print('Joint is falling off the end of the edge.')
            r.set_draw_point(a)
            r.draw_to(joint_center + base_cs.left(notch_width / 2.0), tab=Config.attachment_tab)
            r.draw(base_cs.up(Config.joint_depth))
            r.draw(base_cs.right(notch_width))
            r.draw(base_cs.down(Config.joint_depth))
            joint_point = r.get_draw_point()
            r.draw_to(b)

            if edge.is_male:
                render_joint(joint_point)

        def render_text():
            text_point = mid + base_cs.right(Config.mat_thickness / 2.0 + Config.text_offset) + \
                         base_cs.up(Config.text_offset)
            r.add_text(text_point, b - a,
                          str(edge.index) + ('c' if edge.is_concave else ''),
                          distance(b, text_point) - Config.text_offset, Config.text_height - 2*Config.text_offset)

        def render_panel_edge():
            r.add_line(a_orig, b_orig, color=CUT_THIN, tab=2*Config.attachment_tab)

        def render_panel_guide():
            r.add_line(a + base_cs.left(1), a + base_cs.right(1), color=ENGRAVE_THIN)
            r.add_line(b + base_cs.left(1), b + base_cs.right(1), color=ENGRAVE_THIN)

        def render_panel_text():
            text_point = midpoint(a_orig, b_orig) + base_cs.up(Config.text_offset)
            r.add_text(text_point, b_orig - a_orig,
                          str(edge.index),
                          distance(b, text_point) - Config.text_offset, Config.text_height, ENGRAVE_THIN,
                          h_center=True)

        if render_panels:
            # render panel edge whether or not the edge is open
            render_panel_edge()
            render_panel_guide()
        if edge.is_open:
            # Don't add anything to an open edge
            r.add_line(a, b)
        else:
            render_edge()
            render_text()
            if render_panels:
                render_panel_text()

            if width < Config.min_edge_width:
                print('Side with length {0} is shorter than minimum length {1}'.format(
                    width, Config.min_edge_width))
