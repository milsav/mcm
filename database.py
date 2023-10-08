from neo4j import GraphDatabase
import nxneo4j as nx4
import networkx as nx

'''
problem sa kreiranjem vise sema u bazi podataka tj. vise db instanci iz python koda
proveriti da li je to moguce -- nije u community edition, mora da bude fiksirana sema

za svaki hoa imam jedan cvor, za svaki fsm imam ime i stanja kao cvorove
sacuvati sve u jedan veliki graf
automata memory, create main graph
'''

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4j"))
#driver.session().run("CREATE DATABASE karate1") #ovo ne moze u community edition
#driver.session(database="karate1")

#driver.execute_query("CREATE DATABASE karate1")
#driver.execute_query(":use karate1")
driver.execute_query("match (a) -[r] -> () delete a, r")
driver.execute_query("match (a) delete a")
graph1 = nx.karate_club_graph()
print("cvorova ", graph1.number_of_nodes())
graph2 = nx.karate_club_graph()
db_graph1 = nx4.Graph(driver)
db_graph1.add_edges_from(graph1.edges)
#driver.session().run("CREATE DATABASE karate2")
#driver.session(database="karate2")

#driver.execute_query("CREATE DATABASE karate2")
#driver.execute_query(":use karate2")
driver.execute_query("match (a) -[r] -> () delete a, r")
driver.execute_query("match (a) delete a")
db_graph2 = nx4.Graph(driver)
db_graph2.add_edges_from(graph2.edges)
driver.close()