# Meta-cognitive machines
#
# The module for comparing HOAs and deriving similarity between them
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs


class HOAComplexityComparator:
    def __init__(self, hoa_a, hoa_b):
        self.hoa_a = hoa_a
        self.hoa_b = hoa_b
        

    def compare(self):
        # num FSMS involved
        nodes_a, nodes_b = self.hoa_a.total_FSMS(), self.hoa_b.total_FSMS()
        if nodes_a < nodes_b:
            return -1
        elif nodes_a > nodes_b:
            return 1
        
        # num links
        links_a, links_b = self.hoa_a.G.number_of_edges(), self.hoa_b.G.number_of_edges()
        if links_a < links_b:
            return -1
        elif links_a > links_b:
            return 1
        
        # num link constraints
        cons_a, cons_b = len(self.hoa_a.link_constraints), len(self.hoa_b.link_constraints) 
        if cons_a < cons_b:
            return -1
        elif cons_a > cons_b:
            return 1
        
        # num activation time constraints
        at_a, at_b = len(self.hoa_a.identical_at), len(self.hoa_b.identical_at)
        if at_a < at_b:
            return -1
        elif at_a > at_b:
            return 1
        
        at_a, at_b = len(self.hoa_a.semi_identical_at), len(self.hoa_b.semi_identical_at)
        if at_a < at_b:
            return -1
        elif at_a > at_b:
            return 1
        
        return 0


def longest_common_subsequence(lst1, lst2):
    m, n = len(lst1), len(lst2)
    jh = [[0 for j in range(n + 1)] for i in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if lst1[i - 1] == lst2[j - 1]:
                jh[i][j] = 1 + jh[i - 1][j - 1]
            else:
                jh[i][j] = max(jh[i - 1][j], jh[i][j - 1])

    return jh[-1][-1]


class HOAComparator:
    def __init__(self, hoa_a, hoa_b, factor_nodes=0.4, factor_links=0.4, factor_constraints=0.2):
        self.hoa_a = hoa_a
        self.hoa_b = hoa_b

        self.G_a, self.G_b = hoa_a.G, hoa_b.G

        if factor_nodes + factor_links + factor_constraints != 1:
            print("[HOAComparator, warning] ponders not set properly, the sum of ponders should be 1")

        self.factor_nodes = factor_nodes
        self.factor_links = factor_links
        self.factor_constraints = factor_constraints

        self.similarity = 0
        self.identical_structure = False
        self.subconcept = False
        self.father, self.son = "", ""
    
        self.compare()


    def get_similarity(self):
        return self.similarity

    
    def is_subconcept(self):
        return self.subconcept, self.father, self.son


    def compare(self):
        sim_nodes = self.compare_nodes()
        sim_links = self.compare_links()
        sim_constraints = 0
        
        if sim_nodes == 1 and sim_links == 1:
            self.identical_structure = True
            sim_constraints = self.compare_constraints()

        self.similarity = sim_nodes * self.factor_nodes + sim_links * self.factor_links + sim_constraints * self.factor_constraints


    def compare_nodes(self):
        na = self.hoa_a.bfs()
        nb = self.hoa_b.bfs()

        if na == nb:
            return 1
        
        lcs = longest_common_subsequence(na, nb)
        return lcs / max(len(na), len(nb))


    def compare_links(self):
        na = self.hoa_a.bfs_links()
        nb = self.hoa_b.bfs_links()

        if na == nb:
            return 1
        
        lcs = longest_common_subsequence(na, nb)
        return lcs / max(len(na), len(nb))


    #
    # constraints are compared only for HOAs having identical structure
    # 
    def compare_constraints(self):
        a_lc = [str(x[0]) + "-" + str(x[1]) + "-" + str(x[2]) for x in self.hoa_a.link_constraints] 
        b_lc = [str(x[0]) + "-" + str(x[1]) + "-" + str(x[2]) for x in self.hoa_b.link_constraints]
        
        a_idt = [str(x[0]) + "-" + str(x[1]) for x in self.hoa_a.identical_at] 
        b_idt = [str(x[0]) + "-" + str(x[1]) for x in self.hoa_b.identical_at]
        
        a_sidt = [str(x[0]) + "-" + str(x[1]) for x in self.hoa_a.semi_identical_at]
        b_sidt = [str(x[0]) + "-" + str(x[1]) for x in self.hoa_a.semi_identical_at] 

        if a_lc == b_lc and a_idt == b_idt and a_sidt == b_sidt:
            print("[HOAComparator, warning] identical structure and contraints for two HOAs")
            return 1

        if a_lc <= b_lc and a_idt <= b_idt and a_sidt <= b_sidt:
            self.subconcept = True
            self.father = self.hoa_a.concept
            self.son = self.hoa_b.concept

        if b_lc <= a_lc and b_idt <= a_idt and b_sidt <= a_sidt:
            self.subconcept = True
            self.father = self.hoa_b.concept
            self.son = self.hoa_a.concept
        
        l1 = longest_common_subsequence(a_lc, b_lc) 
        l2 = longest_common_subsequence(a_idt, b_idt) 
        l3 = longest_common_subsequence(a_sidt, b_sidt) 

        sim_score = (l1 + l2 + l3) / (max(len(a_lc), len(b_lc)) + max(len(a_idt), len(b_idt)) + max(len(a_sidt), len(b_sidt)))
        return sim_score




if __name__ == "__main__":
    from AutomataMemory import AutomataMemory
    from SupervisedLearning import SupervisedLearner
    automata_memory = AutomataMemory()

    sl = SupervisedLearner('test_files/vertical_line.pat', automata_memory, verbose=False)
    sl.learn_concept()
    
    sl = SupervisedLearner('test_files/horizontal_line.pat', automata_memory, verbose=False)
    sl.learn_concept()
    
    sl = SupervisedLearner('test_files/square.pat', automata_memory, verbose=False)
    sl.learn_concept()

    sl = SupervisedLearner('test_files/square_cross.pat', automata_memory, verbose=False)
    sl.learn_concept()

    sl = SupervisedLearner('test_files/t.pat', automata_memory, verbose=False)
    sl.learn_concept()

    sl = SupervisedLearner('test_files/rect.pat', automata_memory, verbose=False)
    sl.learn_concept()

    automata_memory.info()

    hoa_square = automata_memory.get_automata('square')[0]
    hoa_rect = automata_memory.get_automata('rectangle')[0]
    hoa_t = automata_memory.get_automata('T')[0]
    hoa_squarec = automata_memory.get_automata('square_cross')[0]

    print("\nTESTING COMPARATOR")

    print("Test case 1: SQUARE, RECT")
    hcmp = HOAComparator(hoa_square, hoa_rect)
    print(hcmp.get_similarity())
    print(hcmp.is_subconcept())
        
    print("Test case 2: SQUARE, T")
    hcmp = HOAComparator(hoa_square, hoa_t)
    print(hcmp.get_similarity())
    print(hcmp.is_subconcept())
    
    print("Test case 3: SQUARE_CROSS, RECT")
    hcmp = HOAComparator(hoa_squarec, hoa_rect)
    print(hcmp.get_similarity())
    print(hcmp.is_subconcept())

    print("\nTesting complexity comparator")
    hc = list(automata_memory.get_hoa_concepts())
    for j in range(1, len(hc)):
        for i in range(0, j):
            ca, cb = hc[i], hc[j]
            hoa_a, hoa_b = automata_memory.get_automata(ca)[0], automata_memory.get_automata(cb)[0] 
            cc = HOAComplexityComparator(hoa_a, hoa_b)
            cmp = cc.compare()
            if cmp == 0:
                print(ca, cb, " identical complexity")
            elif cmp == -1:
                print(ca, cb, " more complex is", cb)
            else:
                print(ca, cb, " more complex is", ca)

            
