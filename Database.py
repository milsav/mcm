from neo4j import GraphDatabase
import nxneo4j as nx4
import networkx as nx

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
    
    def get_big_digraph(self):
        #TODO: implementirati
        return 0
