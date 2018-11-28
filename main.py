import os
from stl import mesh
from triangle import *
from renderer import *
from geometery_utils import length

import numpy as np
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
    for tri in tris:
        full_name = '{0}\\{1}-{2}'.format(output_name, output_name, tri.__str__())
        tri.render(full_name, renderer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a mesh into cuttable triangles.')
    parser.add_argument('mesh_file', help='Relative path to the input .stl')
    parser.add_argument('--debug', action='store_true', help='Only render in matplotlib.')
    args = parser.parse_args()
    main(args.mesh_file, args.mesh_file.split("\\")[-1].split(".")[0], args.debug)
