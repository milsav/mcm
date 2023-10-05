# Meta-cognitive machines
#
# Module for advanced concept learning (learning unsupervised
# base concept to learn a complex concept)  
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

import networkx as nx

from Automaton import PatternGraph, learn_simple_concept_from_matrix
from HOAutomaton import learn_complex_concept
from Matrix import parse_field, create_empty_matrix
from Matrix import print_matrix, determine_first_nonempty_pixel

class AdvancedLearner:
    def __init__(self, concept_id, mat, automata_memory):
        self.concept_id = concept_id
        self.mat = mat
        self.automata_memory = automata_memory

        # first non-empty pixel
        self.start_x, self.start_y = determine_first_nonempty_pixel(mat)

        pattern_graph = PatternGraph(self.mat)
        self.G = pattern_graph.G

    
    def max_degree(self):
        max_d = 0
        max_d_node = None

        for n in self.G.nodes():
            deg = self.G.degree(n)
            if deg > max_d:
                max_d = deg
                max_d_node = n

        return max_d_node 


    def is_simple_component(self, comp):
        for n in comp:
            indeg = self.G.in_degree(n)
            if indeg > 2:
                return False
            
        return True


    def check_components(self, wccs):
        if len(wccs) == 1:
            return False
        
        for w in wccs:
            comp = nx.induced_subgraph(self.G, w)
            if not self.is_simple_component(comp):
                return False
            
        return True


    def decompose_pattern_graph(self):
        stop = False
        wccs = None
        iter = 0

        while not stop:
            node_to_remove = None
            if iter == 0:
                node_to_remove = str(self.start_x) + "-" + str(self.start_y)
            else:
                node_to_remove = self.max_degree()

            print("Removing node", node_to_remove)
            self.G.remove_node(node_to_remove)
            wccs = list(nx.weakly_connected_components(self.G))
            stop = self.check_components(wccs)
            iter += 1

        self.pattern_graphs = []
        for w in wccs:
            comp = nx.induced_subgraph(self.G, w)
            self.pattern_graphs.append(comp)


    def pattern_graph_to_matrix(self, pg):
        #print("Pattern graph to matrix")
        max_x, max_y = 0, 0
        for n in pg:
            x, y = parse_field(n)
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
        
        dimx, dimy = max_x + 1, max_y + 1
        mat = create_empty_matrix(dimx, dimy)

        for n in pg:
            x, y = parse_field(n)
            mat[x][y] = pg.nodes[n]["symbol"]

        return mat


    def learn(self):
        self.decompose_pattern_graph()
        for pg in self.pattern_graphs:
            mat = self.pattern_graph_to_matrix(pg)
            print("Fragment")
            print_matrix(mat)

            sat = self.automata_memory.retrieve_satisfiable_basic_concepts(mat)
            if len(sat) > 0:
                print("Fragmet recongnized by", sat[0][0])
                continue

            print("Learning unknown fragment")
            ok, _, fsms = learn_simple_concept_from_matrix(mat, verbose=False)
            if ok:
                concept_id = self.automata_memory.get_concept_id_for_unknown(True)
                self.automata_memory.add_automata_to_memory(concept_id, True, fsms, mat) 

        ok, msg = learn_complex_concept(self.concept_id, self.mat, self.automata_memory)
        if ok:
            print("Concept", self.concept_id, "learnt successfully")
        else:
            print("Learning concept", self.concept_id, "failed: ", msg)



            
        

