# Meta-cognitive machines
#
# Demo 1: learning & inference
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from AutomataMemory import AutomataMemory
from Matrix import load_matrix
from InferenceEngine import inference
from LearningEngine import LearningEngine

automata_memory = AutomataMemory()

le = LearningEngine(automata_memory, verbose=False)
le.learn('test_files/vertical_line.pat')
le.learn('test_files/horizontal_line.pat')
le.learn('test_files/scene-rect.txt')
le.learn('test_files/t.pat')
le.learn('test_files/left_angle.pat')
le.learn('test_files/right_angle.pat')
le.learn('test_files/rect.pat')
le.learn('test_files/square.pat')
le.learn('test_files/square_cross.pat')
le.learn('test_files/square_line.pat')

print("Learning finished")

print("\n\n\nAutomata memory")
automata_memory.info()


print("\n\nRECOGNITION TEST")
scene_desc, scene_matrix = load_matrix('test_files/scene4.txt')
inference('test_files/scene4.txt', automata_memory, show_activation_history=False)
