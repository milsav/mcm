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

from Automaton import FSMPatRecKernel, PatternGraph
from Matrix import neigh, parse_field, dx, dy, coverage
from Matrix import link_type as LT_ARRAY
from SceneAnalyzer import IdentifyObjects
from HOAComparator import HOAComplexityComparator


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
        print(str(self.node_id) + "-" + self.concept)



class HOA:
    def __init__(self, concept):
        self.concept = concept
        self.G = nx.DiGraph()
        self.num_nodes = 0
        self.nodes = []
        self.link_constraints = []
        self.identical_at = []
        self.semi_identical_at = []
        self.HOA_dependencies = []
        self.base_automata_dependencies = []
    
    
    def change_concept_name(self, new_concept_name):
        self.concept = new_concept_name


    def add_node(self, concept, automaton, automaton_type, activation_time):
        node_id = self.num_nodes
        self.num_nodes += 1 
        n = HOANode(node_id, concept, automaton, automaton_type, activation_time)
        self.nodes.append(n)
        self.G.add_node(n)

        if automaton_type == "HOA":
            self.HOA_dependencies.append(concept)
        else:
            self.base_automata_dependencies.append(concept)
        
    
    def add_link(self, src_index, dst_index, move_type, constraints):
        self.G.add_edge(self.nodes[src_index], self.nodes[dst_index], move_type=move_type, constraints=constraints)
        for c in constraints:
            self.link_constraints.append((src_index, dst_index, c))
    
    
    def print(self):
        print("HOA graph for ", self.concept)
        nodes = self.G.nodes()
        for n in nodes:
            n.print()
        print("#links")
        links = self.G.edges()
        for l in links:
            src, dst = l
            print(src.get_id(), "-->", dst.get_id(), "move = ", self.G.edges[l]["move_type"], " constraints = ", self.G.edges[l]["constraints"])

        print("-- link constraints")
        if len(self.link_constraints) == 0:
            print("none")
        else:
            for lc in self.link_constraints:
                print(lc)

        print("-- activation time constraints")
        if len(self.identical_at) == 0 and len(self.semi_identical_at) == 0:
            print("none")
        else:
            for x in self.identical_at:
                print(x[0], x[1], " identical activation time")
            for x in self.semi_identical_at:
                print(x[0], x[1], " semiidentical activation time")

        print("-- HOA dependencies")
        if len(self.HOA_dependencies) == 0:
            print("none")
        else:
            for d in self.HOA_dependencies:
                print(d)

        print("-- TOTAL FSMS involved:", self.total_FSMS())
    

    def connected(self):
        return nx.is_connected(self.G.to_undirected())
    

    def num_nodes(self):
        return self.num_nodes
    
    
    def get_nodes(self):
        return self.nodes
    

    def process_activation_times(self):
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
    

    def get_link_constraints(self):
        return self.link_constraints
    

    def bfs(self):
        ret = []
        for l in nx.bfs_edges(self.G, self.nodes[0]):
            src, dst = l[0], l[1]
            if src not in ret:
                ret.append(src)
            if dst not in ret:
                ret.append(dst)

        return [n.concept for n in ret]
    

    def bfs_links(self):
        ord = nx.bfs_edges(self.G, self.nodes[0])
        return [l[0].concept + "--" + l[1].concept + "--" + self.G.edges[l]["move_type"] for l in ord]
                

    def get_concept_dependencies(self):
        return self.HOA_dependencies
    

    def get_base_concept_dependencies(self):
        return self.base_automata_dependencies 


    def total_FSMS(self):
        fsms_counter = 0
        nodes = self.G.nodes()
        for n in nodes:
            if n.get_automaton_type() == "HOA":
                n_automaton = n.get_automaton()
                fsms_counter += n_automaton.total_FSMS()
            else:
                fsms_counter += 1 
        
        return fsms_counter




"""
Class for learning HOA graphs
"""
class HOALearner:
    def __init__(self, concept, matrix, automata_memory, exclude_concepts=[], verbose=False):
        idobj = IdentifyObjects(matrix)
        if idobj.num_objects() != 1:
            raise Exception("[ERROR, HOALearner] matrix contains multiple objects")

        self.concept = concept
        self.matrix = matrix
        self.verbose = verbose
        self.hoa = HOA(concept)

        self.automata_memory = automata_memory

        # complex concepts that have to be excluded when learning this particular HOA
        self.exclude_concepts = exclude_concepts


    #
    # identify automata that can be activated in pattern matrix
    # 
    def identify_automata(self):
        # set of visited matrix fields
        visited_fields = set()

        # list of activated automata
        self.activated_automata = []

        base_concepts = self.automata_memory.get_base_concepts()
        complex_concepts = self.automata_memory.get_hoa_concepts()

        bfs_order = self.bfs_traversal()
        for start_field in bfs_order:
            i, j = parse_field(start_field)
            
            if self.matrix[i][j] != ' ' and start_field not in visited_fields:
                hoa_activated = self.identify_complex_concepts(i, j, complex_concepts, visited_fields)
                if not hoa_activated:
                    # if HOA activated then skip FSMs
                    self.identify_base_concepts(i, j, base_concepts, visited_fields, start_field)

        if self.verbose:
            if len(self.activated_automata) == 0:
                print("0 automata activated")
            else:
                print("Activated automata: ", ",".join([a[0] for a in self.activated_automata]))
                

        #ok = self.check_visited_fields(visited_fields)
        ok = coverage(visited_fields, self.matrix)
        if not ok:
            raise Exception("[ERROR, HOALearner] matrix contains unvisited fields")

        # create nodes in HOA graph
        for a in self.activated_automata:
            concept, automaton, automaton_type, activation_time = a[0], a[1], a[2], a[4]
            self.hoa.add_node(concept, automaton, automaton_type, activation_time)

        # derive activation time constraints
        self.hoa.process_activation_times()


    """
    BFS-traversal for pattern matrix
    """
    def bfs_traversal(self):
        pg = PatternGraph(self.matrix)
        ret = []
        for l in nx.bfs_edges(pg.G, pg.first_node):
            src, dst = l[0], l[1]
            if src not in ret:
                ret.append(src)
            if dst not in ret:
                ret.append(dst)

        return ret


    """
    identify complex concepts that can be recognized by existing HOAs 
    """    
    def identify_complex_concepts(self, i, j, complex_concepts, visited_fields):
        # identify complex concepts (HOAs)
        activated = []
        
        for concept in complex_concepts:
            # skip excluded concepts
            if concept in self.exclude_concepts:
                #print("Excluding: ", concept)
                continue

            for hoa in self.automata_memory.get_automata(concept):
                # apply pattern recognition for current HOA
                prk = HOAPatRecKernel(hoa, self.matrix, i, j)
                rec, t, visited = prk.apply()
            
                if rec:
                    if self.verbose:
                        print("Activation [complex] ", visited, ", HOA: ", concept)
                    
                    # skip concepts that partially covers visisted fileds
                    if self.overlap(visited, visited_fields):
                        continue

                    activated.append([concept, hoa, "HOA", visited, t])


        # select one of activated HOAS
        total_activated = len(activated)
        if total_activated > 0:
            if total_activated > 1:
                activated.sort(reverse=True, key=lambda x: x[4])
            
            selected = activated[0]
            
            if total_activated > 1 and activated[0][4] == activated[1][4]:
                # tie resolution
                num_ties = 1                
                while num_ties < total_activated and activated[0][4] == activated[num_ties][4]:
                    num_ties += 1

                # print("#TIES ", num_ties)
                # for i in range(num_ties):
                #    print(activated[i][0])
                
                the_best = 0
                for curr in range(1, num_ties):
                    hoa_a, hoa_b = activated[the_best][1], activated[curr][1]
                    hcc = HOAComplexityComparator(hoa_a, hoa_b)
                    cmp = hcc.compare()
                    if cmp < 0:
                        the_best = curr

                selected = activated[the_best]
                # print("Selected HOA", activated[the_best][0])

            visited = selected[3]
            for v in visited:
                visited_fields.add(v)

            self.activated_automata.append(selected)
            return True

        return False 
    

    def overlap(self, set1, set2):
        for s in set1:
            if s in set2:
                return True
            
        return False


    """
    identify base concepts that can be recognized by existing FSMs
    """
    def identify_base_concepts(self, i, j, base_concepts, visited_fields, start_field):
        # identify base concepts (FSMS)
        for concept in base_concepts:
            for automaton in self.automata_memory.get_automata(concept): 
                prk = FSMPatRecKernel(automaton, self.matrix, i, j)
                rec, t, visited = prk.apply()
                if rec:
                    # check valid activations
                    # an activation is valid if it covers at least one unvisited field
                    valid_activation = False
                    for v in visited:
                        if v != start_field and not v in visited_fields:
                            valid_activation = True
                            break

                    if valid_activation:
                        if self.verbose:
                            print("Activation [simple] ", visited, ", FSM: ", concept)
                        
                        for v in visited:
                            visited_fields.add(v)
                        
                        self.activated_automata.append([concept, automaton, "FSM", visited, t])
                        break


    """
    identify dependencies between activated automata (links in HOA graphs)
    """
    def infere_automata_dependencies(self):
        for j in range(1, len(self.activated_automata)):
            for i in range(j):
                #print("Infering automata dependencies for ", i, j)
                vf_i = self.activated_automata[i][3]
                vf_j = self.activated_automata[j][3]
                #print(vf_i)
                #print(vf_j)

                move_dependency = self.infere_move_dependency(vf_i, vf_j)
                #print("MOVE DEPS:", move_dependency)

                link_constraints = self.infere_link_constraints(vf_i, vf_j)
                #print("LINK CONS:", link_constraints)

                if move_dependency != None or link_constraints != []:
                    if move_dependency == None:
                        move_dependency = "NONE"

                    self.hoa.add_link(i, j, move_dependency, link_constraints)
    
        # check HOA connectedness
        if not self.hoa.connected():
            raise Exception("[ERROR, HOALearner] HOA graph not connected")


    # vf_i -- visited fields by automata i, vf_j -- visited fields by automata j
    def infere_move_dependency(self, vf_i, vf_j):
        i_start, i_end = vf_i[0], vf_i[-1]
        j_start = vf_j[0]

        if i_start == j_start:
            # automata i and j have identical starting positions
            return "START"
        
        # automaton j starts after automata i 
        nei, move = neigh(j_start, i_end)
        if nei:
            return move
        
        # automata i and j starts at adjacent positions
        nei, move = neigh(j_start, i_start)
        if nei:
            return "START_" + move

        # automaton j starts at/around some middle field marked by automata i
        incidences = []
        for k in range(1, len(vf_i) - 1):
            f_i = vf_i[k]
            nei, move = neigh(j_start, f_i)
            if nei:
                incidences.append("INC_" + move)

        if len(incidences) > 0:
            selinc = min(incidences, key=len)
            return selinc

        return None


    # the same arguments as for infere_move_dependency
    def infere_link_constraints(self, vf_i, vf_j):
        i_end, j_end = vf_i[-1], vf_j[-1]

        if i_end == j_end:
            # both automata ends at same position
            return ["END"]
        
        # automaton j ends at/around some middle field marked by automata i
        incidences = []
        for k in range(1, len(vf_i) - 1):
            f_i = vf_i[k]
            nei, move = neigh(j_end, f_i)
            if nei:
                incidences.append("INC_" + move)
        
        return incidences


    """
    SVC: moved to Matrix.py
    
    check whether all fields are visited
    
    def check_visited_fields(self, visited_fields):
        for i in range(self.dim_x):
            for j in range(self.dim_y): 
                f = self.matrix[i][j]
                f_str = str(i) + "-" + str(j)
                if f != ' ' and f_str not in visited_fields:
                    return False
                
        return True
    """


    """
    learning entry point
    """
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
        self.all_visisted_fields = []

        # activation history
        self.activated_nodes = list()
        self.time_constraints_satisfied = list()
        self.link_constraints_satisfied = list()


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
            #print("First automaton succesfully activated", self.x, self.y)
            self.activation_time[0] = t
            self.visited_fields[0] = visited
            self.all_visisted_fields.extend(visited)
            self.activated_nodes.append(start_node.get_id())

            # do bfs
            bfs_succesfull = self.bfs()
            if bfs_succesfull:
                return True, len(self.all_visisted_fields), self.all_visisted_fields
            else:
                return False, len(self.all_visisted_fields), self.all_visisted_fields
        else:
            return False, t, visited        
    
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
            move_type = graph.edges[start_node, s]["move_type"]
            if move_type != "NONE":
                #print("BFS queue initialization -- ", s_id, move_type)
                visited_nodes[s_id] = True
                queue.append((s, 0, move_type))


        while len(queue) > 0:
            curr, prev_id, move_type = queue.popleft()
            curr_id = curr.get_id()
            prev_visited_fields = self.visited_fields[prev_id]
            
            positions = self.determine_starting_position(prev_visited_fields, move_type, curr)
            num_positions = len(positions)
            #print("Positions == ", positions)
            #print(num_positions)

            if num_positions == 0:
                return False
            
            x, y = positions[-1][0], positions[-1][1]


            """
            if num_positions != 1:
                return False
            
            x, y = positions[0][0], positions[0][1]
            """

            #print("Applying automaton", curr_id, " at", x, y)
            if self.on_table(x, y):
                rec, t, visited_fields = self.apply_automaton(curr, x, y)
                if not rec:
                    #print("Automaton failed...")
                    return False
                else:
                    #print("Automaton passed...")
                    #print("Visited fields:", visited_fields)
                    
                    # mark the current node as visited
                    self.visited_fields[curr_id] = visited_fields
                    self.all_visisted_fields.extend(visited_fields)
                    self.activation_time[curr_id] = t

                    # update activation history
                    self.activated_nodes.append(curr_id)

                    # add successor HOA nodes to the queue
                    succs = graph.successors(curr)
                    for s in succs:
                        s_id = s.get_id()
                        move_type = graph.edges[curr, s]["move_type"]
                        
                        #print("Processing successor ", s_id, "--->", move_type)

                        if move_type != "NONE":
                            if not visited_nodes[s_id]:
                                visited_nodes[s_id] = True
                                queue.append((s, curr_id, move_type))
            else:
                return False

        # print("Checking activation time constraints")
        time_constraints_ok = self.check_activation_time_constraints()
        
        # print("Checking link constraints")
        link_constraints_ok = True
        for cc in self.hoa.link_constraints:
            if not self.check_link_constraint(cc[0], cc[1], cc[2]):
                link_constraints_ok = False
            else:
                self.link_constraints_satisfied.append(cc)


        return time_constraints_ok and link_constraints_ok



    def determine_starting_position(self, prev_visited_fields, move_type, automaton_node):
        if move_type == "START":
            x, y = parse_field(prev_visited_fields[0])
            return [[x, y]]
        elif move_type.startswith("START_"):
            mt = move_type[6:]
            x, y = parse_field(prev_visited_fields[0])
            ind = LT_ARRAY.index(mt)
            x += dx[ind]
            y += dy[ind]
            return [[x, y]]
        elif move_type in LT_ARRAY:
            x, y = parse_field(prev_visited_fields[-1])
            ind = LT_ARRAY.index(move_type)
            x += dx[ind]
            y += dy[ind]
            return [[x, y]]
        else:
            # print("Move type = ", move_type)
            # print("Automaton", automaton_node.get_id(), " concept", automaton_node.get_concept())
            
            positions = []

            move = None
            try:
                ui = move_type.index("_")
                move = move_type[(ui + 1):]
            except ValueError:
                pass

            # print("Move = ", move)
            
            for i in range(1, len(prev_visited_fields) - 1):
                x, y = parse_field(prev_visited_fields[i])
                if move != None:
                    ind = LT_ARRAY.index(move)
                    x += dx[ind]
                    y += dy[ind]

                field = str(x) + "-" + str(y)
                if field in self.all_visisted_fields:
                    # print("SKIP", field)
                    continue

                # print("Trying automaton at", x, y)
                if self.on_table(x, y):
                    rec, _, _ = self.apply_automaton(automaton_node, x, y)
                    if rec:
                        positions.append([x, y])

            return positions


    def on_table(self, x, y):
        return x >= 0 and x < self.dimx and y >= 0 and y < self.dimy


    def check_link_constraint(self, auto_i, auto_j, constraint):
        #print("Checking: ", auto_i, auto_j, constraint)
        #print(self.visited_fields[auto_i])
        #print(self.visited_fields[auto_j])
        
        vf_i = self.visited_fields[auto_i]
        vf_j = self.visited_fields[auto_j]
        
        if constraint == "END":
            return vf_i[-1] == vf_j[-1]
        elif constraint.startswith("INC_"):
            end_type = constraint[constraint.index("_") + 1:]
            # print(end_type)
            
            j_end = vf_j[-1]
            for k in range(1, len(vf_i) - 1):
                f_i = vf_i[k]
                nei, move = neigh(j_end, f_i)
                if nei and move == end_type:
                    return True
            
            return False
        else:
            print("[ERROR, check_constraint] to fix")
            print("Constraint = ", constraint)
            return False 


    def check_activation_time_constraints(self):
        constraints_satisfied = True

        idat = self.hoa.get_identical_at()
        for k in idat:
            auto_1, auto_2 = k[0], k[1]
            at_1, at_2 = self.activation_time[auto_1], self.activation_time[auto_2]
            if at_1 != at_2:
                # print("AT id constraint failed", auto_1, auto_2, at_1, at_2) 
                constraints_satisfied = False
            else:
                self.time_constraints_satisfied.append(("ID", auto_1, auto_2)) 

        sidat = self.hoa.get_semi_identical_at()
        for k in sidat:
            auto_1, auto_2 = k[0], k[1]
            at_1, at_2 = self.activation_time[auto_1], self.activation_time[auto_2]
            if at_1 - at_2 != 1:
                # print("AT sid constraint failed", auto_1, auto_2, at_1, at_2)
                constraints_satisfied = False
            else:
                self.time_constraints_satisfied.append(("SID", auto_1, auto_2))

        return constraints_satisfied
    

    def print_activation_history(self):
        print("---- Activation history")
        print("# activated nodes", len(self.activated_nodes), " # total nodes = ", self.hoa.num_nodes)
        for node_id in self.activated_nodes:
            node = self.hoa.nodes[node_id]
            concept = node.get_concept()
            print("Activated", node_id, concept)

        total_time_constraints = len(self.hoa.get_identical_at()) + len(self.hoa.get_semi_identical_at())
        print("# time constraints passed", len(self.time_constraints_satisfied), " # total constraints = ", total_time_constraints)
        for c in self.time_constraints_satisfied:
            print(c)

        total_link_constraints = len(self.hoa.get_link_constraints())
        print("# link constraints passed", len(self.link_constraints_satisfied), "# total constraints = ", total_link_constraints)
        for c in self.link_constraints_satisfied:
            print(c)


    def activation_score(self, activated_nodes_factor=0.7, link_constraints_factor=0.2, time_constraints_factor=0.1):
        f_an = len(self.activated_nodes) / self.hoa.num_nodes        
        f_tc = self.ac_divide(len(self.time_constraints_satisfied), len(self.hoa.get_identical_at()) + len(self.hoa.get_semi_identical_at()))
        f_lc = self.ac_divide(len(self.link_constraints_satisfied), len(self.hoa.get_link_constraints())) 
        return f_an * activated_nodes_factor + f_tc * time_constraints_factor + f_lc * link_constraints_factor
        

    def ac_divide(self, a, b):
        return 1 if b == 0 else a / b


def learn_HOA(concept, matrix, automata_memory, exclude_concepts=[], verbose=False):
    try:
        hoal = HOALearner(concept, matrix, automata_memory, exclude_concepts=exclude_concepts, verbose=verbose)
        hoa = hoal.learn()
        if verbose:
            hoa.print() 

        if hoa.num_nodes == 0:
            raise Exception("[ERROR, HOALearner] empty hoa due to unknown base concepts")

        #automata_memory.add_automata_to_memory(concept, False, [hoa], matrix)
        return True, hoa, "OK"
    except Exception as error:
        #print("Learning ", concept, "failed, error: ", error)
        return False, None, "Learning " + concept + " failed: " + str(error)


def learn_complex_concept(concept, matrix, automata_memory, exclude_concepts=[], verbose=False):
    ok, hoa, msg = learn_HOA(concept, matrix, automata_memory, exclude_concepts=exclude_concepts, verbose=verbose)
    if ok:
        automata_memory.add_automata_to_memory(concept, False, [hoa], matrix)
        return True, "OK"
    
    return False, msg
    
    """
    try:
        hoal = HOALearner(concept, matrix, automata_memory, exclude_concepts=exclude_concepts, verbose=verbose)
        hoa = hoal.learn()
        if verbose:
            hoa.print() 

        if hoa.num_nodes == 0:
            raise Exception("[ERROR, HOALearner] empty hoa due to unknown base concepts")

        automata_memory.add_automata_to_memory(concept, False, [hoa], matrix)
        return True, "OK"
    except Exception as error:
        #print("Learning ", concept, "failed, error: ", error)
        return False, "Learning " + concept + " failed: " + str(error)
    """




if __name__ == "__main__":
    from Matrix import load_matrix
    from AutomataMemory import AutomataMemory
    from Automaton import learn_simple_concept
    from InferenceEngine import inference

    automata_memory = AutomataMemory()

    ok, concept, pattern_matrix, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, pattern_matrix)

    ok, concept, pattern_matrix, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, pattern_matrix)

    print("\n\n------------ LEARNING SQUARE")
    concept, matrix = load_matrix('test_files/square.pat')
    ok, msg = learn_complex_concept(concept, matrix, automata_memory, verbose=True)
    if not ok:
        print(msg)

    print("\n\n------------ LEARNING SQUARE CROSS")
    concept, matrix = load_matrix('test_files/square_cross.pat')
    ok, msg = learn_complex_concept(concept, matrix, automata_memory, verbose=True)
    if not ok:
        print(msg)

    print("\n\n------------ LEARNING TRIANGLE")
    concept, matrix = load_matrix('test_files/triangle.pat')
    ok, msg = learn_complex_concept(concept, matrix, automata_memory, verbose=True)
    if not ok:
        print(msg)

    print("\n\n------------ AUTOMATA MEMORY")
    automata_memory.info()

    inference('test_files/scene1.txt', automata_memory)