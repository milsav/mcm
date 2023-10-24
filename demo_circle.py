from AutomataMemory import AutomataMemory
from Matrix import load_matrix
from InferenceEngine import inference
from LearningEngine import LearningEngine

automata_memory = AutomataMemory()

le = LearningEngine(automata_memory, verbose=False)
le.learn('test_files/circle.pat')

print("\n\n\nAutomata memory")
automata_memory.info()

print("\n\nRECOGNITION TEST")
inference('test_files/circle_scene.txt', automata_memory, show_activation_history=False)