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
from collections import deque

from Automaton import FSMPatRecKernel
from Matrix import neigh, parse_field, dx, dy
from Matrix import link_type as LT_ARRAY
from SceneAnalyzer import IdentifyObjects


"""
Higher-order automaton: graph encompassing simple and/or higher order automata
(represented as objects of HOANode class) connected by activation dependencies
"""

class HOANode:
    def __init__(self, node_id, concept, automaton, automaton_type, activation_time):
        self.node_id = node_id
        self.concept = concept
        self.automaton = automaton
        self.automaton_type = automaton_type
        self.activation_time = activation_time

    def get_concept(self):
        return self.concept
    
    def get_automaton(self):
        return self.automaton
    
    def get_automaton_type(self):
        return self.automaton_type
    
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
    
    
    def add_node(self, concept, automaton, automaton_type, activation_time):
        node_id = self.num_nodes
        self.num_nodes += 1 
        n = HOANode(node_id, concept, automaton, automaton_type, activation_time)
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

        print("-- activation time constraints")
        for x in self.identical_at:
            print(x[0], x[1], " identical activation time")
        for x in self.semi_identical_at:
            print(x[0], x[1], " semiidentical activation time")
    
    def connected(self):
        return nx.is_connected(self.G.to_undirected())
    

    def num_nodes(self):
        return self.num_nodes
    
    
    def get_nodes(self):
        return self.nodes
    

    def process_activation_times(self):
        self.identical_at = []
        self.semi_identical_at = []

        for j in range(1, self.num_nodes):
            for i in range(j):
                at_i = self.nodes[i].get_activation_time()
                at_j = self.nodes[j].get_activation_time()

                if at_i == at_j:
                    self.identical_at.append((i, j))
                elif at_i - at_j == 1:
                    self.semi_identical_at.append((i, j))
                elif at_j - at_i == 1:
                    self.semi_identical_at.append((j, i))


    def get_identical_at(self):
        return self.identical_at
    

    def get_semi_identical_at(self):
        return self.semi_identical_at
                




"""
Class for learning HOA graphs
"""
class HOALearner:
    def __init__(self, concept, matrix, automata_memory, verbose=False):
        idobj = IdentifyObjects(matrix)
        if idobj.num_objects() != 1:
            raise Exception("[ERROR, HOALearner] matrix contains multiple objects")

        self.concept = concept
        self.matrix = matrix
        self.dim_x = len(matrix)
        self.dim_y = len(matrix[0])
        self.verbose = verbose
        self.hoa = HOA(concept)

        self.automata_memory = automata_memory


    #
    # identify automata that can be activated in pattern matrix
    # 
    def identify_automata(self):
        # set of visited matrix fields
        visited_fields = set()

        # list of activated automata
        self.activated_automata = []

        base_concepts = self.automata_memory.get_base_concepts()

        for i in range(self.dim_x):
            for j in range(self.dim_y):
                start_field = str(i) + "-" + str(j)
                if self.matrix[i][j] != ' ' and start_field not in visited_fields:
                    # identify base concepts
                    for concept in base_concepts:
                        for automaton in self.automata_memory.get_automata(concept): 
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

                                    self.activated_automata.append([concept, automaton, "FSM", visited, t])
                                    break      

        if self.verbose:
            print("Activated automata")
            for a in self.activated_automata:
                print(a[0])
                a[1].print()
                print(a[2])
                print(a[3])
                print(a[4])
                print("\n")

        # create nodes in HOA graph
        for a in self.activated_automata:
            concept, automaton, automaton_type, activation_time = a[0], a[1], a[2], a[4]
            self.hoa.add_node(concept, automaton, automaton_type, activation_time)

        # derive activation time constraints
        self.hoa.process_activation_times()

    
    def infere_automata_dependencies(self):
        for j in range(1, len(self.activated_automata)):
            for i in range(j):
                vf_i = self.activated_automata[i][3]
                vf_j = self.activated_automata[j][3]

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
                            # both automata ends at same position
                            self.hoa.add_link(i, j, "END")
                        else:
                            # other incidences
                            incidences = [] 
                            for m in vf_i:
                                for n in vf_j:
                                    nei, move = neigh(n, m)
                                    if nei:
                                        if move == "ID":
                                            # self.hoa.add_link(i, j, "INC")
                                            incidences.append("INC")
                                        else:
                                            #self.hoa.add_link(i, j, "INC_" + move)
                                            incidences.append("INC_" + move)

                            if self.verbose:
                                if len(incidences) == 0:
                                    print("Automata", i, j, " are independent")
                                else:
                                    print("Automata ", i, j, " incidences: ", incidences)

                            if len(incidences) > 0:
                                selinc = min(incidences, key=len)
                                self.hoa.add_link(i, j, selinc)
        
        # check HOA connectedness
        if not self.hoa.connected():
            print("[infere_automata_dependencies, warning] HOA graph not connected")
            return


    def learn(self):
        self.identify_automata()
        self.infere_automata_dependencies()
        return self.hoa


"""
Pattern recognition based on HOA graphs
"""
class HOAPatRecKernel:
    def __init__(self, hoa, input_matrix, x, y):
        self.hoa = hoa
        self.input_matrix = input_matrix
        self.x = x
        self.y = y
        self.dimx = len(input_matrix)
        self.dimy = len(input_matrix[0])
        self.activation_time = [0] * hoa.num_nodes
        self.visited_fields = [None] * hoa.num_nodes


    def apply_automaton(self, hoa_node, x, y):
        autom = hoa_node.get_automaton()
        auto_type = hoa_node.get_automaton_type()
        prk = None
        if auto_type == "FSM":
            prk = FSMPatRecKernel(autom, self.input_matrix, x, y)
        else:
            prk = HOAPatRecKernel(autom, self.input_matrix, x, y)   

        rec, t, visited = prk.apply()
        return rec, t, visited 


    def apply(self):
        # apply the first automaton
        start_node = self.hoa.nodes[0]
        rec, t, visited = self.apply_automaton(start_node, self.x, self.y)

        if rec:
            # print("First automaton succesfully activated", self.x, self.y)
            self.activation_time[0] = t
            self.visited_fields[0] = visited

            # rescale activation times
            # diff = t - start_node_at
            # for i in range(1, len(self.hoa.nodes)):
            #    at = self.hoa.nodes[i].get_activation_time() + diff
            #    self.activation_time.append(at)

            # print("Rescaled activation times: ", self.activation_time)

            bfs_succesfull = self.bfs()
            if bfs_succesfull:
                v = []
                for i in range(hoa.num_nodes):
                    vf = self.visited_fields[i]
                    if vf == None:
                        print("[Warning] Pattern rezognized with an empty visited_fields[i]")
                    else:
                        v += self.visited_fields[i]
                return True, len(v), v 
            else:
                return False, 0, None
        else:
            return False, 0, None
        

    def bfs(self):
        graph = self.hoa.G

        # start node
        start_node = self.hoa.nodes[0]

        # initialize vector of visited nodes
        num_nodes = self.hoa.num_nodes
        visited_nodes = [False] * num_nodes
        visited_nodes[0] = True

        # initialize bfs queue
        queue = deque()
        succs = graph.successors(start_node)
        for s in succs:
            s_id = s.get_id()
            visited_nodes[s_id] = True
            link_type = graph.edges[start_node, s]["link_type"]
            queue.append((s, 0, link_type))

        link_constraints_to_check = []

        while len(queue) > 0:
            curr, prev_id, link_type = queue.popleft()
            curr_id = curr.get_id()
            prev_visited_fields = self.visited_fields[prev_id]
            
            x, y = self.determine_starting_position(prev_visited_fields, link_type)
            # print("Applying automaton", curr_id, " at", x, y)
            if self.on_table(x, y):
                rec, t, visited_fields = self.apply_automaton(curr, x, y)
                if not rec:
                    # print("Pattern not recognized")
                    return False
                #elif t != self.activation_time[curr_id]:
                #    # print("Pattern recognized but with inappropriate activation time")
                #    return False
                else:
                    self.visited_fields[curr_id] = visited_fields
                    self.activation_time[curr_id] = t

                    # add successor HOA nodes to the queue
                    succs = graph.successors(curr)
                    for s in succs:
                        s_id = s.get_id()
                        link_type = graph.edges[curr, s]["link_type"]
                        if not visited_nodes[s_id]:
                            visited_nodes[s_id] = True
                            queue.append((s, curr_id, link_type))
                        else:
                            link_constraints_to_check.append((curr_id, s_id, link_type))
            else:
                return False

        # print("Checking activation time constraints")
        ok = self.check_activation_time_constraints()
        if not ok:
            return False

        # print("Checking link constraints")
        for cc in link_constraints_to_check:
            if not self.check_link_constraint(cc[0], cc[1], cc[2]):
                print("Link constraint failed: ", cc[0], cc[1], cc[2])
                return False
            
        return True


    def determine_starting_position(self, prev_visited_fields, link_type):
        if link_type == "START":
            x, y = parse_field(prev_visited_fields[0])
            return x, y
        elif link_type in LT_ARRAY:
            x, y = parse_field(prev_visited_fields[-1])
            ind = LT_ARRAY.index(link_type)
            x += dx[ind]
            y += dy[ind]
            return x, y
        else:
            print("[ERROR, determine_starting_position] to fix")
            return -1, -1


    def on_table(self, x, y):
        return x >= 0 and x < self.dimx and y >= 0 and y < self.dimy


    def check_link_constraint(self, auto_i, auto_j, constraint):
        if constraint == "END":
            vf_i = self.visited_fields[auto_i]
            vf_j = self.visited_fields[auto_j]
            return vf_i[-1] == vf_j[-1]
        elif constraint == "INC":
            vf_i = self.visited_fields[auto_i]
            vf_j = self.visited_fields[auto_j]

            for f in vf_i:
                if f in vf_j:
                    return True
                
            for f in vf_j:
                if f in vf_i:
                    return True

            return False
        else:
            print("[ERROR, check_constraint] to fix")
            return False 


    def check_activation_time_constraints(self):
        idat = self.hoa.get_identical_at()
        for k in idat:
            auto_1, auto_2 = k[0], k[1]
            at_1, at_2 = self.activation_time[auto_1], self.activation_time[auto_2]
            if at_1 != at_2:
                # print("AT id constraint failed", auto_1, auto_2, at_1, at_2) 
                return False 

        sidat = self.hoa.get_semi_identical_at()
        for k in sidat:
            auto_1, auto_2 = k[0], k[1]
            at_1, at_2 = self.activation_time[auto_1], self.activation_time[auto_2]
            if at_1 - at_2 != 1:
                # print("AT sid constraint failed", auto_1, auto_2, at_1, at_2)
                return False

        return True


if __name__ == "__main__":
    from Matrix import load_matrix, print_matrix
    from SceneAnalyzer import IdentifyObjects
    from AutomataMemory import AutomataMemory
    from Automaton import learn_simple_concept

    automata_memory = AutomataMemory()

    ok, concept, _, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    concept, matrix = load_matrix('test_files/square.pat')
    hoal = HOALearner(concept, matrix, automata_memory, verbose=True)
    hoa = hoal.learn()
    hoa.print()

    scene_desc, scene_matrix = load_matrix('test_files/scene1.txt')
    print(scene_desc, " LOADED")
    print_matrix(scene_matrix)

    idobj = IdentifyObjects(scene_matrix)
    num_objects = idobj.num_objects()
    for i in range(num_objects):
        mat = idobj.get_object_matrix(i)
        print("\nStarting pattern recognition for: ")
        print_matrix(mat)

        prk = HOAPatRecKernel(hoa, mat, 0, 0)
        rec, t, visited = prk.apply()
        if rec:
            print("pattern recognized, activation time", t, " visited cells", visited)



    




