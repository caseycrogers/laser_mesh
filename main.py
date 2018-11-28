import os
from stl import mesh
from triangle import *
from renderer import *

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

    for tri in tris:
        full_name = '{0}\\{1}-{2}'.format(output_name, output_name, tri.__str__())
        tri.render(full_name, renderer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a mesh into cuttable triangles.')
    parser.add_argument('mesh_file', help='Relative path to the input .stl')
    parser.add_argument('output', help='Name for the output path/file names')
    parser.add_argument('--debug', action='store_true', help='Only render in matplotlib.')
    args = parser.parse_args()
    main(args.mesh_file, args.output, args.debug)
