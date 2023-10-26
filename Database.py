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

class Database:
    def __init__(self, username, password):
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=(username, password))

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


        # reconstructing HOAs
        db_hoas = self.driver.session().run("match (n) where n.node_type='HOA' return n;")
        print(db_hoas.data())

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