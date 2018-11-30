import os
from stl import mesh
from triangle import *
from renderer import *
from geometery_utils import length
from rectpack import PackingMode, PackingBin, newPacker, float2dec
from rectpack import maxrects, skyline

import argparse

import sys


def main(mesh_file, output_name, debug):
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
    edge_to_index = {}
    curr_index = 0

    for face, face_normal in zip(src_mesh.vectors, src_mesh.normals):
        # three edges consisting of each pair of points
        tri = Triangle(
            face_normal,
            Edge(face[0], face[1]),
            Edge(face[1], face[2]),
            Edge(face[2], face[0]),
        )
        for edge in tri.edges:
            try:
                # match the edge index to the index of it's edge mate
                edge.index = edge_to_index[edge.indexable()]
            except KeyError:
                # edge has not already been visited, set new index and make female
                edge_to_index[edge.indexable()] = curr_index
                edge.index = curr_index
                edge.male = False
                curr_index += 1
        tris.append(tri)

    edge_lengths = set()
    [edge_lengths.update([length(v[0], v[1]), length(v[1], v[2]), length(v[2], v[0])]) for v in src_mesh.vectors]
    print 'Outputting {0} triangles with a min edge of {1} and a max edge of {2}'.format(
        len(src_mesh.vectors), min(edge_lengths), max(edge_lengths)
    )
    best_packer = None
    for pack_algo in [maxrects.MaxRectsBl, maxrects.MaxRectsBaf, skyline.SkylineMwf, skyline.SkylineBl]:
        packer = newPacker(mode=PackingMode.Offline,
                           pack_algo=pack_algo,
                           bin_algo=PackingBin.BFF,
                           rotation=False)
        rid_to_packing_box = {}
        i = 0
        for tri in tris:
            r = PackingBoxRenderer()
            r.add_triangle(tri)
            box = r.finish('')
            rid_to_packing_box[i] = box
            packer.add_rect(*box.rect, rid=i)
            i += 1
        packer.add_bin(float2dec(Config.bed_width, 2), float2dec(Config.bed_height, 2), count=float('inf'))
        packer.pack()
        print len(packer.bin_list())
        if best_packer is None or len(packer.bin_list()) < len(best_packer.bin_list()):
            best_packer = packer

    right = np.array([1, 0])
    up = np.array([0, 1])
    frame_width = Config.bed_width - 2 * (Config.padding - Config.t)
    frame_height = Config.bed_height - 2 * (Config.padding - Config.t)
    print frame_height
    for i, b in enumerate(packer):
        r = renderer(axis_range=np.array([Config.bed_width, Config.bed_height]))
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
            r.add_triangle(orig_box.triangle, translation=delta)
            r.update()

            min_edge_index = min(min_edge_index, *[e.index for e in orig_box.triangle.edges])
            max_edge_index = max(max_edge_index, *[e.index for e in orig_box.triangle.edges])
        r.finish('{0}/{0}-bed{1}_{2}_{3}'.format(output_name, i, min_edge_index, max_edge_index))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a mesh into cuttable triangles.')
    parser.add_argument('mesh_file', help='Relative path to the input .stl')
    parser.add_argument('--debug', action='store_true', help='Only render in matplotlib.')
    args = parser.parse_args()
    main(args.mesh_file, args.mesh_file.split("/")[-1].split(".")[0], args.debug)
