# Meta-cognitive machines
#
# Long-term automata memory
#
# Authors: {svc, lucy}@dmi.uns.ac.rs


from Automaton import learn_simple_concept

#
# Class implemented long-term memory for holding base automata
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
            print("[Warning] No automata for concept ", concept)
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

