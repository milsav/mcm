from AutomataMemory import AutomataMemory
from LearningEngine import LearningEngine
from Database import Database

import networkx as nx
import nxneo4j as nx4

from InferenceEngine import inference

#automata_memory = AutomataMemory()

#le = LearningEngine(automata_memory, verbose=False)
#le.learn('test_files/vertical_line.pat')
#le.learn('test_files/horizontal_line.pat')
#le.learn('test_files/square.pat')
#le.learn('test_files/rect.pat')
#le.learn('test_files/square_cross.pat')

#print("Learning finished")

#print("\n\n\nAutomata memory")
#automata_memory.info()

#print("\n\nConverting to big digraph")
#G = automata_memory.convert_to_big_digraph()

db = Database("neo4j", "neo4j")
#db.delete_all()
#db.persist(G)
#db.closeDB()
dbG = db.get_database_data()
#print("\n\n\nNodes:\n")
#print(list(dbG.nodes(data=True)))
#print("\n\n\nEdges:\n")
#print(list(dbG.edges(data=True)))
#print("\n\n\n")
memory = db.restore_automata_memory()
memory.info()
print("\n\nRECOGNITION TEST")
inference('test_files/scene4.txt', memory, show_activation_history=False)

db.closeDB()