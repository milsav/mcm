# Meta-cognitive machines
#
# Module for supervised concept learning 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix
from HOAutomaton import learn_HOA
from BaseLearning import BaseLearner
from HOAComparator import HOAComparator, HOAComplexityComparator

class SupervisedLearner:
    def __init__(self, pattern_file, automata_memory, verbose=False):
        self.verbose = verbose
        self.automata_memory = automata_memory
        self.concept, self.pattern_matrix = load_matrix(pattern_file) 
        

    def learn_concept(self):
        if self.concept in self.automata_memory.get_hoa_concepts():
            print("[Warning]", self.concept, "already exists in the automata memory, abort")
            return

        learner = BaseLearner(self.automata_memory, self.pattern_matrix, verbose=self.verbose)
        learner.check_concept()

        if not learner.concept_recognized:
            learner.learn_concept(self.concept, False)
            return 
        
        if learner.complex_concept_recognized:
            self.relearn_concept(learner)
        

    def relearn_concept(self, learner):
        ignore_concepts = [x[0] for x in learner.sat_concepts]
        partial_concepts = [x[0] for x in learner.partially_activated_concepts]
        for ic in ignore_concepts:
            if ic not in partial_concepts:
                partial_concepts.append(ic)
        
        # print("\n\nCONCEPT RECOGNIZED AS", ignore_concepts)
        # print("Partial concepts: ", partial_concepts)

        ok1, new_hoa_1, _ = learn_HOA(self.concept, self.pattern_matrix, self.automata_memory, exclude_concepts=ignore_concepts)
        ok2, new_hoa_2, _ = learn_HOA(self.concept, self.pattern_matrix, self.automata_memory, exclude_concepts=partial_concepts)
        new_hoa = None
        if ok1:
            new_hoa = new_hoa_1
        if ok2:
            cc = HOAComplexityComparator(new_hoa_1, new_hoa_2)
            cmp = cc.compare()
            if cmp < 0:
                new_hoa = new_hoa_2

        if new_hoa == None:
            return
        
        add_new = False

        if len(ignore_concepts) == 1 and self.automata_memory.is_unsupervised_concept(ignore_concepts[0]):
            existing_hoa = self.automata_memory.get_automata(ignore_concepts[0])[0]
            hc = HOAComparator(existing_hoa, new_hoa)
            sim = hc.get_similarity()
            if sim == 1.0:
                self.automata_memory.reconfigure_unsupervised_concept(ignore_concepts[0], False, self.concept, self.pattern_matrix)
            else:
                add_new = True
        else:
            add_new = True

        if add_new:
            self.automata_memory.add_automata_to_memory(self.concept, False, [new_hoa], self.pattern_matrix)


        

    """
    def handle_learnt_concept(self, sat_concepts, base_concept):
        # reconfigure automata memory when supervised concept matches an unsupervised concept
        if len(sat_concepts) == 1:
            sat_concept_name = sat_concepts[0][0]
            if self.automata_memory.is_unsupervised_concept(sat_concepts[0][0]):
                self.automata_memory.reconfigure_unsupervised_concept(sat_concept_name, base_concept, self.concept, self.pattern_matrix) 
    """

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
    

