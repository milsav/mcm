from AutomataMemory import AutomataMemory
from LearningEngine import LearningEngine
from Database import Database

automata_memory = AutomataMemory()

le = LearningEngine(automata_memory, verbose=False)
le.learn('test_files/vertical_line.pat')
le.learn('test_files/horizontal_line.pat')
le.learn('test_files/square.pat')
le.learn('test_files/rect.pat')

print("Learning finished")

print("\n\n\nAutomata memory")
automata_memory.info()

print("\n\n\nConverting to big digraph")
G = automata_memory.convert_to_big_digraph()

print("\n\n\nSaving to database")
db = Database("neo4j", "neo4j")
db.delete_all()
db.persist(G)
db.closeDB()
print("Automata memory saved to database!")
