# Meta-cognitive machines
#
# Base module for supervised and unsupervised concept learning 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from HOAutomaton import learn_complex_concept
from Automaton import learn_simple_concept_from_matrix

class BaseLearner:
    def __init__(self, automata_memory, mat, verbose=False):
        self.automata_memory = automata_memory
        self.mat = mat
        self.concept_recognized = False
        self.complex_concept_recognized, self.base_concept_recognized = False, False
        self.sat_concepts = []
        self.verbose = verbose


    #
    # checks whether an existing concept can be applied to mat
    #
    def check_concept(self):
        self.sat_concepts = self.automata_memory.retrieve_satisfiable_hoa_concepts(self.mat)
        self.partially_activated_concepts = self.automata_memory.retrieve_partially_activated_concepts()
        
        self.complex_concept_recognized = len(self.sat_concepts) > 0
        if not self.complex_concept_recognized:
            self.sat_concepts = self.automata_memory.retrieve_satisfiable_basic_concepts(self.mat)
            self.base_concept_recognized = len(self.sat_concepts) > 0

        self.concept_recognized = self.complex_concept_recognized or self.base_concept_recognized
        


    #
    # base concept learning routine (for both supervised and unsupervised learning)
    # 
    def learn_concept(self, concept_id, unsupervised):
        # learn complex concept first
        if unsupervised:
            concept_id = self.automata_memory.get_concept_id_for_unknown(False)
        
        passed, _ = learn_complex_concept(concept_id, self.mat, self.automata_memory, self.verbose)
        if passed:
            self.concept_similarity_analysis(concept_id)
            return

        # if a complex concept cannot be learnt then try to learn a simple concept
        passed, _, fsms = learn_simple_concept_from_matrix(self.mat, self.verbose)
        if passed:
            if unsupervised:
                concept_id = self.automata_memory.get_concept_id_for_unknown(True)
            
            self.automata_memory.add_automata_to_memory(concept_id, True, fsms, self.mat)
                        


    #
    # Concept similarity analysis
    #                    
    def concept_similarity_analysis(self, concept_id):
        print("concept similarity analysis for", concept_id)
        print("#similar concepts = ", len(self.partially_activated_concepts))
        for pc in self.partially_activated_concepts:
            print(pc[0], pc[3]) 