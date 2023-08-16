# Meta-cognitive machines
#
# Module for supervised concept learning 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix
from HOAutomaton import learn_complex_concept
from Automaton import PatternGraph, FSMLearner

class SupervisedLearner:
    def __init__(self, pattern_file, automata_memory, verbose=False):
        self.verbose = verbose
        self.automata_memory = automata_memory
        self.concept, self.pattern_matrix = load_matrix(pattern_file) 
        self.pattern_graph = PatternGraph(self.pattern_matrix)
        self.complex_concept = not self.pattern_graph.is_concept_simple()


    def learn_concept(self):
        if self.complex_concept:
            sat_concepts = self.automata_memory.retrieve_satisfiable_hoa_concepts(self.pattern_matrix)
            ex = len(sat_concepts) > 0
            
            if ex and self.verbose:
                print("HOA for", self.concept, "already learnt as", ",".join([sat[0] for sat in sat_concepts]))
            else:
                ok, msg = learn_complex_concept(self.concept, self.pattern_matrix, self.automata_memory, self.verbose)
                if self.verbose:
                    if ok:
                        print("HOA Concept", self.concept, "learnt succesfully")
                    else:
                        print("Learning HOA", self.concept, "failed: ", msg)        
        else:
            sat_concepts = self.automata_memory.retrieve_satisfiable_basic_concepts(self.pattern_matrix)
            ex = len(sat_concepts) > 0

            if ex and self.verbose:
                print("FSMS for", self.concept, "already learnt as", ",".join([sat[0] for sat in sat_concepts]))
            else:
                # learn HOA for a simple concept
                ok, _ = learn_complex_concept(self.concept + "-AS-HOA", self.pattern_matrix, self.automata_memory, self.verbose)
                if ok and self.verbose:
                    print("Concept", self.concept, " learned as HOA")

                # learn FSM for a simple concept
                start_nodes = self.pattern_graph.start_nodes
                fsms = [FSMLearner(self.pattern_graph, sn).learn() for sn in start_nodes]
                self.automata_memory.add_automata_to_memory(self.concept, True, fsms)
                if self.verbose:
                    print("Concept", self.concept, "learned as simple")




if __name__ == "__main__":
    from AutomataMemory import AutomataMemory
    from InferenceEngine import hoa_inference
    automata_memory = AutomataMemory()

    sl = SupervisedLearner('test_files/vertical_line.pat', automata_memory, verbose=False)
    sl.learn_concept()
    
    sl = SupervisedLearner('test_files/horizontal_line.pat', automata_memory, verbose=False)
    sl.learn_concept()

    sl = SupervisedLearner('test_files/square.pat', automata_memory, verbose=False)
    sl.learn_concept()

    sl = SupervisedLearner('test_files/square_cross.pat', automata_memory, verbose=False)
    sl.learn_concept()

    print("\n\n\nAutomata memory")
    automata_memory.info()

    print("\n\nRECOGNITION TEST")

    scene_desc, scene_matrix = load_matrix('test_files/scene4.txt')
    hoa_inference('test_files/scene4.txt', automata_memory)
    

