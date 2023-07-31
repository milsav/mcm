# Meta-cognitive machines
#
# Automaton module constains functions and classes 
# for pattern recognition based on finite-state-machines 
# constructed from 2D matrix patterns
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

import random
import networkx as nx

# Moore neighborhood: offsets
dx = [-1, -1, -1, 0, 0, 1, 1, 1]
dy = [-1, 0, 1, -1, 1, -1, 0, 1]
        
# Moore neighborhood: link types in pattern graphs 
link_type = ["UL", "U", "UR", "L", "R", "DL", "D", "DR"]


def create_empty_matrix(dimx, dimy):
    mat = []
    for _ in range(dimx):
        row = [' '] * dimy
        mat.append(row)

    return mat


def create_random_matrix(dimx, dimy, p):
    mat = create_empty_matrix(dimx, dimy)
    for i in range(dimx):
        for j in range(dimy):
            r = random.random()
            if r <= p:
                mat[i][j] = 'x'

    return mat


def load_pattern_matrix(file):
    with open(file) as f:
        lines = [line.rstrip() for line in f]

    conceptName = lines[0]
    dimx = len(lines) - 1
    dimy = 0
    for i in range(1, len(lines)):
        l = len(lines[i])
        if l > dimy:
            dimy = l

    mat = create_empty_matrix(dimx, dimy)
    
    for i in range(1, len(lines)):
        l = lines[i]
        for j in range(len(l)):
            c = l[j]
            if c != ' ':
                mat[i - 1][j] = c

    return conceptName, mat


def print_matrix(mat):
    for i in range(len(mat)):
        print("".join(mat[i]))


class PatternGraph:
    def __init__(self, mat):
        dimx = len(mat)
        dimy = len(mat[0])

        self.G = nx.DiGraph()
        first_node = None

        for i in range(dimx):
            for j in range(dimy):
                if mat[i][j] != ' ':
                    node_id = str(i) + "-" + str(j)
                    self.G.add_node(node_id, x=i, y=j, symbol=mat[i][j])
                    if first_node == None:
                        first_node = node_id

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
            print("[PatternGraph, error] Pattern not connected")
            return
        
        self.start_nodes = self.determine_start_nodes()
        if len(self.start_nodes) == 0:
            print("[PatternGraph, warning] Pattern does not have clear starting nodes")
            self.start_nodes = [first_node]
        
        print("START-NODES = ", self.start_nodes)


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
            print("End state         = ", self.states[-1].name)
            for s in self.states:
                s.print()


class FSMLearner:
    def __init__(self, pattern_graph, start_node):
        self.pattern_graph = pattern_graph
        self.start_node = start_node
        self.sequences, self.dfs_parent, self.return_back = self.pattern_graph.dfs(start_node, verbose_results=True)
        

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



class FSMPatRecKernel:
    def __init__(self, fsm, input_matrix, x, y):
        self.fsm = fsm
        self.input_matrix = input_matrix
        self.x = x
        self.y = y


if __name__ == "__main__":
    concept, mat = load_pattern_matrix('l1.pat')
    print(concept)
    print_matrix(mat)
    print("\n")

    pg = PatternGraph(mat)
    start_nodes = pg.start_nodes
    for sn in start_nodes:
        l = FSMLearner(pg, sn) 
        fsm = l.learn()

        print("\nLearned FSM")
        fsm.print()

        first = False

    #pg.print()

    """
    print("Random matrix")
    rnd_mat = create_random_matrix(30, 30, 0.2)
    print_matrix(rnd_mat)
    """