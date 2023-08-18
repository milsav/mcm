# Meta-cognitive machines
#
# Module for supervised concept learning 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix
from BaseLearning import BaseLearner

class SupervisedLearner:
    def __init__(self, pattern_file, automata_memory, verbose=False):
        self.verbose = verbose
        self.automata_memory = automata_memory
        self.concept, self.pattern_matrix = load_matrix(pattern_file) 
        

    def learn_concept(self):
        learner = BaseLearner(self.automata_memory, self.pattern_matrix, verbose=self.verbose)
        learner.check_concept()

        if learner.concept_recognized:
            self.handle_learnt_concept(learner.sat_concepts, learner.base_concept_recognized)
            return
        
        learner.learn_concept(self.concept, False)

        

    def handle_learnt_concept(self, sat_concepts, base_concept):
        # reconfigure automata memory when supervised concept matches an unsupervised concept
        if len(sat_concepts) == 1:
            sat_concept_name = sat_concepts[0][0]
            if self.automata_memory.is_unsupervised_concept(sat_concepts[0][0]):
                self.automata_memory.reconfigure_unsupervised_concept(sat_concept_name, base_concept, self.concept, self.pattern_matrix) 


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
    

