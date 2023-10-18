from neo4j import GraphDatabase
import nxneo4j as nx4
import networkx as nx

'''
To install neo4j database use: https://neo4j.com/download/ 
To install driver for python use: pip install neo4j (https://pypi.org/project/neo4j/)
Library used for direct connection between NetworkX and neo4j is installed with:
pip install networkx-neo4j (https://github.com/ybaktir/networkx-neo4j)

Community edition of neo4j database supports using only one database (schema) on one
account. Java version 11 must installed on system, earlier and later versions are not supported.
If problems during later use appear, from neo4j root folder delete contents of folders 
../data/databases and ../data/transactions, run neo4j-admin dbms set-initial-password <password>
(https://neo4j.com/docs/operations-manual/current/configuration/set-initial-password/) and then
try starting database again. After starting database grphical interface will be available at
http://localhost:7474/browser/.

Other used libraries require no additional setup.
'''

#by obtaining the driver connection is established
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4j"))
#using obtained driver we can execute queries and transactions
driver.execute_query("match (a) -[r] -> () delete a, r")
driver.execute_query("match (a) delete a")

#we can use NetworkX graphs (and digraphs), but to store data from used graph we must
#copy it to a nxneo4j graph
graph1 = nx.karate_club_graph()
db_graph1 = nx4.Graph(driver)
#NOTE: adding all edges does not add edge labels and addiotional data
#furthermore, labels can not be edited by editing graph from python, cypher query must be used
db_graph1.add_edges_from(graph1.edges)
#adding edge by edge we can save edge info
db_graph1.add_edge(0, 22, weight="2",link_type="inheritance", similarity="0.4")

#TEST: loading previously stored graph
db_graph2 = nx4.Graph(driver)
print(list(db_graph2.nodes))
print(list(db_graph2.edges(data=True)))

driver.close()