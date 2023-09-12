# Meta-cognitive machines
#
# Class implementing long-term automata memory
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import determine_first_nonempty_pixel, parse_field, coverage, print_matrix
from HOAutomaton import HOAPatRecKernel
from Automaton import FSMPatRecKernel, PatternGraph
from HOAComparator import HOAComparator

import networkx as nx

"""
Directed graphs for concept relationships
"""
class ConceptDirectedGraph:
    def __init__(self):
        self.G = nx.DiGraph()


    def add_link(self, concept1, concept2):
        if not self.G.has_node(concept1):
            self.G.add_node(concept1)
        
        if not self.G.has_node(concept2):
            self.G.add_node(concept2)

        self.G.add_edge(concept1, concept2)

    
    def empty(self):
        return len(self.G.nodes()) == 0


    def info(self, graph_name):
        if self.empty():
            print("Empty", graph_name)
            return
        
        print(graph_name)
        print("Nodes: ", self.G.nodes())
        print("Links: ", self.G.edges())


    def reconfigure(self, old_concept_name, new_concept_name):
        if not self.G.has_node(old_concept_name):
            #print("[ConceptDirectedGraph, warning] reconfiguration attempt for non-existing node", old_concept_name)
            return

        succ = self.G.successors(old_concept_name)
        pred = self.G.predecessors(old_concept_name)
        
        self.G.remove_node(old_concept_name)
        self.G.add_node(new_concept_name)

        for s in succ:
            self.G.add_edge(new_concept_name, s)

        for p in pred:
            self.G.add_edge(p, new_concept_name)


    def remove_node(self, concept):
        if self.G.has_node(concept):
            self.G.remove_node(concept)


"""
HOA inheritance tree
"""
class HOAInheritanceTree(ConceptDirectedGraph):
    def __init__(self):
        super().__init__()


    def info(self):
        super().info("HOA inheritance tree")



"""
Concept dependency network
"""
class DependencyNet(ConceptDirectedGraph):
    def __init__(self):
        super().__init__()


    def info(self):
        super().info("Concept dependency network")



"""
HOA similarity network
"""
class HOASimilarityNet:
    def __init__(self):
        self.G = nx.Graph()


    def add_link(self, concept1, concept2, similarity):
        if not self.G.has_node(concept1):
            self.G.add_node(concept1)
        
        if not self.G.has_node(concept2):
            self.G.add_node(concept2)

        self.G.add_edge(concept1, concept2, similarity=similarity)


    def info(self):
        if len(self.G.nodes()) == 0:
            print("Empty HOA similarity network")
            return
        
        print("HOA similarity network")
        links = self.G.edges()
        for l in links:
            print(l[0], l[1], self.G.edges[l]["similarity"])


    def reconfigure(self, old_concept_name, new_concept_name):
        if not self.G.has_node(old_concept_name):
            return

        self.G.add_node(new_concept_name)
        
        neis = self.G.neighbors(old_concept_name)
        for nei in neis:
            w = self.G.edges[old_concept_name, nei]["similarity"]
            self.G.add_edge(new_concept_name, nei, similarity=w)

        self.G.remove_node(old_concept_name)


    def remove_node(self, concept):
        if self.G.has_node(concept):
            self.G.remove_node(concept)


class AutomataMemory:
    def __init__(self):
        self.automata = dict()       # map from concepts to automata recognizing concepts
        self.patterns = dict()       # map from concepts to patterns used to learn concepts
        self.base_concepts = set()   # concepts recognized by base automata
        self.hoa_concepts = set()    # concepts recognized by higher-oder automata 

        self.unknown_base_concepts = set()
        self.unknown_hoa_concepts = set()

        self.partially_activated_hoa = []

        self.inheritance_tree = HOAInheritanceTree()
        self.dependency_net = DependencyNet()
        self.similarity_net = HOASimilarityNet()


    """
    concept - string, automata -- list of automata
    """
    def add_automata_to_memory(self, concept, base_concept, automata, pattern_matrix):
        if concept in self.automata:
            self.automata[concept].extend(automata)
            self.patterns[concept].extend(pattern_matrix)
        else:
            self.automata[concept] = automata
            self.patterns[concept] = [pattern_matrix]

        if base_concept:
            self.base_concepts.add(concept)
        else:
            self.hoa_concepts.add(concept)

        # check if the concept is unknown (unsupervised learning)
        if self.is_unsupervised_concept(concept):
            if base_concept:
                self.unknown_base_concepts.add(concept)
            else:
                self.unknown_hoa_concepts.add(concept)

        # update dependency net
        if not base_concept:
            dep_concepts = []
            for a in automata:
                dep_concepts.extend(a.get_concept_dependencies())
                dep_concepts.extend(a.get_base_concept_dependencies())
            
            for d in dep_concepts:
                self.dependency_net.add_link(concept, d)

            # update inheritance tree and similarity net
            self.hoa_similarity_analysis(concept, automata)

        concept_type = "base" if base_concept else "complex"
        print('[AutomataMemory] new ' + concept_type + ' concept ' + concept + ' added to memory')


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
        
    
    def get_patterns(self, concept):
        if not concept in self.patterns:
            print("[Warning] No patterns for concept ", concept)
            return []
        else:
            return self.patterns[concept]    
        

    def get_all_automata(self):
        return self.automata


    def get_concept_id_for_unknown(self, base_concept):
        concept_type = "FSM" if base_concept else "HOA"
        num = len(self.unknown_base_concepts) if base_concept else len(self.unknown_hoa_concepts)
        return "UNKNOWN-" + concept_type + "-" + str(num)


    def is_unsupervised_concept(self, concept):
        return concept.startswith("UNKNOWN-")


    """
    svc: this function also forms the list of partially activated HOAs 
         (in that case return_only_first must be set to True)
    """
    def retrieve_satisfiable_hoa_concepts(self, matrix, return_only_first=False):
        sat = []
       
        self.partially_activated_hoa.clear()
        
        first_pixel = determine_first_nonempty_pixel(matrix)
        for hoa_concept in self.hoa_concepts:
            hoas = self.automata[hoa_concept]
            for hoa in hoas:
                prk = HOAPatRecKernel(hoa, matrix, first_pixel[0], first_pixel[1])
                rec, _, visited_fields = prk.apply()

                ac_score = prk.activation_score()
                if ac_score > 0:
                    self.partially_activated_hoa.append((hoa_concept, hoa, prk, ac_score))

                if rec and coverage(visited_fields, matrix):
                    sat.append((hoa_concept, hoa))
                    if return_only_first:
                        return sat
                
        return sat
    

    def retrieve_partially_activated_concepts(self):
        return self.partially_activated_hoa


    def retrieve_satisfiable_basic_concepts(self, matrix, return_only_first=False):
        sat = []

        pg = PatternGraph(matrix)
        starts = pg.start_nodes
        for start in starts:
            x, y = parse_field(start)
            for base_concept in self.base_concepts:
                fsms = self.automata[base_concept]
                for fsm in fsms:
                    pkr = FSMPatRecKernel(fsm, matrix, x, y)
                    rec, _, visited_fields = pkr.apply()
                    if rec and coverage(visited_fields, matrix):
                        sat.append((base_concept, pkr))
                        if return_only_first:
                            return sat
                    
        return sat


    def hoa_similarity_analysis(self, concept, automata):
        current_HOA = automata[0]
        
        for hc in self.hoa_concepts:
            if hc == concept:
                continue

            prev_HOA = self.automata[hc][0]
            cmp = HOAComparator(current_HOA, prev_HOA)
            similarity = cmp.get_similarity()
            if similarity > 0:
                self.similarity_net.add_link(concept, hc, similarity)
            
            sub, father, son = cmp.is_subconcept()
            if sub:
                self.inheritance_tree.add_link(son, father)




    def info(self):
        if len(self.automata) == 0:
            print("Empty automata memory")
            return
        
        print("Base/FSM    concepts = ", self.base_concepts)
        print("Complex/HOA concepts = ", self.hoa_concepts)

        for c in self.automata:
            print("Concept", c)
            print("Pattern")
            for p in self.patterns[c]:
                print_matrix(p)
            print("#automata", len(self.automata[c]))
            cnt = 0
            for a in self.automata[c]:
                print("---------- Automaton ", cnt)
                cnt += 1
                a.print()
                print()

        self.inheritance_tree.info()
        self.dependency_net.info()
        self.similarity_net.info()


    #
    # automata memory reconfiguration routines
    # 
    def reconfigure_unsupervised_concept(self, unsupervised_name, base_concept, supervised_name, supervised_pattern):
        automata = self.automata.pop(unsupervised_name)

        unsupervised_pattern = self.patterns[unsupervised_name]
        self.automata[supervised_name] = automata
        self.patterns[supervised_name] = unsupervised_pattern + [supervised_pattern]

        if base_concept:
            self.base_concepts.remove(unsupervised_name)
            self.base_concepts.add(supervised_name)
            self.unknown_base_concepts.remove(unsupervised_name)
        else:
            self.hoa_concepts.remove(unsupervised_name)
            self.hoa_concepts.add(supervised_name)
            self.unknown_hoa_concepts.remove(unsupervised_name)

            # reconfigure HOA networks
            self.dependency_net.reconfigure(unsupervised_name, supervised_name)
            self.inheritance_tree.reconfigure(unsupervised_name, supervised_name)
            self.similarity_net.reconfigure(unsupervised_name, supervised_name)

            for a in automata:
                a.change_concept_name(supervised_name)

        print("[AutomataMemory] unsupervised concept " + unsupervised_name + " reconfigured to " + supervised_name)


    #
    # automata memory deleting routines
    #
    def remove_concept_from_memory(self, concept_name):
        if not concept_name in self.automata:
            print("[warning, remove_concept_from_memory] concept does not exist:", concept_name)
            return

        concepts_to_relearn = self.determine_affected_concepts(concept_name)
        pats = []
        for c in concepts_to_relearn:
            p = self.patterns[c][0]
            pats.append(p)

        """
        for i in range(len(concepts_to_relearn)):
            print(concepts_to_relearn[i])
            print_matrix(pats[i])
        """

        concepts_to_remove = []
        for c in concepts_to_relearn:
            concepts_to_remove.append(c)
        concepts_to_remove.append(concept_name)

        #print("Concepts to remove: ", concepts_to_remove)
        
        for c in concepts_to_remove:
            self.delete_concept(c)


    def delete_concept(self, c):
        base_concept = c in self.base_concepts
        if base_concept:
            self.base_concepts.remove(c)
        else:
            self.hoa_concepts.remove(c)

        del self.automata[c]
        del self.patterns[c]

        self.inheritance_tree.remove_node(c)
        self.dependency_net.remove_node(c)
        self.similarity_net.remove_node(c)



    def determine_affected_concepts(self, concept_name):
        depg = self.dependency_net.G
        
        if not concept_name in depg:
            return []
        
        deps = nx.ancestors(depg, concept_name)
        return list(deps) 


"""
if __name__ == "__main__":
    automata_memory = AutomataMemory()

    from Automaton import learn_simple_concept
    ok, concept, mat, _, fsms = learn_simple_concept('test_files/vertical_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, mat)

    ok, concept, mat, _, fsms = learn_simple_concept('test_files/horizontal_line.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, mat)

    ok, concept, mat, _, fsms = learn_simple_concept('test_files/square.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, mat)

    ok, concept, mat, _, fsms = learn_simple_concept('test_files/scene1.txt', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, mat)

    ok, concept, mat, _, fsms = learn_simple_concept('test_files/t.pat', verbose=False)
    if ok:
        automata_memory.add_automata_to_memory(concept, True, fsms, mat)

    automata_memory.info()

  
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
