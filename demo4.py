# Meta-cognitive machines
#
# Demo 4: long-term persistance of automata memory to Neo4J database
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from AutomataMemory import AutomataMemory
from LearningEngine import LearningEngine

import networkx as nx

automata_memory = AutomataMemory()

le = LearningEngine(automata_memory, verbose=False)
le.learn('test_files/vertical_line.pat')
le.learn('test_files/horizontal_line.pat')
le.learn('test_files/square.pat')
le.learn('test_files/rect.pat')
le.learn('test_files/square_cross.pat')

print("Learning finished")

print("\n\n\nAutomata memory")
automata_memory.info()

print("\n\nConverting to big digraph")
G = automata_memory.convert_to_big_digraph()
print("\n\n", type(G))
print("#NODES")
for n in G.nodes:
    print(n, G.nodes[n])
print("#LINKS")
for l in G.edges:
    print(l, G.edges[l])

print("\n\nweakly connected components")
print("#WCC:", nx.number_weakly_connected_components(G))
for c in nx.weakly_connected_components(G):
    print(c)