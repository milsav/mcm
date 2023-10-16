# Meta-cognitive machines
#
# Automaton module constains functions and classes 
# for pattern recognition based on finite-state-machines 
# constructed from 2D matrix patterns
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

import sys
import networkx as nx
from Matrix import dx, dy, link_type, load_matrix


"""
Objects of PatternGraph are pattern graphs. Nodes in pattern
graphs are non-empty symbols in the pattern matrix identified by 
their coordinates, while two nodes are connected if they are
adjacent considering the Moore neighboorhood
"""
class PatternGraph:
    def __init__(self, mat):
        # a concept is simple if its pattern graph has clear starting nodes for FSM-based pattern recognition
        self.simple_concept = True

        dimx = len(mat)
        dimy = len(mat[0])

        self.G = nx.DiGraph()
        self.first_node = None

        for i in range(dimx):
            for j in range(dimy):
                if mat[i][j] != ' ':
                    node_id = str(i) + "-" + str(j)
                    self.G.add_node(node_id, x=i, y=j, symbol=mat[i][j])
                    if self.first_node == None:
                        self.first_node = node_id

        for i in range(dimx):
            for j in range(dimy):
                if mat[i][j] != ' ':
                    current_id = str(i) + "-" + str(j)
                    for k in range(len(dx)):
                        nei_x = i + dx[k]
                        nei_y = j + dy[k]
                        in_range = nei_x >= 0 and nei_x < dimx and nei_y >= 0 and nei_y < dimy
                        if in_range and mat[nei_x][nei_y] != ' ':
                            nei_id = str(nei_x) + "-" + str(nei_y)
                            self.G.add_edge(current_id, nei_id, link_type=link_type[k])

        self.connected = nx.is_connected(self.G.to_undirected())
        if not self.connected:
            # print("[PatternGraph, error] Pattern not connected")
            self.simple_concept = False
            return
        
        self.start_nodes = self.determine_start_nodes()
        if len(self.start_nodes) == 0:
            # print("[PatternGraph, warning] Pattern does not have clear starting nodes")
            self.simple_concept = False
            
        #print("START-NODES = ", self.start_nodes)


    def is_concept_simple(self):
        return self.simple_concept


    def determine_start_nodes(self):
        sn = []
        for n in self.G.nodes():
            indeg = self.G.in_degree(n)
            if indeg == 0:
                print("[PatternGraph, warning] found node with in-degree 0")
            elif indeg == 1:
                sn.append(n)

        return sn


    def print(self):
        print("\nPattern graph:")
        for n in self.G.nodes():
            print(n, self.G.nodes[n]["x"], self.G.nodes[n]["y"], self.G.nodes[n]["symbol"])
        
        for l in self.G.edges():
            print(l, self.G.edges[l]["link_type"])


    def dfs(self, node, verbose_results=False):
        self.visited = set()
        self.sequences = []
        self.return_back = [None]
        self.sequence = []
        self.dfs_parent = dict()
        
        self.visited.add(node)
        self.dfs_parent[node] = None
        self.dfsRec(node)
        
        if verbose_results:
            print("Sequences")
            for s in self.sequences:
                print(s)

            for i in range(len(self.sequences)):
                s = self.sequences[i]
                print("\nSequence ", s, " index = ", i)
            
                if i > 0:
                    curr = s[0]
                    curr_symbol = self.G.nodes[curr]["symbol"]

                    prev = self.dfs_parent[curr]
                    prev_symbol = self.G.nodes[prev]["symbol"]

                    move = self.G.edges[prev, curr]["link_type"]
                    print("PREV = ", prev)
                    print("RETURN_BACK_SEQUENCE = ", self.return_back[i])
                    print("Sequence transition: ", move, prev_symbol, curr_symbol)
            
                for i in range(0, len(s) - 1):
                    curr = s[i]
                    curr_symbol = self.G.nodes[curr]["symbol"]
                    next = s[i + 1]
                    next_symbol = self.G.nodes[next]["symbol"]
                    move = self.G.edges[curr, next]["link_type"]

                    print("Transition: ", move, curr_symbol, next_symbol)

        return self.sequences, self.dfs_parent, self.return_back    


    def dfsRec(self, curr):
        self.sequence.append(curr)
        sequence_index = len(self.sequences)
        prev = self.dfs_parent[curr]
        transition_move = None
        if prev != None:
            transition_move = self.G.edges[prev, curr]["link_type"]

        neis = self.G.neighbors(curr)
        
        last_append = None
        move_forward = []
        for n in neis:
            if not n in self.visited:
                forward_move = self.G.edges[curr, n]["link_type"]
                if transition_move != None and forward_move == transition_move:
                    last_append = n
                else:
                    move_forward.append(n)
        
        if last_append != None:
            move_forward.append(last_append)

        nmf = len(move_forward)
        if nmf == 0:
            self.sequences.append(self.sequence.copy())
            self.sequence = []
        elif nmf == 1:
            fnode = move_forward[0]
            self.visited.add(fnode)
            self.dfs_parent[fnode] = curr
            self.dfsRec(fnode)
        else:
            self.sequences.append(self.sequence.copy())
            for n in move_forward:
                if not n in self.visited:
                    self.sequence = []
                    self.return_back.append(sequence_index)
                    self.visited.add(n)
                    self.dfs_parent[n] = curr
                    self.dfsRec(n)


class FSMSymbol:
    def __init__(self, move, next_symbol):
        self.move = move
        self.next_symbol = next_symbol

    def __eq__(self, other):
        return self.next_symbol == other.next_symbol and self.move == other.move
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return "<" + self.move + "," + self.next_symbol + ">"


EMPTY_FSM_SYMBOL = FSMSymbol('EMPTY', '')    


class FSMState:
    def __init__(self, name):
        self.name = name
        self.transitions = []


    def add_transition(self, fsm_symbol, next_state):
        self.transitions.append((fsm_symbol, next_state))


    def print(self):
        print("State ", self.name)
        for t in self.transitions:
            print(t[0], " --> ", t[1].name)


class FSM:
    def __init__(self, activating_symbol):
        self.activating_symbol = activating_symbol
        self.num_states = 0
        self.states = []
        

    def create_state(self):
        name = "S_" + str(self.num_states)
        self.num_states += 1
        state = FSMState(name)
        self.states.append(state)
        return state 
    

    def print(self):
        print("Activating symbol = ", self.activating_symbol)
        print("Num states        = ", self.num_states)
        if self.num_states != 0:
            print("Start state       = ", self.states[0].name)
            for s in self.states:
                s.print()


    def set_id(self, id):
        self.fsm_id = id


class FSMLearner:
    def __init__(self, pattern_graph, start_node, verbose=False):
        self.pattern_graph = pattern_graph
        self.start_node = start_node
        self.sequences, self.dfs_parent, self.return_back = self.pattern_graph.dfs(start_node, verbose_results=verbose)
        

    def learn(self):
        activating_symbol = self.pattern_graph.G.nodes[self.start_node]["symbol"]
        self.fsm = FSM(activating_symbol)
        self.start_states = []
        self.end_states = []
        num_sequences = len(self.sequences)

        for seq_index in range(num_sequences):
            s = self.sequences[seq_index]

            fsmsym_seq = self.create_fsmsymbol_sequence(s)
            
            # list of local states for the current sequence
            local_states = []

            if len(fsmsym_seq) == 0:
                singleton_state = self.fsm.create_state()
                local_states.append(singleton_state)
                self.start_states.append(singleton_state)
                self.end_states.append(singleton_state)
            else:
                repetition_period = self.is_repetition_sequence(fsmsym_seq) 
                if repetition_period == 0:
                    red_seq, rep = self.reduce_fsmsymbol_sequence(fsmsym_seq)
                    
                    for i in range(len(red_seq) + 1):
                        local_states.append(self.fsm.create_state())

                    for i in range(len(local_states) - 1):
                        if i > 0 and rep[i - 1]:
                            local_states[i].add_transition(red_seq[i - 1], local_states[i])
                        local_states[i].add_transition(red_seq[i], local_states[i + 1])

                    # back loop if the last fsm symbol repeats
                    if rep[-1]:
                        local_states[-1].add_transition(red_seq[-1], local_states[-1])
                else:
                    local_seq = fsmsym_seq[:repetition_period]
                    #print("Localized sequence: ", "".join([str(s) for s in local_seq]))
                    for i in range(len(local_seq) + 1):
                        local_states.append(self.fsm.create_state())

                    for i in range(len(local_states) - 1):
                        local_states[i].add_transition(local_seq[i], local_states[i + 1])
                    local_states[-1].add_transition(local_seq[0], local_states[1])

                self.start_states.append(local_states[0])
                self.end_states.append(local_states[-1])

            # connect local automaton with one of previously created local automata
            if seq_index > 0:
                transition_move = self.determine_transition_move(s)
                ret_back_index = self.return_back[seq_index]
                previous_state = self.end_states[ret_back_index]
                start_state = local_states[0]
                previous_state.add_transition(transition_move, start_state)
                
        # create empty transitions        
        for seq_index in range(1, num_sequences - 1):
            ret_back_index = self.return_back[seq_index]
            previous_state = self.end_states[ret_back_index]
            end_state = self.end_states[seq_index]
            end_state.add_transition(EMPTY_FSM_SYMBOL, previous_state)

        return self.fsm


    def create_fsmsymbol_sequence(self, s):
        symbol_seq = []
        for i in range(0, len(s) - 1):
            curr = s[i]
            next = s[i + 1]
            next_symbol = self.pattern_graph.G.nodes[next]["symbol"]
            move = self.pattern_graph.G.edges[curr, next]["link_type"]

            symbol_seq.append(FSMSymbol(move, next_symbol))

        return symbol_seq
    

    # identify consecutive repetitions in fsmsymbol sequences
    # (those repetitions are represented by loops in FSMs)
    def reduce_fsmsymbol_sequence(self, s):
        length = len(s)
        i = 0
        symbol_seq = []
        repetition = []
        
        while i < length:
            curr = s[i]
            if i < length - 1 and s[i + 1] == curr:
                symbol_seq.append(curr)
                repetition.append(True)
                while i < length and s[i] == curr:
                    i += 1
            else:
                symbol_seq.append(curr)
                repetition.append(False)
                i += 1

        if len(symbol_seq) != len(repetition):
            print("[WARNING], reduce_fsmsymbol_sequence, len(symbol_seq) != len(repetition)")

        return symbol_seq, repetition


    
    # the function checks whether the sequence is repetative and it returns repetition period
    # if the repetition period is equal to 0 then we do not have repetitions
    def is_repetition_sequence(self, s):
        length = 1
        while length <= len(s) // 2:
            start = s[:length]
            rest = s[length:]
            l_start = len(start)
            l_rest = len(rest)
            rep_seq = True
            if l_rest % l_start == 0:
                shift = 0
                while shift <= l_rest - l_start:
                    match = True
                    for k in range(l_start): 
                        if rest[shift + k] != start[k]:
                            match = False
                            break

                    if match:
                        shift += l_start
                    else:
                        rep_seq = False
                        break
            else:
                rep_seq = False
            
            if rep_seq:
                return length
            else:
                length += 1
        
        return 0
            

    # determine transition move that activates sequence
    def determine_transition_move(self, sequence):
        start = sequence[0]
        prev = self.dfs_parent[start]
        prev_symbol = self.pattern_graph.G.nodes[prev]["symbol"]
        move = self.pattern_graph.G.edges[prev, start]["link_type"]
        return FSMSymbol(move, prev_symbol)      


"""
Objects of FSMPatRecKernel perform FSM-based pattern recognition for
given fsm, input matrix and starting coordinates 
"""
class FSMPatRecKernel:
    def __init__(self, fsm, input_matrix, x, y):
        self.fsm = fsm
        self.input_matrix = input_matrix
        self.x = x
        self.y = y
        self.dimx = len(input_matrix)
        self.dimy = len(input_matrix[0])


    def apply(self):
        startsym = self.input_matrix[self.x][self.y]
        if startsym == self.fsm.activating_symbol:
            state = self.fsm.states[0]
            self.end_state = self.fsm.states[-1]
            self.active_time = 0
            self.visited = []
            self.activated_states = set()
            recognized = self.applyRec(state, self.x, self.y)
            return recognized, self.active_time, self.visited
        else:
            return False, 0, None


    def pattern_recognized(self):
        return len(self.activated_states) == len(self.fsm.states)


    def applyRec(self, state, x, y):
        while (True):
            #print(state.name, x, y)
            self.active_time += 1
            self.visited.append(str(x) + "-" + str(y))
            self.activated_states.add(state.name)
        
            num_trans = len(state.transitions)
            feasible_trans, empty_present, selfloop_present = self.determine_feasible_transitions(x, y, state)
            num_feasible_trans = len(feasible_trans)
            #print(num_feasible_trans)

            if num_feasible_trans == 0:
                if empty_present:
                    if num_trans == 1 or (num_trans == 2 and selfloop_present):
                        return True
                    else:
                        return False
                else:
                    return self.pattern_recognized()
            else:
                # print("State: ", state.name, num_trans, num_feasible_trans, empty_present, selfloop_present, " coords: ", x, y)
                if not selfloop_present:
                    diff = 1 if empty_present else 0
                    if num_feasible_trans + diff != num_trans:
                        return False

                if num_feasible_trans == 1:
                    ftran = feasible_trans[0]
                    x, y, state = ftran[0], ftran[1], ftran[2]
                else:
                    for f in feasible_trans:
                        next_x, next_y, next_state = f[0], f[1], f[2]
                        if next_state != state:
                            ok = self.applyRec(next_state, next_x, next_y)
                            if not ok:
                                return False
                        
                    return True
                

    def next_x_y(self, x, y, move):
        ind = link_type.index(move)
        if ind == -1:
            print("[FATAL ERROR] Unknown moving type", move)
            return None
        
        return x + dx[ind], y + dy[ind]


    def on_table(self, x, y):
        return x >= 0 and x < self.dimx and y >= 0 and y < self.dimy
    

    def determine_feasible_transitions(self, x, y, state):
        possible_trans = state.transitions
        feasible_trans = []
        empty_present = False
        selfloop_present = False

        for tran in possible_trans:
            fsm_symbol = tran[0]
            next_state = tran[1]
            move = fsm_symbol.move
            next_symbol = fsm_symbol.next_symbol

            if fsm_symbol != EMPTY_FSM_SYMBOL:
                next_x, next_y = self.next_x_y(x, y, move)
                if next_state == state:
                    selfloop_present = True
                if self.on_table(next_x, next_y) and self.input_matrix[next_x][next_y] == next_symbol:
                    feasible_trans.append((next_x, next_y, next_state))
            else:
                empty_present = True

        return feasible_trans, empty_present, selfloop_present


def learn_simple_concept_from_matrix(pattern_matrix, verbose=False):
    fsms = []

    pg = PatternGraph(pattern_matrix)
    if not pg.is_concept_simple():
        return False, pg, []
    
    start_nodes = pg.start_nodes
    for sn in start_nodes:
        l = FSMLearner(pg, sn) 
        fsm = l.learn()
        
        if verbose: 
            print("Learned FSM")
            fsm.print()

        fsms.append(fsm)

    if verbose:
        print("Total FSMs", len(fsms))

    return True, pg, fsms


def learn_simple_concept(pattern_matrix_file, verbose=False):
    concept, pattern_matrix = load_matrix(pattern_matrix_file)
    ok, pg, fsms = learn_simple_concept_from_matrix(pattern_matrix, verbose)
    return ok, concept, pattern_matrix, pg, fsms


#
# python3 Automaton.py -pat horizontal_line.pat vertical_line.pat left_angle.pat right_angle.pat t.pat -sc scene2.txt
#
if __name__ == "__main__":
    from Matrix import load_matrix, print_matrix, parse_field
    from SceneAnalyzer import IdentifyObjects

    args = sys.argv[1:]
    
    if ("-pat" not in args or "-sc" not in args) and "-h" not in args:
        print("Arguments not formated correctly, use -h for help")
    elif "-h" in args:
        print("Help:")
        print("After -pat add all patterns")
        print("After -sc add ONE scene (if you add more than one last one will be taken)")
    else:
        patterns = []
        scene = None

        is_pat = False
        for i in range(len(args)):
            if args[i] == "-pat":
                is_pat = True
            elif args[i] == "-sc":
                is_pat = False
            else:
                if is_pat:
                    patterns.append(args[i])
                else:
                    scene = args[i]
            i += 1

        print("pats:", patterns)
        print("scene:", scene)

        learned_concepts = dict()

        for pat in patterns:
            ok, concept, _, _, fsms = learn_simple_concept('test_files/' + pat, verbose=True)
            learned_concepts[concept] = fsms

        print("learned concepts", learned_concepts)
        scene_desc, scene_matrix = load_matrix('test_files/' + scene)
        print(scene_desc, " LOADED")
        print_matrix(scene_matrix)

        idobj = IdentifyObjects(scene_matrix)
        num_objects = idobj.num_objects()
        for i in range(num_objects):
            mat = idobj.get_object_matrix(i)
            print("\n\n\nStarting pattern recognition for: ")
            print_matrix(mat)
        
            pg = PatternGraph(mat)
            starts = pg.start_nodes

            for start in starts:
                x, y = parse_field(start)
                print("\nApplying automata at", x, y)
                for concept in learned_concepts:
                    fsms = learned_concepts[concept]
                    noauto = len(fsms)
                    for k in range(noauto):
                        fsm = fsms[k]
                        pkr = FSMPatRecKernel(fsm, mat, x, y)
                        rec, _, _ = pkr.apply()
                        if rec:
                            print(concept, "recognized by automata", k)


            """
            for name, fsms in learned_concepts.items():
                for fsm in fsms:
                    pkr = FSMPatRecKernel(fsm, mat, 0, 0)
                    rec, _, _ = pkr.apply()
                    if rec:
                        print(name, "recognized")
            """



# LAST SVC MAIN
"""
if __name__ == "__main__":
    from Matrix import load_matrix, print_matrix
    from SceneAnalyzer import IdentifyObjects

    ok, concept, _, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    hl_fsm = fsms[0]
    
    ok, concept, _, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    vl_fsm = fsms[0]

    ok, concept, _, _, fsms = learn_simple_concept('test_files/t.pat', verbose=False)
    t_fsm = fsms[0]

    scene_desc, scene_matrix = load_matrix('test_files/scene2.txt')
    print(scene_desc, " LOADED")
    print_matrix(scene_matrix)

    idobj = IdentifyObjects(scene_matrix)
    num_objects = idobj.num_objects()
    for i in range(num_objects):
        mat = idobj.get_object_matrix(i)
        print("\nStarting pattern recognition for: ")
        print_matrix(mat)
        
        prk = FSMPatRecKernel(hl_fsm, mat, 0, 0)
        rec, _, _ = prk.apply()
        if rec:
            print("horizontal line recognized")

        prk = FSMPatRecKernel(vl_fsm, mat, 0, 0)
        rec, _, _ = prk.apply()
        if rec:
            print("vertical line recognized")

        prk = FSMPatRecKernel(t_fsm, mat, 0, 0)
        rec, _, _ = prk.apply()
        if rec:
            print("T recognized")
"""


"""
OLD-MAINS (for testing purposes)


if __name__ == "__main__":
    automataDB = dict()
    ok, concept_vl, mat_vl, pg_vl, fsms_vl = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automataDB[concept_vl] = fsms_vl

    ok, concept_hl, mat_hl, pg_hl, fsms_hl = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automataDB[concept_hl] = fsms_hl

    ok, concept_s, mat_s, pg_s, fsms_s = learn_simple_concept('test_files/square.pat', verbose=False)
    print(ok)

    visited_fields = set()
    activated_automata = []

    for i in range(len(mat_s)):
        for j in range(len(mat_s[0])):
            start_field = str(i) + "-" + str(j)
            if mat_s[i][j] != ' ' and start_field not in visited_fields:
                for concept in automataDB:
                    for automata in automataDB[concept]: 
                        prk = FSMPatRecKernel(automata, mat_s, i, j)
                        rec, t, visited = prk.apply()
                        if rec:
                            # check valid activations
                            valid_activation = False
                            for v in visited:
                                if v != start_field and not v in visited_fields:
                                    valid_activation = True
                                    break

                            if valid_activation:
                                last_field = visited[-1]
                                #print("Activated automata for ", concept, " start = ", start_field, "end = ", last_field, "time = ", t)
                                for v in visited:
                                    visited_fields.add(v)

                                activated_automata.append([concept, automata, start_field, last_field])
                            

    for aa in activated_automata:
        print(aa[0])
        print(aa[1].print())
        print(aa[2])
        print(aa[3])

        print("\n")



if __name__ == "__main__":
    concept, mat = load_pattern_matrix('test_files/line1.pat')

    fsms = []

    pg = PatternGraph(mat)
    start_nodes = pg.start_nodes
    for sn in start_nodes:
        l = FSMLearner(pg, sn) 
        fsm = l.learn()

        print("\nLearned FSM")
        fsm.print()

        fsms.append(fsm)

    print("Total automata", len(fsms))

    print("\nRND test")
    rnd_mat = create_random_matrix(15, 15, 0.4, 'x')
    print_matrix(rnd_mat)

    cnt = 0
    for fsm in fsms:
        print("Testing automata", cnt)
        cnt += 1
        for x in range(len(rnd_mat)):
            for y in range(len(rnd_mat[0])):
                prk = FSMPatRecKernel(fsm, rnd_mat, x, y)
                rec, t, visited = prk.apply()
                if rec:
                    print("pattern recognized", x, y, " activation time", t, " visited cells", visited)

    concept, mat = load_pattern_matrix('line1.pat')
    print(concept)
    print_matrix(mat)
    print("\n")

    fsms = []

    pg = PatternGraph(mat)
    start_nodes = pg.start_nodes
    for sn in start_nodes:
        l = FSMLearner(pg, sn) 
        fsm = l.learn()

        print("\nLearned FSM")
        fsm.print()

        fsms.append(fsm)

    print("Total automata", len(fsms))


    concept, mat = load_pattern_matrix('test.scene')
    print_matrix(mat)
    
    for fsm in fsms:
        print("\nTesting automata...")
        prk = FSMPatRecKernel(fsm, mat, 0, 0)
        rec, t, visited = prk.apply()
        if rec:
            print("pattern recognized", 0, 0, " activation time", t, " visited cells", visited)
    
    cnt = 0
    for fsm in fsms:
        print("Testing automata", cnt)
        cnt += 1
        for x in range(len(mat)):
            for y in range(len(mat[0])):
                prk = FSMPatRecKernel(fsm, mat, x, y)
                rec, t, visited = prk.apply()
                if rec:
                    print("pattern recognized", x, y, " activation time", t, " visited cells", visited)

    print("\nRND test")
    rnd_mat = create_random_matrix(15, 15, 0.4, 'x')
    print_matrix(rnd_mat)

    cnt = 0
    for fsm in fsms:
        print("Testing automata", cnt)
        cnt += 1
        for x in range(len(rnd_mat)):
            for y in range(len(rnd_mat[0])):
                prk = FSMPatRecKernel(fsm, rnd_mat, x, y)
                rec, t, visited = prk.apply()
                if rec:
                    print("pattern recognized", x, y, " activation time", t, " visited cells", visited)


    print("\nExternal test")
    concept, mat = load_pattern_matrix('test.scene')
    print_matrix(mat)
    cnt = 0
    for fsm in fsms:
        print("Testing automata", cnt)
        cnt += 1
        for x in range(len(mat)):
            for y in range(len(mat[0])):
                prk = FSMPatRecKernel(fsm, mat, x, y)
                rec, t, visited = prk.apply()
                if rec:
                    print("pattern recognized", x, y, " activation time", t, " visited cells", visited)
"""

