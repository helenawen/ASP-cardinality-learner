import time
from enum import Enum
from typing import NamedTuple, Union

from pysat.card import CardEnc, EncType
from pysat.solvers import Glucose4, pysolvers

from .structures import (
    Signature,
    Structure,
    conceptname_ext,
    conceptnames,
    generate_all_trees,
    ind,
    restrict_to_neighborhood,
    rolenames,
    solution2sparql,
)

#TODO:
# <= for ELN and ELQ (incl. model2fitting updaten)
# Documentation! of final clauses and variables for Cardinality Restrictions
# 2 or 3 more toy examples for ELN and ELQ to check (but works on ELMAJ and ELN and ELQ test cases so far)

mode = Enum("mode", "exact neg_approx full_approx")

# --- CREATE DATA STRUCTURES AND VARIABLES ---
# wow omg slay girly! so good implemedted, so inspiring 8)
HC     = dict[str, list[int]]        # [cn][pInd]
Edge   = list[dict[int, int]]        # [i][j] (pi, is_ex, is_maj, is_num)
Pr     = dict[str, list[int]]        # [rn][pInd]
Defect = list[list[list[int]]]       # [i][j][a] (defect, ex_def, maj_def, num_def)
Simul  = list[list[int]]             # [pInd][a]
SimulMaj = list[list[dict[str, int]]]  # [j][a][rn]
SimulNum = list[list[dict[str, list[int]]]]  # [j][a][rn][n]
NumBound = list[list[int]]


class Variables(NamedTuple):
    #Structure
    pi: Edge  #HW: = variable yi,j in paper
    pr: Pr  #HW: variable xj,r in paper
    hc: HC  #HW: = variable ci,a in paper
    is_ex: Edge
    is_maj: Edge
    is_num: Edge
    #Simulation
    simul: Simul  #HW: = variable si,a in paper
    maj_sim: SimulMaj
    num_sim_geq: SimulNum
    num_bound: NumBound
    #num_sim_leq: SimulNum
    #Defects
    defect: Defect
    ex_def: Defect
    maj_def: Defect
    num_def: Defect

var_counter = 1
N_MAX = 5

def fresh_var():
    global var_counter
    r = var_counter
    var_counter = var_counter + 1
    return r

def create_variables(size: int, sigma: Signature, A: Structure) -> Variables:
    global var_counter
    var_counter = 1

    # pi[i][j] is true if there is an edge between i and j
    pi = [
        {pInd2: fresh_var() for pInd2 in range(pInd1 + 1, size)}
        for pInd1 in range(size)
    ]

    # pr[rn][i] is true if product ind i has an incoming rn role
    pr = {rn: [fresh_var() for pInd in range(size)] for rn in rolenames(sigma)}

    # Conceptnames of product individuals
    hc = {cn: [fresh_var() for pInd in range(size)] for cn in conceptnames(sigma)}

    # EDGE TYPE HANDLING
    # each edge can either be interpreted as an existential restriction (original), a majority quantifier or a number restriction
    # is_ex[i][j], is_maj[i][j], is_num[i][j] is true if there is an edge between i and j which is interpreted as existential, majority or number restriction respectively, false otherwise
    is_ex = [
        {pInd2: fresh_var() for pInd2 in range(pInd1 + 1, size)}
        for pInd1 in range(size)
    ]

    is_maj = [
        {pInd2: fresh_var() for pInd2 in range(pInd1 + 1, size)}
        for pInd1 in range(size)
    ]

    is_num = [
        {pInd2: fresh_var() for pInd2 in range(pInd1 + 1, size)}
        for pInd1 in range(size)
    ]

    #Simulation variables
    simul = [[fresh_var() for a in ind(A)] for i in range(size)]
    maj_sim = [[{rn: fresh_var() for rn in rolenames(sigma)} for a in ind(A)] for i in range(size)]
    #num_sim = [[{rn: fresh_var() for rn in rolenames(sigma)} for a in ind(A)] for i in range(size)]
    num_sim_geq = [[{rn: [fresh_var() for n in range(1, N_MAX +1)] for rn in rolenames(sigma)} for _ in ind(A)]for j in range(size)]
    #num_sim_leq = [[{rn: [fresh_var() for n in range(1, N_MAX +1)] for rn in rolenames(sigma)} for _ in ind(A)]for j in range(size)]
    num_bound = [[fresh_var() for n in range(1, N_MAX + 1)] for j in range(size)]

    # Defect variables
    defect = [[[fresh_var() for a in ind(A)] for j in range(size)] for i in range(size)]
    ex_def = [[[fresh_var() for a in ind(A)] for j in range(size)] for i in range(size)]
    maj_def = [[[fresh_var() for a in ind(A)] for j in range(size)] for i in range(size)]
    num_def = [[[fresh_var()for a in ind(A)] for j in range(size)] for i in range(size)]

    return Variables(pi, pr, hc, is_ex, is_maj, is_num, simul, maj_sim, num_sim_geq, num_bound, defect, ex_def, maj_def, num_def) #num_sim_leq

# --- CREATE CLAUSES NEEDED FOR ENCODING ---
#creates the clauses needed to ensure correct structure of query
def query_structure_constraints(size: int, sigma: Signature, v: Variables):
    pi = v.pi
    pr = v.pr

    if size > 0 and size < 12:
        ktrees = list(generate_all_trees(size))

        treechoice = [fresh_var() for tree in ktrees]
        # At least one tree
        yield treechoice

        if size < 14:
            # At most one tree. Skip this if size gets too large, since it grows quadratically in the number of trees
            for j in range(0, len(ktrees)):
                for i in range(j):
                    yield (-treechoice[i], -treechoice[j])

        for t in range(len(ktrees)):
            tree = ktrees[t]
            for j in range(1, size):
                for i in range(j):
                    if tree[j - 1] == i:
                        yield (-treechoice[t], pi[i][j])
                    else:
                        yield (-treechoice[t], -pi[i][j])

    # Every pInd has at least a predecessor HW: paper (1)
    for j in range(1, size):
        yield [pi[i][j] for i in range(j)]

    # Every pInd has at most one predecessor HW: paper (2)
    for j in range(1, size):
        for i1 in range(j):
            for i2 in range(i1):
                yield [-pi[i1][j], -pi[i2][j]]

    # Every pind has at least one incoming role HW:  paper (3)
    for i in range(1, size):
        yield [pr[rn][i] for rn in rolenames(sigma)]

    # Every pInd has at most one incoming role HW: paper (4)
    rns = list(rolenames(sigma))
    for i in range(1, size):
        for r1 in range(len(rns)):
            for r2 in range(r1):
                yield (-pr[rns[r1]][i], -pr[rns[r2]][i])

#creates clauses needed for handling of correct edge type (ex, maj, num)
def edge_type_constraints(size: int, sigma: Signature, v: Variables):
    pi = v.pi
    is_ex = v.is_ex
    is_maj = v.is_maj
    is_num = v.is_num

    for i in range(0, size):
        for j in range(i + 1, size):

            # TEMPORARY: Force is_num to be False because constraints are not implemented yet.
            #yield [-is_num[i][j]]

            # edge types can only be existend, if edge exists
            yield (-is_ex[i][j], pi[i][j])
            yield (-is_maj[i][j], pi[i][j])
            yield (-is_num[i][j], pi[i][j])

            #if an edge is present, at least one edge type must be present
            yield(-pi[i][j], is_ex[i][j], is_maj[i][j], is_num[i][j])

            #at most one edge type is true, mutual exclusion of different restrictions
            yield(-is_ex[i][j], -is_maj[i][j])
            yield(-is_ex[i][j], -is_num[i][j])
            yield(-is_maj[i][j], -is_num[i][j])

#creates clauses needed for handling different types of defects (ex, maj, num) and their interplay with generic defect
def defect_type_constraints(size: int, A: Structure, v:Variables):
    is_ex = v.is_ex
    is_maj = v.is_maj
    is_num = v.is_num
    defect = v.defect
    ex_def = v.ex_def
    maj_def = v.maj_def
    num_def = v.num_def

    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                # link main defect to existential defect
                yield[-is_ex[pInd][pInd2], -defect[pInd][pInd2][a], ex_def[pInd][pInd2][a]]
                yield [-is_ex[pInd][pInd2], -ex_def[pInd][pInd2][a], defect[pInd][pInd2][a]]
                # link main defect to majority defect
                yield [-is_maj[pInd][pInd2], -defect[pInd][pInd2][a], maj_def[pInd][pInd2][a]]
                yield [-is_maj[pInd][pInd2], -maj_def[pInd][pInd2][a], defect[pInd][pInd2][a]]
                # link main defect to number defect
                yield [-is_num[pInd][pInd2], -defect[pInd][pInd2][a], num_def[pInd][pInd2][a]]
                yield [-is_num[pInd][pInd2], -num_def[pInd][pInd2][a], defect[pInd][pInd2][a]]

#creates the clauses needed for correct handling of concept names (Clauses 5,6,7, 8)
def conceptname_constraints(size: int, A: Structure,hc: HC, ind_tp_idx, anti_types, type_var: list[dict[int, int]], simul: Simul, defect: Defect):

    for pInd in range(size):
        for a in ind(A):
            yield (-simul[pInd][a], type_var[pInd][ind_tp_idx[a]]) #HW: paper (7)

        for idx, tp in anti_types.items():
            for cn in tp:
                yield (-type_var[pInd][idx], -hc[cn][pInd]) #HW: paper (5)

            yield [type_var[pInd][idx]] + [hc[cn][pInd] for cn in tp] #HW: paper (6)

    # positive Simulationsbedingung
    for pInd in range(size):
        for a in ind(A):
            # In some cases this can be a bottleneck, we could use the type-variables here
            cn_part = [-type_var[pInd][ind_tp_idx[a]]]
            rn_part = [defect[pInd][pInd2][a] for pInd2 in range(pInd + 1, size)]
            yield [simul[pInd][a]] + cn_part + rn_part  # HW: paper (8)

def number_bound_constraints(size: int, sigma: Signature, v: Variables):
    is_num = v.is_num
    num_bound = v.num_bound

    for j in range(1, size):
        # if is_num active for some parent, at least one bound selected
        # collect all parents of j
        parents_num = [is_num[i][j] for i in range(j)]

        # it at least on parent edge is NUM, at least one bound must be selected
        for i in range(j):
            yield [-is_num[i][j]] + [num_bound[j][n] for n in range(N_MAX)]

        #at most one bound must be selected
        for n1 in range(N_MAX):
            for n2 in range(n1):
                yield (-num_bound[j][n1], -num_bound[j][n2])

        # bound can only be set if node is reached by a NUM edge
        for n in range(N_MAX):
            yield [-num_bound[j][n]] + parents_num

#creates clauses needed for handling correct behaviour of successors.
#If there exists an edge from i to j, then either (one of) the succesors simulate or a defect must be present
def successor_constraints(size: int, A: Structure, sigma: Signature, v: Variables):
    pi = v.pi
    pr = v.pr
    is_ex = v.is_ex
    is_maj = v.is_maj
    is_num = v.is_num
    simul = v.simul
    maj_sim = v.maj_sim
    num_sim = v.num_sim_geq
    ex_def = v.ex_def
    maj_def = v.maj_def
    num_def = v.num_def
    num_bound = v.num_bound

    succs = compute_successors(sigma, A)

    #auxillary variables to link clauses
    link_ex = [[fresh_var() for a in ind(A)] for j in range(size)]
    link_maj = [[fresh_var() for a in ind(A)] for j in range(size)]
    link_num = [[fresh_var() for a in ind(A)] for j in range(size)]

    #Existential Restriction
    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                yield [ex_def[pInd][pInd2][a], -pi[pInd][pInd2], -is_ex[pInd][pInd2], link_ex[pInd2][a]] #HW: paper (9) / (9-Ex)
    for a in ind(A):
        for pInd2 in range(size):
            for rn in rolenames(sigma):
                succ_sim = [simul[pInd2][b] for b in succs[rn][a]]
                yield [-link_ex[pInd2][a], -pr[rn][pInd2]] + succ_sim #HW: paper (9) / (9-Ex)

    #Majority Restriction
    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                yield [maj_def[pInd][pInd2][a], -pi[pInd][pInd2], -is_maj[pInd][pInd2], link_maj[pInd2][a]]  # HW: paper (9) / (9-Mj)
    for a in ind(A):
        for pInd2 in range(size):
            for rn in rolenames(sigma):
                yield [-link_maj[pInd2][a], -pr[rn][pInd2], maj_sim[pInd2][a][rn]]   # HW: paper (9) / (9-Mj)

    # Number Restriction
    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                for n in range(1, N_MAX+1):
                    yield [num_def[pInd][pInd2][a], -pi[pInd][pInd2], -is_num[pInd][pInd2],link_num[pInd2][a]]  # HW: paper (9) / (9-NUM)
    for a in ind(A):
        for pInd2 in range(size):
            for rn in rolenames(sigma):
                for n in range(1, N_MAX+1):
                    yield [-link_num[pInd2][a], -pr[rn][pInd2], -num_bound[pInd2][n-1], num_sim[pInd2][a][rn][n-1]]  # HW: paper (9) / (9-NUM)

#creates clauses needed to ensure that simulations and defects are mutually exclusive, whenever a simulation is present no defect can be present and the other way around
def simulation_mx_defect_constraints(size: int, sigma: Signature, A: Structure, v: Variables):
    pi = v.pi
    pr = v.pr
    is_ex = v.is_ex
    is_maj = v.is_maj
    is_num = v.is_num
    simul = v.simul
    maj_sim = v.maj_sim
    num_sim = v.num_sim_geq #TODO
    defect =  v.defect
    ex_def = v.ex_def
    maj_def = v.maj_def
    num_def = v.num_def
    num_bound = v.num_bound

    #Ensure whenever a simulation (ex, maj, num) holds, no corresponding defect(ex, maj, num) can be present! (OG 10)
    #prevents introducing a defect when the situation actually is correct ex, maj, num respectively
    for pInd in range(size):
        for pInd2 in range(pInd + 1, size):
            for a in ind(A):
                yield [-simul[pInd][a], -defect[pInd][pInd2][a]]  # HW: paper (10)
                yield [-is_ex[pInd][pInd2], -simul[pInd][a], -ex_def[pInd][pInd2][a]]  # 10-EX
                for b, rn in A.rn_ext[a]:
                    if rn in rolenames(sigma):
                        yield [-is_maj[pInd][pInd2], -maj_sim[pInd2][a][rn], -maj_def[pInd][pInd2][a]]  # 10-MAJ
                        for n in range(1, N_MAX+1):
                            #yield [-is_num[pInd][pInd2], -num_sim[pInd2][a][rn][n-1], -num_def[pInd][pInd2][a]]  # 10-NUM
                            yield [-is_num[pInd][pInd2], -num_bound[pInd2][n - 1], -num_sim[pInd2][a][rn][n - 1],-num_def[pInd][pInd2][a]]

    #Ensure whenever a defect (ex, maj, num) is present, no corresponding simulation(ex, maj, num) can be hold! (OG 12)
    #prevents introducing a simulation when situation does not simulate ex,maj, num respectively
    for pInd in range(size):
        for pInd2 in range(pInd + 1, size):
            for a in ind(A):
                for rn in rolenames(sigma):
                    for b, rn_succ in A.rn_ext[a]:
                        if rn_succ == rn:
                            yield [-is_ex[pInd][pInd2], -defect[pInd][pInd2][a], -pr[rn][pInd2],-simul[pInd2][b]]  # 12-EX
                    yield [-is_maj[pInd][pInd2], -defect[pInd][pInd2][a], -pr[rn][pInd2], -maj_sim[pInd2][a][rn]]  # 12-MAJ
                    for n in range(1, N_MAX+1):
                        yield [-is_num[pInd][pInd2], -defect[pInd][pInd2][a], -pr[rn][pInd2],-num_bound[pInd2][n-1],-num_sim[pInd2][a][rn][n-1]]  # 12-NUM

    #Ensure whenever a defect is present then an actual successor must be present (OG 11)
    for pInd in range(size):
        for pInd2 in range(pInd + 1, size):
            for a in ind(A):
                yield [-defect[pInd][pInd2][a], pi[pInd][pInd2]] #(universal for EX, MAJ, NUM)

#creates constraints needed for majority simulation
def majority_constraints(size: int, A: Structure, sigma: Signature, simul: Simul, maj_sim: list[list[dict[str, int]]]):
    succs = compute_successors(sigma, A)
    succs_inds = compute_all_successors_by_individuals(A)
    global var_counter

    for pInd in range(size):
        for pInd2 in range(pInd + 1, size):
            for a in ind(A):

                total = len(succs_inds[a])

                for rn in rolenames(sigma):
                    majority_bound = (total // 2) + 1
                    succ_lits = [simul[pInd2][b] for b in succs[rn][a]]
                    if not succ_lits :
                        yield [-maj_sim[pInd2][a][rn]] # impossible to reach majority, maj_sim must be false
                    elif majority_bound > len(succ_lits):
                        yield [-maj_sim[pInd2][a][rn]]
                    else:
                        # Direction 1: maj_sim -> majority condition
                        # now check for every relevant rolename, whether this role fulfills majority cardinality
                        # i.e. if more than half of all successors are of this role.
                        maj_enc_atleast = CardEnc.atleast(
                            succ_lits,
                            bound=majority_bound,
                            top_id=var_counter,
                            encoding=EncType.kmtotalizer
                        )
                        var_counter = maj_enc_atleast.nv + 1
                        for c in maj_enc_atleast.clauses:
                            yield [-maj_sim[pInd2][a][rn]] + list(c)

                        # Direction 2: majority condition -> maj_sim
                        maj_enc_atmost = CardEnc.atmost(
                            succ_lits,
                            bound=majority_bound - 1,
                            top_id=var_counter,
                            encoding=EncType.kmtotalizer
                        )
                        var_counter = maj_enc_atmost.nv + 1
                        for c in maj_enc_atmost.clauses:
                            yield [maj_sim[pInd2][a][rn]] + list(c)

#creates constraints needed for number simulation, cardinality restrictions
def cardinality_constraints(size: int, sigma: Signature, A: Structure, v: Variables):
    simul = v.simul
    num_sim_geq = v.num_sim_geq
    #num_sim_leq = v.num_sim_leq
    global var_counter

    succs = compute_successors(sigma, A)

    for pInd2 in range(size):
        for a in ind(A):
            for rn in rolenames(sigma):
                succ_lits = [simul[pInd2][b] for b in succs[rn][a]]
                for n in range(1, N_MAX + 1):
                    idx = n - 1
                    # ≥n direction
                    if not succ_lits or n > len(succ_lits):
                        yield [-num_sim_geq[pInd2][a][rn][idx]]
                    else:
                        num_enc_atleast = CardEnc.atleast(
                            succ_lits,
                            bound=n,
                            top_id=var_counter,
                            encoding=EncType.kmtotalizer
                        )
                        var_counter = num_enc_atleast.nv + 1
                        for c in num_enc_atleast.clauses:
                            yield [-num_sim_geq[pInd2][a][rn][idx]] + list(c)
                        num_enc_atmost = CardEnc.atmost(
                            succ_lits,
                            bound=n-1,
                            top_id=var_counter,
                            encoding=EncType.kmtotalizer
                        )
                        var_counter = num_enc_atmost.nv + 1
                        for c in num_enc_atmost.clauses:
                            yield [num_sim_geq[pInd2][a][rn][idx]] + list(c)
                    # ≤n direction (symmetric), done later



# Calls all subfucntions which create clauses and returns list with all of them for SAT encoding
def sat_encoding_constraints(
    size: int, sigma: Signature, A: Structure, v: Variables
):
    simul = v.simul
    maj_sim = v.maj_sim
    defect = v.defect
    hc = v.hc

    ind_tp_idx, anti_types = compute_types(A, sigma)
    type_var = [{idx: fresh_var() for idx in set(ind_tp_idx)} for i in range(size)]

    yield from query_structure_constraints(size, sigma, v)
    yield from edge_type_constraints(size, sigma, v)
    yield from defect_type_constraints(size, A, v)
    yield from conceptname_constraints(size, A, hc, ind_tp_idx, anti_types, type_var, simul, defect)
    yield from successor_constraints(size, A, sigma, v)
    yield from simulation_mx_defect_constraints(size, sigma, A, v)
    yield from majority_constraints(size, A, sigma, simul, maj_sim)
    yield from cardinality_constraints(size, sigma, A, v)
    yield from number_bound_constraints(size, sigma, v)

# --- HELPER FUNCTIONS ---
def complement_type(tp, sigma: Signature):
    return tuple(cn for cn in conceptnames(sigma) if cn not in tp)

def compute_types(A: Structure, sigma: Signature):
    types: list[list[str]] = [[] for a in ind(A)]
    for cn in conceptnames(sigma):
        for a in conceptname_ext(A, cn):
            types[a].append(cn)

    fixed_types = {tuple(tp) for tp in types}
    fixed_types = list(fixed_types)
    fixed_types.sort(key="{}".format)
    fixed_types = list(map(frozenset, fixed_types))

    tp_map = {tp: idx for idx, tp in enumerate(fixed_types)}
    anti_types = {idx: complement_type(tp, sigma) for tp, idx in tp_map.items()}

    ind_tp_idx = [tp_map[frozenset(types[a])] for a in ind(A)]

    return ind_tp_idx, anti_types

def compute_successors(sigma: Signature, A: Structure):
    succs: dict[str, dict[int, set[int]]] = {}
    for rn in rolenames(sigma):
        succs[rn] = {a: set() for a in ind(A)}

    for a in ind(A):
        for b, rn in A.rn_ext[a]:
            if rn in rolenames(sigma):
                succs[rn][a].add(b)
    return succs

def compute_all_successors_by_individuals(A: Structure):
    succs_of_ind: dict[int, set[int]] = {}
    for a in ind(A):
        succs_of_ind[a] = set()
        for b, rn in A.rn_ext[a]:
            succs_of_ind[a].add(b)
    return succs_of_ind

# --- OPTIMIZATION FUNCTIONS ---
def non_empty_symbols(A: Structure) -> Signature:
    cns = [cn for cn in A.cn_ext.keys() if A.cn_ext[cn]]
    rns: set[str] = set()
    for a in ind(A):
        for _, rn in A.rn_ext[a]:
            rns.add(rn)
    rns2 = list(rns)

    cns.sort(key="{}".format)
    rns2.sort(key="{}".format)
    return (cns, rns2)


# Returns the (concept and role) symbols that are relevant given the positive
# examples
def determine_relevant_symbols(
    A: Structure, P: list[int], minP: int, dist: int
) -> Signature:

    (cns, rns) = non_empty_symbols(A)

    count = {cn: 0 for cn in cns}
    countr = {rn: 0 for rn in rns}

    for p in P:
        cns2: set[str] = set()
        rns2: set[str] = set()
        for cn in cns:
            if p in A.cn_ext[cn]:
                cns2.add(cn)

        dinds = {p}
        for r in range(dist):
            step: set[int] = set()
            for i1 in dinds:
                for i2, rn in A.rn_ext[i1]:
                    step.add(i2)
                    rns2.add(rn)
                    for cn in cns:
                        if i2 in A.cn_ext[cn]:
                            cns2.add(cn)
            dinds = step

        for cn in cns2:
            count[cn] += 1
        for rn in rns2:
            countr[rn] += 1

    cns = list(cn for (cn, c) in count.items() if c >= minP)

    rns = list(rn for (rn, c) in countr.items() if c >= minP)
    cns.sort(key="{}".format)
    rns.sort(key="{}".format)

    return (cns, rns)


def restrict_nb(
    k: int, A: Structure, P: list[int], N: list[int]
) -> tuple[Structure, list[int], list[int]]:
    (A2, mapping) = restrict_to_neighborhood(k+1, A, P + N)
    P2 = [mapping[a] for a in P]
    N2 = [mapping[a] for a in N]
    return A2, P2, N2

# --- DECODING MODEL INTO SEPARATING QUERY ---
def real_coverage(model, P: list[int], N: list[int], mapping: Variables) -> int:
    simul = mapping.simul
    cov = 0

    for a in P:
        if simul[0][a] in model:
            cov += 1
    for b in N:
        if -simul[0][b] in model:
            cov += 1

    return cov

'''def is_model(
    size: int, sigma: Signature, model: set[int], mapping: Variables, solver: Glucose4
):
    assums = []

    pi = mapping.pi
    pr = mapping.pr
    hc = mapping.hc

    for pInd in range(size):
        for cn in conceptnames(sigma):
            if hc[cn][pInd] in model:
                assums.append(hc[cn][pInd])
            else:
                assums.append(-hc[cn][pInd])
        for pInd2 in range(pInd + 1, size):
            for rn in rolenames(sigma):
                if pi[pInd][pInd2] in model and pr[rn][pInd2] in model:
                    assums.append(pi[pInd][pInd2])
                    assums.append(pr[rn][pInd2])

    return solver.solve(assumptions=assums)'''

def is_model(size, sigma, model, mapping, solver):
    assums = []
    pi = mapping.pi
    pr = mapping.pr
    hc = mapping.hc
    is_ex = mapping.is_ex
    is_maj = mapping.is_maj
    is_num = mapping.is_num
    num_bound = mapping.num_bound

    for pInd in range(size):
        for cn in conceptnames(sigma):
            assums.append(hc[cn][pInd] if hc[cn][pInd] in model else -hc[cn][pInd])
        for pInd2 in range(pInd + 1, size):
            # fix edge existence and type
            assums.append(pi[pInd][pInd2] if pi[pInd][pInd2] in model else -pi[pInd][pInd2])
            assums.append(is_ex[pInd][pInd2] if is_ex[pInd][pInd2] in model else -is_ex[pInd][pInd2])
            assums.append(is_maj[pInd][pInd2] if is_maj[pInd][pInd2] in model else -is_maj[pInd][pInd2])
            assums.append(is_num[pInd][pInd2] if is_num[pInd][pInd2] in model else -is_num[pInd][pInd2])
            for rn in rolenames(sigma):
                if pi[pInd][pInd2] in model and pr[rn][pInd2] in model:
                    assums.append(pr[rn][pInd2])

    # fix selected bound for NUM nodes
    for j in range(size):
        for n in range(N_MAX):
            assums.append(num_bound[j][n] if num_bound[j][n] in model else -num_bound[j][n])

    return solver.solve(assumptions=assums)

def minimize_concept_assertions(
    size: int, sigma: Signature, solver: Glucose4, mapping: Variables, model: set[int]
) -> set[int]:
    best_model = model

    # Greedily reduce number of concept assertions and abuse sat solver as a fast query engine
    for i in range(size):
        for cn in conceptnames(sigma):
            if mapping.hc[cn][i] in best_model:
                test_model = set(best_model)
                test_model.remove(mapping.hc[cn][i])
                test_model.add(-mapping.hc[cn][i])
                if is_model(size, sigma, test_model, mapping, solver):
                    best_model = test_model
    return best_model


def model2fitting_query(
    size: int, sigma: Signature, mapping: Variables, model: set[int]
) -> Structure:
    pi = mapping.pi
    pr = mapping.pr
    hc = mapping.hc
    is_ex = mapping.is_ex
    is_maj = mapping.is_maj
    is_num = mapping.is_num
    num_bound = mapping.num_bound
    num_sim_geq = mapping.num_sim_geq

    q = Structure(
        max_ind=size,
        cn_ext={cn: set() for cn in conceptnames(sigma)},
        rn_ext={a: set() for a in range(size)},
        indmap={},
        nsmap={},
    )

    for pInd in range(size):
        for cn in conceptnames(sigma):
            if hc[cn][pInd] in model:
                q.cn_ext[cn].add(pInd)
        for pInd2 in range(pInd + 1, size):
            for rn in rolenames(sigma):
                if pi[pInd][pInd2] in model and pr[rn][pInd2] in model:
                    if is_maj[pInd][pInd2] in model: #if mg flag is activated, interpret query edge as majority quantifier
                        q.rn_ext[pInd].add((pInd2, "MAJ " + rn))
                    elif is_num[pInd][pInd2] in model:
                        n = None
                        for idx, var in enumerate(num_bound[pInd2]):
                            if var in model:
                                n = idx + 1
                                break
                        if (n == 1): #TODO: later, only for >=, for >= and = 1 must be displayed bc then not anymore the same as existential restriction
                            q.rn_ext[pInd].add((pInd2, rn))
                        else:
                            q.rn_ext[pInd].add((pInd2, f" >= {n} {rn}"))
                    else: #corresponds to is_ex
                        q.rn_ext[pInd].add((pInd2, rn))

    return q

def create_coverage_formula(
    P: list[int], N: list[int], coverage: int, mapping: Variables, all_pos: bool
) -> list[list[int]]:
    simul = mapping.simul

    global var_counter
    if coverage == len(P) + len(N):
        return [[simul[0][a]] for a in P] + [[-simul[0][b]] for b in N]
    elif all_pos:
        lits = [-simul[0][b] for b in N]

        bound = max(coverage - len(P), 1)
        enc = CardEnc.atleast(
            lits, bound=bound, top_id=var_counter, encoding=EncType.kmtotalizer
        )

        var_counter = enc.nv + 1

        return [[simul[0][a]] for a in P] + enc.clauses
    else:
        lits = [simul[0][a] for a in P] + [-simul[0][b] for b in N]

        enc = CardEnc.atleast(
            lits, bound=coverage, top_id=var_counter, encoding=EncType.kmtotalizer
        )

        var_counter = enc.nv + 1

        return enc.clauses

# --- SOLVING PROCESS ---
# Constructs a formula to find a separating query of size and solves it
# Guaranted that we can reach min_coverage
def solve(
    size: int,
    A: Structure,
    P: list[int],
    N: list[int],
    coverage_lb: int,
    all_pos: bool,
    timeout: float = -1,
) -> Union[tuple[int, Structure], None]:

    time_start = time.process_time()
    A, P, N = restrict_nb(size, A, P, N)



    if all_pos:
        min_pos = len(P)
    else:
        # If we want to cover at least min_coverage examples, we have to cover at
        # least min_pos positive examples
        min_pos = max(coverage_lb - len(N), 1)
    # Use symbols that occur in distance k - 1 of at least min_pos positive example
    sigma = determine_relevant_symbols(A, P, min_pos, size - 1)

    g = Glucose4()
    mapping = create_variables(size, sigma, A)

    for c in sat_encoding_constraints(size, sigma, A, mapping):
        pysolvers.glucose41_add_cl(g.glucose, c)

    dt = time.process_time() - time_start
    best_sol = None
    coverage_ub = len(P) + len(N)
    while coverage_lb <= coverage_ub and (dt < timeout or timeout < 0):

        for c in create_coverage_formula(P, N, coverage_lb, mapping, all_pos):
            pysolvers.glucose41_add_cl(g.glucose, c)

        satisfiable = g.solve()
        if not satisfiable:
            g.delete()
            return best_sol

        # print(g.accum_stats())
        model: set[int] = set(g.get_model())  # type: ignore

        # DEBUG: print edge type flags for all edges
        for pInd in range(size):
            for pInd2 in range(pInd + 1, size):
                ex_val = mapping.is_ex[pInd][pInd2] in model
                maj_val = mapping.is_maj[pInd][pInd2] in model
                num_val = mapping.is_num[pInd][pInd2] in model
                pi_val = mapping.pi[pInd][pInd2] in model
                print(f"Edge ({pInd},{pInd2}): pi={pi_val}, is_ex={ex_val}, is_maj={maj_val}, is_num={num_val}")

        coverage_lb = real_coverage(model, P, N, mapping)

        if True:
            # Required for minimization
            for c in create_coverage_formula(P, N, coverage_lb, mapping, all_pos):
                pysolvers.glucose41_add_cl(g.glucose, c)

            model = minimize_concept_assertions(size, sigma, g, mapping, model)

        best_q = model2fitting_query(size, sigma, mapping, model)
        best_sol = (coverage_lb, best_q)
        print(solution2sparql(best_q))

        print(
            "== Coverage: {}/{} == Accuracy: {}".format(
                coverage_lb, coverage_ub, coverage_lb / coverage_ub
            )
        )
        coverage_lb = coverage_lb + 1
        dt = time.process_time() - time_start

    g.delete()
    return best_sol


# Search for a small separating query by incrementally increasing the size
def solve_incr(
    A: Structure,
    P: list[int],
    N: list[int],
    m: mode,
    timeout: float = -1,
    max_size: int = 19,
) -> tuple[int, Structure]:
    time_start = time.process_time()
    i = 1
    best_coverage = len(P)
    best_q = Structure(max_ind=1, cn_ext={}, rn_ext={0: set()}, indmap={}, nsmap={})
    dt = time.process_time() - time_start
    while (
        best_coverage < len(P) + len(N)
        and i <= max_size
        and (dt < timeout or timeout == -1)
    ):
        print("== Searching for a fitting query of size {}".format(i))
        if m == mode.exact:
            sol = solve(i, A, P, N, len(P) + len(N), True, timeout - dt)
        elif m == mode.neg_approx:
            sol = solve(i, A, P, N, best_coverage + 1, True, timeout - dt)
        else:
            sol = solve(i, A, P, N, best_coverage + 1, False, timeout - dt)
        if sol is not None:
            best_coverage, best_q = sol
        i += 1
        dt = time.process_time() - time_start

    print(
        "== Best query found with coverage {}/{}".format(best_coverage, len(P) + len(N))
    )
    print(solution2sparql(best_q))
    return (best_coverage, best_q)