# Meta-cognitive machines
#
# Unsupervised learning module: module for learning non-labeled concepts
# present in a given scene 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix
from SceneAnalyzer import IdentifyObjects
from BaseLearning import BaseLearner


class UnsupervisedLearner:
    def __init__(self, scene_file, automata_memory, verbose=False):
        self.verbose = verbose
        self.automata_memory = automata_memory

        # load and parse scene
        scene_desc, self.scene_matrix = load_matrix(scene_file)
        if verbose:
            print(scene_desc, "loaded")


    def identify_and_learn_unknown_concepts(self):
        idobj = IdentifyObjects(self.scene_matrix)
        num_objects = idobj.num_objects()

        if self.verbose:
            print("Loaded scene contains", num_objects, "objects")

        for i in range(num_objects):
            mat = idobj.get_object_matrix(i)
            
            learner = BaseLearner(self.automata_memory, mat, verbose=self.verbose)
            learner.check_concept()
            if not learner.concept_recognized:
                learner.learn_concept(None, True)



if __name__ == "__main__":
    from AutomataMemory import AutomataMemory
    from Automaton import learn_simple_concept
    from HOAutomaton import learn_complex_concept
    from InferenceEngine import hoa_inference

    automata_memory = AutomataMemory()

    ok, concept, pattern_matrix, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, pattern_matrix)

    ok, concept, pattern_matrix, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, pattern_matrix)

    concept, matrix = load_matrix('test_files/square.pat')
    learn_complex_concept(concept, matrix, automata_memory, verbose=False)

    ul = UnsupervisedLearner("test_files/scene3.txt", automata_memory, verbose=False)
    ul.identify_and_learn_unknown_concepts()

    print("\n\nRECOGNITION TEST")

    scene_desc, scene_matrix = load_matrix('test_files/scene4.txt')
    hoa_inference('test_files/scene4.txt', automata_memory)