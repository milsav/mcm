# Meta-cognitive machines
#
# HOAutomaton module constains functions and classes 
# for pattern recognition based on higher-order automata
# combining base automata 
#
# As base automata, HO automata are also constructed from 
# 2D matrix patterns
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

import networkx as nx

from AutomataMemory import base_automata_memory
from Automaton import FSMPatRecKernel
from Matrix import neigh
from SceneAnalyzer import IdentifyObjects


"""
Higher-order automaton: graph encompassing simple and/or higher order automata
(represented as objects of HOANode class) connected by activation dependencies
"""

class HOANode:
    def __init__(self, node_id, concept, automaton, activation_time):
        self.node_id = node_id
        self.concept = concept
        self.automaton = automaton
        self.activation_time = activation_time

    def get_concept(self):
        return self.concept
    
    def get_automaton(self):
        return self.automaton
    
    def get_activation_time(self):
        return self.activation_time
    
    def __hash__(self):
        return hash(self.node_id)
    
    def get_id(self):
        return self.node_id
    
    def print(self):
        print(str(self.node_id) + "-" + self.concept + "-" + str(self.activation_time))


class HOA:
    def __init__(self, concept):
        self.concept = concept
        self.G = nx.DiGraph()
        self.num_nodes = 0
        self.nodes = []
    
    def add_node(self, concept, automaton, activation_time):
        node_id = self.num_nodes
        self.num_nodes += 1 
        n = HOANode(node_id, concept, automaton, activation_time)
        self.nodes.append(n)
        self.G.add_node(n)
        
    def add_link(self, src_index, dst_index, link_type):
        self.G.add_edge(self.nodes[src_index], self.nodes[dst_index], link_type=link_type)
    
    def print(self):
        print("HOA graph for ", self.concept)
        nodes = self.G.nodes()
        for n in nodes:
            n.print()
        print("#links")
        links = self.G.edges()
        for l in links:
            src, dst = l
            print(src.get_id(), "-->", dst.get_id(), "move = ", self.G.edges[l]["link_type"])

    

"""
Class for learning HOA graphs
"""
class HOALearner:
    def __init__(self, concept, matrix, verbose=False):
        idobj = IdentifyObjects(matrix)
        if idobj.num_objects() != 1:
            raise Exception("[ERROR, HOALearner] matrix contains multiple objects")

        self.concept = concept
        self.matrix = matrix
        self.dim_x = len(matrix)
        self.dim_y = len(matrix[0])
        self.verbose = verbose
        self.hoa = HOA(concept)

    #
    # identify automata that can be activated in pattern matrix
    # 
    def identify_automata(self):
        # set of visited matrix fields
        visited_fields = set()

        # list of activated automata
        self.activated_automata = []

        base_concepts = base_automata_memory.get_concepts()

        for i in range(self.dim_x):
            for j in range(self.dim_y):
                start_field = str(i) + "-" + str(j)
                if self.matrix[i][j] != ' ' and start_field not in visited_fields:
                    # identify base concepts
                    for concept in base_concepts:
                        for automaton in base_automata_memory.get_automata(concept): 
                            prk = FSMPatRecKernel(automaton, self.matrix, i, j)
                            rec, t, visited = prk.apply()
                            if rec:
                                # check valid activations
                                valid_activation = False
                                for v in visited:
                                    if v != start_field and not v in visited_fields:
                                        valid_activation = True
                                        break

                                if valid_activation:
                                    for v in visited:
                                        visited_fields.add(v)

                                    self.activated_automata.append([concept, automaton, visited, t])
                                    break      

        if self.verbose:
            print("Activated automata")
            for a in self.activated_automata:
                print(a[0])
                a[1].print()
                print(a[2])
                print(a[3])
                print("\n")

        # create nodes in HOA graph
        for a in self.activated_automata:
            concept, automaton, activation_time = a[0], a[1], a[3]
            self.hoa.add_node(concept, automaton, activation_time)

    
    def infere_automata_dependencies(self):
        for j in range(1, len(self.activated_automata)):
            for i in range(j):
                vf_i = self.activated_automata[i][2]
                vf_j = self.activated_automata[j][2]

                i_start, i_end = vf_i[0], vf_i[-1]
                j_start, j_end = vf_j[0], vf_j[-1]

                if i_start == j_start:
                    # automata i and j have identical starting positions
                    self.hoa.add_link(i, j, "START")
                else:
                    # automaton j starts after automata i 
                    nei, move = neigh(j_start, i_end)
                    if nei:
                        self.hoa.add_link(i, j, move)
                    else:
                        # incident automata
                        if i_end == j_end:
                            self.hoa.add_link(i, j, "END")
                        else: 
                            for m in vf_i:
                                for n in vf_j:
                                    nei, move = neigh(n, m)
                                    if nei:
                                        if move == "ID":
                                            self.hoa.add_link(i, j, "INC")
                                            print(m, n)
                                        else:
                                            self.hoa.add_link(i, j, "INC_" + move)

                    
    def learn(self):
        self.identify_automata()
        self.infere_automata_dependencies()
        return self.hoa


if __name__ == "__main__":
    from Automaton import load_matrix
    concept, matrix = load_matrix('test_files/square_cross.pat')

    hoal = HOALearner(concept, matrix, verbose=True)
    hoa = hoal.learn()
    hoa.print()
    




