import os
from stl import mesh
from polygon import *
from renderer import *
from geometery_utils import *
from rectpack import PackingMode, PackingBin, newPacker, float2dec
from rectpack import maxrects, skyline
from render_polygon import render_polygon

import argparse
import numpy as np

import sys


def main(mesh_file, output_name, merge, render_panels, debug, individual, display_packing_boxes):
    if debug:
        renderer = DebugRenderer
    else:
        renderer = DXFRenderer
        if os.path.exists(output_name):
            print('output directory ({0}) already exists.'.format(output_name))
            sys.exit(1)
        os.mkdir(output_name)

    src_mesh = mesh.Mesh.from_file(mesh_file)

    polys = []
    edge_to_edge_mate = {}
    edge_to_poly_mate = {}
    curr_index = 0

    faces, face_normals = list(map(list, src_mesh.vectors)), list(map(list, src_mesh.normals))
    if merge:
        faces, face_normals = merge_coplanar_faces(src_mesh.vectors, src_mesh.normals)

    for face, face_normal in zip(faces, face_normals):
        unit_norm = normalized(face_normal)
        orig_poly = Polygon(
            face_normal,
            [Edge(b, c, angle_between_three_points(c, b, a, unit_norm), angle_between_three_points(d, c, b, unit_norm))
             for a, b, c, d in adjacent_nlets(list(reversed(face)), 4)]
        )
        for edge in orig_poly.edges:
            try:
                # find the edge mate if present
                edge.index = curr_index
                edge_mate = edge_to_edge_mate[edge.indexable()]
                poly_mate = edge_to_poly_mate[edge.indexable()]

                # find the two vertices not shared by the two polygons, needed to help determine concavity
                disjoint_vert = [p for p in orig_poly.points
                                 if not point_equals(p, edge.point_a)
                                 and not point_equals(p, edge.point_b)][0]
                disjoint_vert_mate = [p for p in poly_mate.points
                                      if not point_equals(p, edge.point_a)
                                      and not point_equals(p, edge.point_b)][0]
                if np.dot(orig_poly.unit_norm, poly_mate.unit_norm) >= 0:
                    edge_angle = angle_between_faces(disjoint_vert, disjoint_vert_mate, orig_poly.unit_norm, poly_mate.unit_norm)
                else:
                    edge_angle = angle_between_faces(disjoint_vert, disjoint_vert_mate, orig_poly.unit_norm, -1*poly_mate.unit_norm)


                # set concave edges to female to try to avoid collisions
                target_type = Edge.female if edge.angle_a > np.pi or edge.angle_b > np.pi else Edge.male
                edge.set_type(target_type)
                edge.set_edge_angle(edge_angle)
                edge.set_edge_mate(edge_mate)

                edge_mate.set_type(Edge.opposite_type(target_type))
                edge_mate.set_edge_angle(edge_angle)
                edge_mate.set_edge_mate(edge)
                edge_mate.index = curr_index
                curr_index += 1
            except KeyError:
                # edge has not already been visited, add it to the dictionaries
                edge_to_edge_mate[edge.indexable()] = edge
                edge_to_poly_mate[edge.indexable()] = orig_poly
        polys.append(orig_poly)

    edge_lengths = set()
    [edge_lengths.update([distance(v[0], v[1]), distance(v[1], v[2]), distance(v[2], v[0])]) for v in src_mesh.vectors]
    print('================================')
    print('Outputting:\npolys: {0} \nmax edges: {1}\nmax edge length: {2}\nmin edge length: {3}'.format(
        len(polys),
        max([len(p.edges) for p in polys]),
        max(edge_lengths),
        min(edge_lengths),
    ))
    print('================================')

    if individual:
        for i, orig_poly in enumerate(polys):
            r = renderer()
            render_polygon(r, orig_poly, render_panels)
            indices = [e.index for e in orig_poly.edges]
            r.finish('{0}/{0}-tri{1}-{2}_{3}_{4}'.format(output_name, i, *indices))
    else:
        best_packer = None
        for pack_algo in [maxrects.MaxRectsBl, maxrects.MaxRectsBaf, skyline.SkylineMwf, skyline.SkylineBl]:
            packer = newPacker(mode=PackingMode.Offline,
                               pack_algo=pack_algo,
                               bin_algo=PackingBin.BFF,
                               rotation=True)
            rid_to_box = {}
            rid_to_poly = {}
            i = 0
            for orig_poly in polys:
                r = PackingBoxRenderer()
                render_polygon(r, orig_poly, render_panels)
                box = r.finish('')
                rid_to_box[i] = box
                rid_to_poly[i] = orig_poly
                packer.add_rect(*box.rect, rid=i)
                i += 1
            packer.add_bin(float2dec(Config.bed_width, 2), float2dec(Config.bed_height, 2), count=float('inf'))
            packer.pack()
            if best_packer is None or len(packer.bin_list()) < len(best_packer.bin_list()):
                best_packer = packer

        frame_width = Config.bed_width - 2 * (Config.padding - Config.t)
        frame_height = Config.bed_height - 2 * (Config.padding - Config.t)
        for i, b in enumerate(packer):
            r = renderer(panels=render_panels, axis_range=np.array([Config.bed_width, Config.bed_height]))
            # draw positioning frame
            r.add_rectangle(np.array([0, 0]), frame_width, frame_height)

            min_edge_index = float('inf')
            max_edge_index = float('-inf')
            for rect in b:
                orig_box = rid_to_box[rect.rid]
                orig_poly = rid_to_poly[rect.rid]
                if rect.width != orig_box.rect[0]:
                    rot = np.pi/2
                else:
                    rot = 0.0
                delta = np.array([float(rect.x), float(rect.y)]) - rotate_cc_around_origin_2d(
                    orig_box.top_right if rot else orig_box.bottom_left, rot)
                if display_packing_boxes:
                    box_points = [
                        [rect.x, rect.y], [rect.x + rect.width, rect.y], [rect.x + rect.width, rect.y + rect.height],
                        [rect.x, rect.y + rect.height]
                    ]
                    for a, b in adjacent_nlets(box_points, 2):
                        r.add_line(a, b, color=DEBUG)
                render_polygon(r, orig_poly, render_panels, translation=delta, rotation=rot)
                r.update()

                min_edge_index = min(min_edge_index, *[e.index for e in orig_poly.edges])
                max_edge_index = max(max_edge_index, *[e.index for e in orig_poly.edges])
            r.finish('{0}/{0}-bed{1}_{2}_{3}'.format(output_name, i, min_edge_index, max_edge_index))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a mesh into cuttable triangles.')
    parser.add_argument('mesh_file', help='Relative path to the input .stl')
    parser.add_argument('--no_merge', action='store_true', help='Don\'t merge coplanar faces.')
    parser.add_argument('--debug', action='store_true', help='Only render in matplotlib.')
    parser.add_argument('--no_panels', action='store_true', help='Don\'t render panels.')
    parser.add_argument('--individual', action='store_true', help='Render each triangle individually.')
    parser.add_argument('--display_packing_boxes', action='store_true', help='Showing packing boxes.')
    args = parser.parse_args()
    main(args.mesh_file,
         args.mesh_file.split("/")[-1].split(".")[0],
         not args.no_merge,
         not args.no_panels,
         args.debug,
         args.individual,
         args.display_packing_boxes)
