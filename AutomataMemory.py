# Meta-cognitive machines
#
# Class implementing long-term automata memory
#
# Authors: {svc, lucy}@dmi.uns.ac.rs


class AutomataMemory:
    def __init__(self):
        self.automata = dict()
        self.base_concepts = set()   # concepts recognized by base automata
        self.hoa_concepts = set()    # concepts recognized by higher-oder automat 


    """
    concept - string, automata -- list of automata
    """
    def add_automata_to_memory(self, concept, base_concept, automata):
        if concept in self.automata:
            self.automata[concept].extend(automata)
        else:
            self.automata[concept] = automata

        if base_concept:
            self.base_concepts.add(concept)
        else:
            self.hoa_concepts.add(concept)


    def get_base_concepts(self):
        return self.base_concepts
    

    def get_hoa_concepts(self):
        return self.hoa_concepts
    

    def get_automata(self, concept):
        if not concept in self.automata:
            print("[Warning] No automata for concept ", concept)
            return []
        else:
            return self.automata[concept]
        

    def get_all_automata(self):
        return self.automata
    

    def info(self):
        for c in self.automata:
            print("Concept", c)
            print("#automata", len(self.automata[c]))
            cnt = 0
            for a in self.automata[c]:
                print("---------- Automaton ", cnt)
                cnt += 1
                a.print()
                print()



if __name__ == "__main__":
    automata_memory = AutomataMemory()

    from Automaton import learn_simple_concept
    ok, concept, _, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/square.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/scene1.txt', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/t.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms)

    automata_memory.info()

"""    
#
# Class implementing long-term memory for holding base automata
# 
class BaseAutomataMemory:
    def __init__(self):
        self.base_automata = dict()

    def add_automaton(self, concept, fsms):
        if concept in self.base_automata:
            self.base_automata[concept].extend(fsms)
        else:
            self.base_automata[concept] = fsms

    def get_concepts(self):
        return self.base_automata.keys()
    
    def get_automata(self, concept):
        if not concept in self.base_automata:
            print("[Warning] No automaton for concept ", concept)
            return []
        else:
            return self.base_automata[concept]
        
    def get_all_automata(self):
        return self.base_automata
    
    def info(self):
        for c in self.base_automata:
            print("Concept", c)
            print("#automata", len(self.base_automata[c]))
            cnt = 0
            for a in self.base_automata[c]:
                print("---------- Automaton ", cnt)
                cnt += 1
                a.print()
                print()
            




#
# base automata memory object
#
base_automata_memory = None

def init_base_automata_memory(verbose=False):
    global base_automata_memory

    base_automata_memory = BaseAutomataMemory()
    ok_msg = "automaton created and added to memory"

    ok, concept, _, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        if verbose:
            print(concept + " " + ok_msg)
        base_automata_memory.add_automaton(concept, fsms)

    ok, concept, _, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        if verbose:
            print(concept + " " + ok_msg)
        base_automata_memory.add_automaton(concept, fsms)

#
#  initialize base automata memory object
#
init_base_automata_memory()


if __name__ == "__main__":
    base_automata_memory.info()
"""
