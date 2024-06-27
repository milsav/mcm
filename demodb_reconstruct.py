from Database import Database
from InferenceEngine import inference

db = Database("neo4j", "neo4j")
dbG = db.get_database_data()
memory = db.restore_automata_memory()
memory.info()
print("\n\nRECOGNITION TEST")
inference('test_files/scene4.txt', memory, show_activation_history=False)

db.closeDB()