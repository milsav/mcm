'''
Metacognitive machines 

SceneAnalyzer: Identification of objects in given scene

Authors: Dusica Knezevic (lucy@dmi.uns.ac.rs), Milos Savic (svc@dmi.uns.ac.rs)
'''

import networkx as nx

from Matrix import dx, dy, link_type

# Moore neighborhood: offsets
# dx = [-1, -1, -1, 0, 0, 1, 1, 1]
# dy = [-1, 0, 1, -1, 1, -1, 0, 1]
        
# Moore neighborhood: link types in pattern graphs 
# link_type = ["UL", "U", "UR", "L", "R", "DL", "D", "DR"]

class IdentifyObjects:
    def __init__(self, file, remove_internal_pix = False):
        with open(file) as f:
            lines = [line.rstrip() for line in f]

        self.conceptName = lines[0] #remove if not needed
        self.remove_internal_pix = remove_internal_pix
        dimx = len(lines) - 1
        dimy = 0
        for i in range(1, len(lines)):
            l = len(lines[i])
            if l > dimy:
                dimy = l

        mat = self.__create_empty_matrix(dimx, dimy)
        
        for i in range(1, len(lines)):
            l = lines[i]
            for j in range(len(l)):
                c = l[j]
                if c != ' ':
                    mat[i - 1][j] = c

        self.dimx = dimx
        self.dimy = dimy
        self.matrix = mat
        self.objects = self.__identify_objects()

    def __create_empty_matrix(self, dimx, dimy):
        mat = []
        for _ in range(dimx):
            row = [' '] * dimy
            mat.append(row)

        return mat


    # identifies all objects on a scene represented by matrix
    def __identify_objects(self):
        objects = [] # result; list of all detected components
        self.graph = nx.DiGraph()

        for i in range(0, self.dimx):
            for j in range(0, self.dimy):
                if self.matrix[i][j] != ' ':
                    node_id = str(i) + "-" + str(j)
                    self.graph.add_node(node_id)

        for i in range(0, self.dimx):
            for j in range(0, self.dimy):
                if self.matrix[i][j] != ' ':
                    current_id = str(i) + "-" + str(j)
                    for k in range(len(dx)):
                        nei_x = i + dx[k]
                        nei_y = j + dy[k]
                        in_range = nei_x >= 0 and nei_x < self.dimx and nei_y >= 0 and nei_y < self.dimy
                        if in_range and self.matrix[nei_x][nei_y] != ' ':
                            nei_id = str(nei_x) + "-" + str(nei_y)
                            self.graph.add_edge(current_id, nei_id, link_type=link_type[k])
        
        if self.remove_internal_pix:
            to_remove = []
            for node in self.graph.nodes:
                if self.graph.in_degree(node) == 8:
                    to_remove.append(node)

            self.graph.remove_nodes_from(to_remove)

        components = nx.weakly_connected_components(self.graph)
        for comp in components:
            obj = nx.DiGraph()
            obj.add_nodes_from(comp)
            obj.add_edges_from((n, nbr, d)
            for n, nbrs in self.graph.adj.items() if n in comp
            for nbr, d in nbrs.items() if nbr in comp)
            objects.append(obj)

        return objects

    def __node_contained(self, list_objs, node):
        for obj in list_objs:
            if node in obj.nodes:
                return True
        return False

    # identifies one object from specific point (i,j) on scene
    def __find_object(self, i, j):
        return None

    def getObjects(self):
        return self.objects
    


idobj = IdentifyObjects("test_files/scene2.txt", True)
objs = idobj.getObjects()
for obj in objs:
    print(obj.nodes)