# Meta-cognitive machines
#
# Database module constains functions for persisting
# AutomataMemory to Neo4j database and reconstucting
# data from database back to AutomataMemory
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from neo4j import GraphDatabase
import nxneo4j as nx4
import networkx as nx

import Matrix
import AutomataMemory
from Automaton import FSM, FSMSymbol, EMPTY_FSM_SYMBOL
import HOAutomaton

class Database:
    def __init__(self, username, password):
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=(username, password))


    def closeDB(self):
        self.driver.close()

    def persist(self, digraph):
        db_graph = nx4.DiGraph(self.driver)
        #copy nodes
        for node in list(digraph.nodes(data=True)):
            db_graph.add_node(node[0], attr_dict=node[1])

        #copy edges
        for edge in digraph.edges:
            u = edge[0]
            v = edge[1]
            data = [(k, v) for k, v in digraph.get_edge_data(u, v).items()]
            if len(data) == 1:
                db_graph.add_edge(u, v, link_type = data[0][1])
            elif len(data) == 2:
                db_graph.add_edge(u, v, link_type = data[0][1], symbol = data[1][1])
            elif len(data) == 3:
                db_graph.add_edge(u, v, link_type = data[0][1], move_type = data[1][1], constraints = data[2][1])
    
    def delete_all(self):
        self.driver.execute_query("match (a) -[r] -> () delete a, r")
        self.driver.execute_query("match (a) delete a")

    def get_database_data(self):
        db_graph = nx4.DiGraph(self.driver)
        return db_graph
    
    def restore_automata_memory(self):
        memory = AutomataMemory.AutomataMemory()

        # reconstructing FSMs
        db_fsms = self.driver.session().run("match (n) where n.node_type = 'FSM' return n")
        fsm_map = dict()
        
        for db_fsm in db_fsms:
            database_id = db_fsm.data()['n']['id']
            tokens = database_id.split('-')
            name = tokens[1]
            last_us = database_id.rfind('-')
            index = database_id[last_us + 1:]
            mat = self.str_to_matrix(db_fsm.data()['n']['pattern'])
            fsm = FSM(db_fsm.data()['n']['activating_symbol'])
            
            # create states
            sb_fsm_states = list(self.driver.session().run("match (n) where n.id contains $fsm_id and n.node_type='FSM_STATE' return n;", fsm_id=database_id).data())
            num_states = len(sb_fsm_states)
            for _ in range(num_states):
                fsm.create_state()

            # create transitions
            sb_fsm_links = list(self.driver.session().run("match (n1)-[r]->(n2) where n1.id contains $fsm_id and n1.node_type='FSM_STATE' and n2.id contains $fsm_id and n2.node_type='FSM_STATE' return n1,n2,r;", fsm_id=database_id))
            for link in sb_fsm_links:
                id_n1 = int(dict(link['n1'])['id'].split("-")[-1].split("_")[-1])
                symbol = dict(link['r'])['symbol'] 
                id_n2 = int(dict(link['n2'])['id'].split("-")[-1].split("_")[-1])
                
                sep_index = symbol.find(",")
                move = symbol[1:sep_index]
                next_symbol = symbol[sep_index + 1: -1]
                
                fsm_symb = EMPTY_FSM_SYMBOL
                if move != 'EMPTY':
                    fsm_symb = FSMSymbol(move, next_symbol)        

                fsm.states[id_n1].add_transition(fsm_symb, fsm.states[id_n2])
            
            if name in fsm_map:
                fsm_map[name][1].append((fsm, index))
            else:
                fsm_map[name] = (mat, [(fsm, index)])            
            
        for concept in fsm_map:
            pattern_matrix = fsm_map[concept][0]
            automata = [fsm[0] for fsm in fsm_map[concept][1]]
            memory.add_automata_to_memory(concept, True, automata, pattern_matrix)

        """
        for d in fsm_map:
            print(d)
            print(fsm_map[d][1])
            print()
        """
        # reconstructing HOAs
        
        all_hoas = dict()
        
        #first get HOAs with no other HOAs as dependencies
        db_hoas = self.driver.session().run("match (n)-[r]->(m) where n.node_type='HOA' and r.link_type <> 'DEPENDENCY' return distinct n;")
        for db_hoa in db_hoas.data():
            concept = db_hoa['n']['id'].split("-")[1]
            
            pattern = self.str_to_matrix(db_hoa['n']['pattern'])
            hoa = HOAutomaton.HOA(concept)
            
            #get hoa states
            query = "match (n)-[r]->(m) where n.id contains 'HOA-"+concept+"-' and m.id contains 'HOA-"+concept+"-' and m.node_type='HOA_STATE' and n.node_type='HOA_STATE' return n,r,m;"
            hoa_states = list(self.driver.session().run(query))
            
            hnodes = [None] * len(hoa_states)
            hlinks = []
            
            for state in hoa_states:
                src = dict(state.get("n"))
                link_src_dst = dict(state.get("r"))
                dst = dict(state.get("m"))
                
                src_id, dst_id = src['id'], dst['id']
                src_at, dst_at = int(src['activation_time']), int(dst['activation_time'])
                move_type = link_src_dst['move_type']
                constraints = eval(link_src_dst['constraints'])
                
                src_toks, dst_toks = src_id.split("-"), dst_id.split("-")
                src_concept, src_index, src_state_index = src_toks[-2], src_toks[-1], int(src_toks[2])
                dst_concept, dst_index, dst_state_index = dst_toks[-2], dst_toks[-1], int(dst_toks[2])
                
                if hnodes[src_state_index] == None:
                    hnodes[src_state_index] = (src_concept, src_index, src_at)
                    
                if hnodes[dst_state_index] == None:
                    hnodes[dst_state_index] = (dst_concept, dst_index, dst_at)
                    
                hlinks.append((src_state_index, dst_state_index, move_type, constraints))
            
            for i in range(len(hnodes)):
                fsm_concept, aindex, at = hnodes[i][0], hnodes[i][1], hnodes[i][2]
                candidates = fsm_map[fsm_concept]
                automaton = None
                for c in candidates[1]:
                    if c[1] == aindex:
                        automaton = c[0]
                
                hoa.add_node(fsm_concept, automaton, "FSM", at)
                
            hoa.process_activation_times()
                
            for hl in hlinks:
                srci, dsti, mt, cons = hl[0], hl[1], hl[2], hl[3]
                hoa.add_link(srci, dsti, mt, cons)
                
            all_hoas[concept] = (hoa, pattern)
            memory.add_automata_to_memory(concept, False, [hoa], pattern)
            
            """
            states_map = dict()
            relations_map = list()
            for state in hoa_states:
                n = dict(dict(state)['n'])
                n_index = n['id'].split('-')[2]
                n_fsm_id = n['id'].split('-')[-2]
                n_fsm_index = n['id'].split('-')[-1]
                n_automaton = None
                for auts in fsm_map[n_fsm_id][1]:
                    if auts[1] == n_fsm_index:
                        n_automaton = auts[0]
                n_activation_time = int(n['activation_time'])
                states_map[n_index] = {'concept':n_fsm_id, 'automaton':n_automaton, 'automaton_type':'FSM', 'activation_time':n_activation_time}
                
                r = dict(dict(state)['r'])
                nodes = list(dict(state)['r'].nodes)
                n1_index = dict(nodes[0])['id'].split('-')[2]
                n2_index = dict(nodes[1])['id'].split('-')[2]
                move_type = r['move_type']
                constraints = r['constraints'][2:-2].split(',')
                relations_map.append((n1_index, n2_index, move_type, constraints))

                m = dict(dict(state)['m'])
                m_index = m['id'].split('-')[2]
                if m_index not in states_map.keys():
                    m_fsm_id = m['id'].split('-')[-2]
                    m_fsm_index = m['id'].split('-')[-1]
                    m_automaton = None
                    for auts in fsm_map[m_fsm_id][1]:
                        if auts[1] == m_fsm_index:
                            m_automaton = auts[0]
                    m_activation_time = int(m['activation_time'])
                    states_map[m_index] = {'concept':m_fsm_id, 'automaton':m_automaton, 'automaton_type':'FSM', 'activation_time':m_activation_time}

            
            for key in states_map:
                state = states_map[key]
                hoa.add_node(state['concept'], state['automaton'], state['automaton_type'], state['activation_time'])
            
            for rel in relations_map:
                hoa.add_link(int(rel[0]) - 1, int(rel[1]) - 1, rel[2], rel[3])
                
            all_hoas[concept] = (hoa, pattern)
            memory.add_automata_to_memory(concept, False, [hoa], pattern)
            """
                            
            
        #get the rest of HOAs
        """
        db_hoas = self.driver.session().run("match (n) where n.node_type='HOA' return n;")
        for db_hoa in db_hoas.data():
            concept = db_hoa['n']['id'].split("-")[1]
            if concept not in all_hoas.keys():
                pattern = self.str_to_matrix(db_hoa['n']['pattern'])
                hoa = HOAutomaton.HOA(concept)
            
                #get hoa states
                query = "match (n)-[r]->(m) where n.id contains 'HOA-"+concept+"-' and m.id contains 'HOA-"+concept+"-' and m.node_type='HOA_STATE' and n.node_type='HOA_STATE' return n,r,m;"
                hoa_states = list(self.driver.session().run(query))
                states_map = dict()
                relations_map = list()
                for state in hoa_states:
                    n = dict(dict(state)['n'])
                    if('FSM' in n['id']):
                        n_index = n['id'].split('-')[2]
                        n_fsm_id = n['id'].split('-')[-2]
                        n_fsm_index = n['id'].split('-')[-1]
                        n_automaton = None
                        for auts in fsm_map[n_fsm_id][1]:
                            if auts[1] == n_fsm_index:
                                n_automaton = auts[0]
                        n_activation_time = int(n['activation_time'])
                        states_map[n_index] = {'concept':n_fsm_id, 'automaton':n_automaton, 'automaton_type':'FSM', 'activation_time':n_activation_time}
                    else:
                        n_index = n['id'].split('-')[2]
                        n_hoa_id = n['id'].split('-')[-1]
                        n_automaton = all_hoas[n_hoa_id][0]
                        n_activation_time = int(n['activation_time'])
                        states_map[n_index] = {'concept':n_hoa_id, 'automaton':n_automaton, 'automaton_type':'HOA', 'activation_time':n_activation_time}
                    
                    r = dict(dict(state)['r'])
                    nodes = list(dict(state)['r'].nodes)
                    n1_index = dict(nodes[0])['id'].split('-')[2]
                    n2_index = dict(nodes[1])['id'].split('-')[2]
                    move_type = r['move_type']
                    constraints = r['constraints'][2:-2].split(',')
                    relations_map.append((n1_index, n2_index, move_type, constraints))


                    m = dict(dict(state)['m'])
                    if 'FSM' in m['id']:
                        m_index = m['id'].split('-')[2]
                        if m_index not in states_map.keys():
                            m_fsm_id = m['id'].split('-')[-2]
                            m_fsm_index = m['id'].split('-')[-1]
                            m_automaton = None
                            for auts in fsm_map[m_fsm_id][1]:
                                if auts[1] == m_fsm_index:
                                    m_automaton = auts[0]
                            m_activation_time = int(m['activation_time'])
                            states_map[m_index] = {'concept':m_fsm_id, 'automaton':m_automaton, 'automaton_type':'FSM', 'activation_time':m_activation_time}
                    else:
                        m_index = m['id'].split('-')[2]
                        m_hoa_id = m['id'].split('-')[-1]
                        m_automaton = all_hoas[m_hoa_id][0]
                        m_activation_time = int(m['activation_time'])
                        states_map[m_index] = {'concept':m_hoa_id, 'automaton':m_automaton, 'automaton_type':'HOA', 'activation_time':m_activation_time}
                    
                    for key in states_map:
                        state = states_map[key]
                        hoa.add_node(state['concept'], state['automaton'], state['automaton_type'], state['activation_time'])
            
                    for rel in relations_map:
                        hoa.add_link(int(rel[0]) - 1, int(rel[1]) - 1, rel[2], rel[3])
                
                    all_hoas[concept] = (hoa, pattern)
                    memory.add_automata_to_memory(concept, False, [hoa], pattern)
        """
        self.driver.close()

        return memory


    def str_to_matrix(self, str):
        tokens = str.split("\n")
        tokens.pop() #posto je poslednji element prazan string zbog viska \n na kraju
        dimx = len(tokens)
        dimy = len(tokens[0])

        mat = Matrix.create_empty_matrix(dimx, dimy)
        for i in range(dimx):
            for j in range(dimy):
                mat[i][j] = tokens[i][j]

        return mat