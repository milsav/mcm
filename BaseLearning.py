# Meta-cognitive machines
#
# Base module for supervised and unsupervised concept learning 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from HOAutomaton import learn_complex_concept
from Automaton import learn_simple_concept_from_matrix
from AdvancedLearning import AdvancedLearner

class BaseLearner:
    def __init__(self, automata_memory, mat, exclude_concepts=[], verbose=False):
        self.automata_memory = automata_memory
        self.mat = mat
        self.concept_recognized = False
        self.complex_concept_recognized, self.base_concept_recognized = False, False
        self.sat_concepts = []
        self.exclude_concepts = exclude_concepts
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
        
        passed, _ = learn_complex_concept(concept_id, self.mat, self.automata_memory, exclude_concepts=self.exclude_concepts, verbose=self.verbose)
        if passed:
            #self.concept_similarity_analysis(concept_id)
            return

        # if a complex concept cannot be learnt then try to learn a simple concept
        passed, _, fsms = learn_simple_concept_from_matrix(self.mat, verbose=self.verbose)
        if passed:
            if unsupervised:
                concept_id = self.automata_memory.get_concept_id_for_unknown(True)
            
            self.automata_memory.add_automata_to_memory(concept_id, True, fsms, self.mat)
            return
        
        print("Unable to learn concept", concept_id, "starting advanced learning")
        adv_learner = AdvancedLearner(concept_id, self.mat, self.automata_memory)
        adv_learner.learn()
                        


    #
    # Concept similarity analysis
    #                    
    """
    def concept_similarity_analysis(self, concept_id):
        print("concept similarity analysis for", concept_id)
        print("#similar concepts = ", len(self.partially_activated_concepts))
        
        current_hoa = self.automata_memory.get_automata(concept_id)[0]

        for pc in self.partially_activated_concepts:
            pc_name = pc[0]
            pc_hoa = self.automata_memory.get_automata(pc_name)[0]
            cmp = HOAComparator(current_hoa, pc_hoa)
            print("SIMILARITY", concept_id, pc_name, cmp.get_similarity())
            print(cmp.is_subconcept())
    """