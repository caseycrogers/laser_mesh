import os
from stl import mesh
from polygon import *
from renderer import *
from geometery_utils import *
from rectpack import PackingMode, PackingBin, newPacker, float2dec
from rectpack import maxrects, skyline

import argparse

import sys


def main(mesh_file, output_name, merge, panels, debug, individual):
    if debug:
        renderer = DebugRenderer
    else:
        renderer = DXFRenderer
        if os.path.exists(output_name):
            print 'output directory ({0}) already exists.'.format(output_name)
            sys.exit(1)
        os.mkdir(output_name)

    src_mesh = mesh.Mesh.from_file(mesh_file)

    tris = []
    edge_to_edge_mate = {}
    edge_to_poly_mate = {}
    curr_index = 0

    faces, face_normals = list(map(list, src_mesh.vectors)), list(map(list, src_mesh.normals))
    if merge:
        faces, face_normals = merge_coplanar_faces(src_mesh.vectors, src_mesh.normals)

    for face, face_normal in zip(faces, face_normals):
        unit_norm = normalized(face_normal)
        poly = Polygon(
            face_normal,
            [Edge(b, c, angle_between_three_points(c, b, a, unit_norm), angle_between_three_points(d, c, b, unit_norm))
             for a, b, c, d in adjacent_nlets(face, 4)]
        )
        for edge in poly.edges:
            try:
                # find the edge mate if present
                edge.index = curr_index
                edge_mate = edge_to_edge_mate[edge.indexable()]
                poly_mate = edge_to_poly_mate[edge.indexable()]

                # find the two vertices not shared by the two polygons, needed to help determine concavity
                disjoint_vert = [p for p in poly.points
                                 if not point_equals(p, edge.point_a)
                                 and not point_equals(p, edge.point_b)][0]
                disjoint_vert_mate = [p for p in poly_mate.points
                                      if not point_equals(p, edge.point_a)
                                      and not point_equals(p, edge.point_b)][0]
                edge_angle = angle_between_faces(disjoint_vert, disjoint_vert_mate, poly.unit_norm, poly_mate.unit_norm)

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
                edge_to_poly_mate[edge.indexable()] = poly
        tris.append(poly)

    edge_lengths = set()
    [edge_lengths.update([distance(v[0], v[1]), distance(v[1], v[2]), distance(v[2], v[0])]) for v in src_mesh.vectors]
    print 'Outputting {0} triangles with a min edge of {1} and a max edge of {2}'.format(
        len(src_mesh.vectors), min(edge_lengths), max(edge_lengths)
    )

    if individual:
        for i, poly in enumerate(tris):
            r = renderer(panels=panels)
            r.add_polygon(poly)
            indices = [e.index for e in poly.edges]
            r.finish('{0}\\{0}-tri{1}-{2}_{3}_{4}'.format(output_name, i, *indices))
    else:
        best_packer = None
        for pack_algo in [maxrects.MaxRectsBl, maxrects.MaxRectsBaf, skyline.SkylineMwf, skyline.SkylineBl]:
            packer = newPacker(mode=PackingMode.Offline,
                               pack_algo=pack_algo,
                               bin_algo=PackingBin.BFF,
                               rotation=False)
            rid_to_packing_box = {}
            i = 0
            for poly in tris:
                r = PackingBoxRenderer()
                r.add_polygon(poly)
                box = r.finish('')
                rid_to_packing_box[i] = box
                packer.add_rect(*box.rect, rid=i)
                i += 1
            packer.add_bin(float2dec(Config.bed_width, 2), float2dec(Config.bed_height, 2), count=float('inf'))
            packer.pack()
            if best_packer is None or len(packer.bin_list()) < len(best_packer.bin_list()):
                best_packer = packer

        right = np.array([1, 0])
        up = np.array([0, 1])
        frame_width = Config.bed_width - 2 * (Config.padding - Config.t)
        frame_height = Config.bed_height - 2 * (Config.padding - Config.t)
        for i, b in enumerate(packer):
            r = renderer(panels=panels, axis_range=np.array([Config.bed_width, Config.bed_height]))
            # draw positioning frame
            f0 = np.array([Config.padding - Config.t, Config.padding - Config.t])
            f1 = f0 + frame_width * right
            r.add_line(f0, f1, color=FRAME)
            f2 = f1 + frame_height * up
            r.add_line(f1, f2, color=FRAME)
            f3 = f2 - frame_width * right
            r.add_line(f2, f3, color=FRAME)
            r.add_line(f3, f0, color=FRAME)

            min_edge_index = float('inf')
            max_edge_index = float('-inf')
            for rect in b:
                orig_box = rid_to_packing_box[rect.rid]
                delta = np.array([float(rect.x), float(rect.y)]) - orig_box.bottom_left
                r.add_polygon(orig_box.triangle, translation=delta)
                r.update()

                min_edge_index = min(min_edge_index, *[e.index for e in orig_box.triangle.edges])
                max_edge_index = max(max_edge_index, *[e.index for e in orig_box.triangle.edges])
            r.finish('{0}\\{0}-bed{1}_{2}_{3}'.format(output_name, i, min_edge_index, max_edge_index))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a mesh into cuttable triangles.')
    parser.add_argument('mesh_file', help='Relative path to the input .stl')
    parser.add_argument('--no_merge', action='store_true', help='Don\'t merge coplanar faces.')
    parser.add_argument('--debug', action='store_true', help='Only render in matplotlib.')
    parser.add_argument('--no_panels', action='store_true', help='Don\'t render panels.')
    parser.add_argument('--individual', action='store_true', help='Render each triangle individually.')
    args = parser.parse_args()
    main(args.mesh_file,
         args.mesh_file.replace("/", "\\").split("\\")[-1].split(".")[0],
         not args.no_merge,
         not args.no_panels,
         args.debug,
         args.individual)
