# Meta-cognitive machines
#
# Unsupervised learning module: module for learning non-labeled concepts
# present in a given scene 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix, print_matrix
from SceneAnalyzer import IdentifyObjects
from HOAutomaton import learn_complex_concept

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
            
            sat_concepts = self.automata_memory.retrieve_satisfiable_hoa_concepts(mat)
            concept_recognized = len(sat_concepts) > 0

            if self.verbose:
                print("\n")
                print_matrix(mat)
                if concept_recognized:
                    print("Object", i, " recognized as: ", ",".join([sat[0] for sat in sat_concepts]))
                else:
                    print("Object", i, " is not recognized by existing concepts")

            if not concept_recognized:
                concept_id = self.automata_memory.get_concept_id_for_unknown(False)
                ok, msg = learn_complex_concept(concept_id, mat, self.automata_memory, self.verbose)
                if self.verbose:
                    if not ok:
                        print("Learning complex concept failed for object", i)
                        print(msg)
                    else:
                        print("Learning complex concept for object", i, " passed succesfully")
                        hoa = self.automata_memory.get_automata(concept_id)[0]
                        hoa.print()



if __name__ == "__main__":
    from AutomataMemory import AutomataMemory
    from Automaton import learn_simple_concept
    from InferenceEngine import hoa_inference

    automata_memory = AutomataMemory()

    ok, concept, _, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    concept, matrix = load_matrix('test_files/square.pat')
    learn_complex_concept(concept, matrix, automata_memory, verbose=False)

    ul = UnsupervisedLearner("test_files/scene3.txt", automata_memory, verbose=True)
    ul.identify_and_learn_unknown_concepts()

    print("\n\nRECOGNITION TEST")

    scene_desc, scene_matrix = load_matrix('test_files/scene4.txt')
    hoa_inference('test_files/scene4.txt', automata_memory)