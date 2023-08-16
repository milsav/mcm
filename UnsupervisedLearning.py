# Meta-cognitive machines
#
# Unsupervised learning module: module for learning non-labeled concepts
# present in a given scene 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix, print_matrix
from SceneAnalyzer import IdentifyObjects
from HOAutomaton import learn_complex_concept
from Automaton import learn_simple_concept_from_matrix

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
            #if self.verbose:
            #    print("\nProcessing")
            #    print_matrix(mat)
            
            complex_concept_recognized, base_concept_recognized = False, False

            sat_concepts = self.automata_memory.retrieve_satisfiable_hoa_concepts(mat)
            complex_concept_recognized = len(sat_concepts) > 0
            if not complex_concept_recognized:
                sat_concepts = self.automata_memory.retrieve_satisfiable_basic_concepts(mat)
                base_concept_recognized = len(sat_concepts) > 0

            concept_recognized = complex_concept_recognized or base_concept_recognized

            if self.verbose and concept_recognized:
                concept_type = "HOA" if complex_concept_recognized else "FSM"
                print("Object", i, " recognized as: ", ",".join([sat[0] for sat in sat_concepts]), " #", concept_type)
            
            if not concept_recognized:
                concept_id = self.automata_memory.get_concept_id_for_unknown(False)
                ok, _ = learn_complex_concept(concept_id, mat, self.automata_memory, self.verbose)
                if ok and self.verbose:
                    print("Learning complex concept for object", i, " passed successfully --> ", concept_id)

                if not ok:
                    passed, _, fsms = learn_simple_concept_from_matrix(mat, self.verbose)
                    if passed:
                        concept_id = self.automata_memory.get_concept_id_for_unknown(True)
                        self.automata_memory.add_automata_to_memory(concept_id, True, fsms, mat)
                        
                        if self.verbose:
                            print("Learning base concept for object", i, "passed successfully --> ", concept_id)
            



if __name__ == "__main__":
    from AutomataMemory import AutomataMemory
    from Automaton import learn_simple_concept
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

    ul = UnsupervisedLearner("test_files/scene3.txt", automata_memory, verbose=True)
    ul.identify_and_learn_unknown_concepts()

    print("\n\nRECOGNITION TEST")

    scene_desc, scene_matrix = load_matrix('test_files/scene4.txt')
    hoa_inference('test_files/scene4.txt', automata_memory)