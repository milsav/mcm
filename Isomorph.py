# Meta-cognitive machines
#
# Isomoprh module constains functionalities related to isomorphism checking
#
# Authors: {svc, lucy}@dmi.uns.ac.rs


from Automaton import EMPTY_FSM_SYMBOL

"""
FSM Isomoprhism Checker
"""
class FSMIsomorphChecker:
    def __init__(self, fsm_a, fsm_b):
        self.fsm_a, self.fsm_b = fsm_a, fsm_b
        self.isomorph_fsms = False

    def isomoprh(self):
        if self.fsm_a.num_states != self.fsm_b.num_states:
            return False
        
        num_states = self.fsm_a.num_states
        
        # transition mapping 
        self.tran_map = dict()

        for i in range(num_states):
            a_state = self.fsm_a.states[i]
            b_state = self.fsm_b.states[i]
            if not self.isomorph_states(a_state, b_state):
                return False
            
        self.isomorph_fsms = True
        return True
    

    def isomorph_states(self, a_state, b_state):
        a_trans = a_state.transitions
        b_trans = b_state.transitions

        if len(a_trans) != len(b_trans):
            return False
        
        num_trans = len(a_trans)
        for i in range(num_trans):
            a_tran, a_next = a_trans[i][0], a_trans[i][1].name
            b_tran, b_next = b_trans[i][0], b_trans[i][1].name 
            
            if a_next != b_next:
                return False
            
            if a_tran == EMPTY_FSM_SYMBOL and b_tran != EMPTY_FSM_SYMBOL:
                return False

            if b_tran == EMPTY_FSM_SYMBOL and a_tran != EMPTY_FSM_SYMBOL:
                return False
            
            a_tran_s, b_tran_s = str(a_tran), str(b_tran)
            if a_tran_s in self.tran_map:
                if b_tran_s != self.tran_map[a_tran_s]:
                    return False
            else:
                self.tran_map[a_tran_s] = b_tran_s 

        return True
    

    def explain_isomoprhism(self):
        if self.isomorph_fsms:
            for t in self.tran_map:
                print(t, " --> ", self.tran_map[t])



def isomoprh_concepts(a_fsms, b_fsms):
    for a_fsm in a_fsms:
        for b_fsm in b_fsms:
            checker = FSMIsomorphChecker(a_fsm, b_fsm)
            if checker.isomoprh():
                return True
            
    return False



if __name__ == "__main__":
    from Automaton import learn_simple_concept

    concepts = []

    _, name, _, _, fsms = learn_simple_concept("test_files/horizontal_line.pat")
    concepts.append((name, fsms))
    
    _, name, _, _, fsms = learn_simple_concept("test_files/vertical_line.pat")
    concepts.append((name, fsms))

    _, name, _, _, fsms = learn_simple_concept("test_files/left_angle.pat")
    concepts.append((name, fsms))

    _, name, _, _, fsms = learn_simple_concept("test_files/right_angle.pat")
    concepts.append((name, fsms))

    for j in range(1, len(concepts)):
        for i in range(j):
            concept_a, concept_b = concepts[i][0], concepts[j][0]
            fsms_a, fsms_b = concepts[i][1], concepts[j][1]

            if isomoprh_concepts(fsms_a, fsms_b):
                print("ISOMORPH CONCEPTS: ", concept_a, concept_b)
            else:
                print("non-isomoprph concepts", concept_a, concept_b)


