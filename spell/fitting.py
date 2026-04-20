from os import write
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

mode = Enum("mode", "exact neg_approx full_approx")

HC = dict[str, list[int]]
Simul = list[list[int]]
Pi = list[dict[int, int]]
Pr = dict[str, list[int]]
Mj = list[dict[int, int]] #HW: same structure as Pi

class Variables(NamedTuple):
    simul: Simul  #HW: = variable si,a in paper
    pi: Pi  #HW: = variable yi,j in paper
    pr: Pr  #HW: variable xj,r in paper
    hc: HC  #HW: = variable ci,a in paper
    mj: Mj


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

var_counter: int = 1

def fresh_var():
    global var_counter
    r = var_counter
    var_counter = var_counter + 1
    return r


def constraint_conceptname(
    size: int,
    A: Structure,
    hc: HC,
    ind_tp_idx,
    anti_types,
    type_var: list[dict[int, int]],
    simul: Simul,
):

    for pInd in range(size):
        for a in ind(A):
            yield (-simul[pInd][a], type_var[pInd][ind_tp_idx[a]]) #HW: paper (7)

        for idx, tp in anti_types.items():
            for cn in tp:
                yield (-type_var[pInd][idx], -hc[cn][pInd]) #HW: paper (5)

            yield [type_var[pInd][idx]] + [hc[cn][pInd] for cn in tp] #HW: paper (6)


def constraint_succ(
    size: int,
    A: Structure,
    sigma: Signature,
    pi: Pi,
    pr: Pr,
    mj: Mj,
    simul: Simul,
    exd: list[list[list[int]]],
    mjd: list[list[list[int]]],
    mjsat: list[list[dict[str, int]]]
):
    succs = compute_successors(sigma, A)

    link_ex = [[fresh_var() for a in ind(A)] for j in range(size)]
    link_mj = [[fresh_var() for a in ind(A)] for j in range(size)]

    #Existential Restriction Part MAJ-EXT ADAPTED
    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                yield [exd[pInd][pInd2][a], -pi[pInd][pInd2], mj[pInd][pInd2], link_ex[pInd2][a]] #HW: paper (9) / (9-Ex)

    for a in ind(A):
        for pInd2 in range(size):
            for rn in rolenames(sigma):
                succ_sim = [simul[pInd2][b] for b in succs[rn][a]]
                yield [-link_ex[pInd2][a], -pr[rn][pInd2]] + succ_sim #HW: paper (9) / (9-Ex)

    #Majority Restriction Part MAJ-EXT NEW
    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                pass
                yield [mjd[pInd][pInd2][a], -pi[pInd][pInd2], -mj[pInd][pInd2], link_mj[pInd2][a]]  # HW: paper (9) / (9-Mj)

    for a in ind(A):
        for pInd2 in range(size):
            for rn in rolenames(sigma):
                pass
                yield [-link_mj[pInd2][a], -pr[rn][pInd2], mjsat[pInd2][a][rn]]   # HW: paper (9) / (9-Mj)

    for pInd in range(size):
        for pInd2 in range(pInd + 1, size):
            for a in ind(A):
                for b, rn in A.rn_ext[a]:
                    if rn in rolenames(sigma):
                        yield [-mj[pInd][pInd2], -pi[pInd][pInd2], -pr[rn][pInd2], -mjsat[pInd2][a][rn], -mjd[pInd][pInd2][a]]


#MAJ-EXT NEW
def majority_encoding(
        size: int,
        A: Structure,
        sigma: Signature,
        simul: Simul,
        mjsat: list[list[dict[str, int]]],
):
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
                        yield [-mjsat[pInd2][a][rn]] # impossible to reach majority, mjsat must be false
                    elif majority_bound > len(succ_lits):
                        yield [-mjsat[pInd2][a][rn]]
                    else:
                        # Direction 1: mjsat -> majority condition
                        # now check for every relecant rolename, whether this role fulfills majority cardinality
                        # i.e. if more than half of all successors are of this role.
                        maj_enc_atleast = CardEnc.atleast(
                            succ_lits,
                            bound=majority_bound,
                            top_id=var_counter,
                            encoding=EncType.kmtotalizer
                        )
                        var_counter = maj_enc_atleast.nv + 1
                        for c in maj_enc_atleast.clauses:
                            yield [-mjsat[pInd2][a][rn]] + list(c)

                        # Direction 2: majority condition -> mjsat
                        maj_enc_atmost = CardEnc.atmost(
                            succ_lits,
                            bound=majority_bound - 1,
                            top_id=var_counter,
                            encoding=EncType.kmtotalizer
                        )
                        var_counter = maj_enc_atmost.nv + 1
                        for c in maj_enc_atmost.clauses:
                            yield [mjsat[pInd2][a][rn]] + list(c)

# MAJ-EXT NEW
def manage_defect_links(
    size: int,
    A: Structure,
    mj: Mj,
    DR: list[list[list[int]]],
    exd: list[list[list[int]]],
    mjd: list[list[list[int]]],
):
    for a in ind(A):
        for pInd2 in range(size):
            for pInd in range(pInd2):
                # link main defect to existential defect
                yield[mj[pInd][pInd2], -DR[pInd][pInd2][a], exd[pInd][pInd2][a]]
                yield [mj[pInd][pInd2], -exd[pInd][pInd2][a], DR[pInd][pInd2][a]]
                # link main defect to majority defect
                yield [-mj[pInd][pInd2], -DR[pInd][pInd2][a], mjd[pInd][pInd2][a]]
                yield [-mj[pInd][pInd2], -mjd[pInd][pInd2][a], DR[pInd][pInd2][a]]


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


# Returns a list of constraints that enforce the simulation conditions
def simulation_constraints(
    size: int, sigma: Signature, A: Structure, mapping: Variables
):
    simul = mapping[0]
    pi = mapping[1]
    pr = mapping[2]
    hc = mapping[3]
    mj = mapping[4]

    # Defect vars MAJ-EXT NEW
    DR = [[[fresh_var() for a in ind(A)] for j in range(size)] for i in range(size)] #HW: 'umbrella'/main defect
    exd = [[[fresh_var() for a in ind(A)] for j in range(size)] for i in range(size)] #HW: existential defect - MAJ-EXT NEW
    mjd = [[[fresh_var() for a in ind(A)] for j in range(size)] for i in range(size)] #HW: majority defect - MAJ-EXT NEW
    mjsat = [[{rn: fresh_var() for rn in rolenames(sigma)} for a in ind(A)] for j in range(size)] #HW: majority satisfiable - MAJ-EXT NEW

    ind_tp_idx, anti_types = compute_types(A, sigma)
    type_var = [{idx: fresh_var() for idx in set(ind_tp_idx)} for i in range(size)]

    yield from majority_encoding(size, A, sigma, simul, mjsat)
    yield from manage_defect_links(size, A, mj, DR, exd, mjd)
    yield from constraint_conceptname(size, A, hc, ind_tp_idx, anti_types, type_var, simul)
    yield from constraint_succ(size, A, sigma, pi, pr, mj, simul, exd, mjd, mjsat)

    # positive Simulationsbedingung
    for pInd in range(size):
        for a in ind(A):
            #In some cases this can be a bottleneck, we could use the type-variables here
            cn_part = [-type_var[pInd][ind_tp_idx[a]]]
            rn_part = [DR[pInd][pInd2][a] for pInd2 in range(pInd + 1, size)]
            yield [simul[pInd][a]] + cn_part + rn_part #HW: paper (8)

    # Same for roles
    for pInd in range(size):
        for pInd2 in range(pInd + 1, size):
            for a in ind(A):
                yield [-DR[pInd][pInd2][a], pi[pInd][pInd2]] #HW: paper (11)
                for rn in rolenames(sigma):

                    for b, rn_succ in A.rn_ext[a]:
                        if rn_succ == rn:
                            yield [mj[pInd][pInd2], -DR[pInd][pInd2][a], -pr[rn][pInd2], -simul[pInd2][b]] #HW: (12-EX)

                    yield [-mj[pInd][pInd2], -DR[pInd][pInd2][a], -pr[rn][pInd2], -mjsat[pInd2][a][rn]] #HW: (12-Maj)

    for pInd in range(size):
        for a in ind(A):
            for pInd2 in range(pInd + 1, size):
                yield [-simul[pInd][a], -DR[pInd][pInd2][a]] #HW: paper (10)


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


def is_model(
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
    mj = mapping.mj

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
                    if mj[pInd][pInd2] in model: #if mg flag is activated, interpret query edge as majority quantifier
                        q.rn_ext[pInd].add((pInd2, "MAJ " + rn))
                    else:
                        q.rn_ext[pInd].add((pInd2, rn))

    return q


def create_variables(size: int, sigma: Signature, A: Structure) -> Variables:
    global var_counter
    var_counter = 1

    simul = [[fresh_var() for ind in ind(A)] for pInd in range(size)]

    # pi[i][j] is true if there is an edge between i and j
    pi = [
        {pInd2: fresh_var() for pInd2 in range(pInd1 + 1, size)}
        for pInd1 in range(size)
    ]

    # pr[rn][i] is true if product ind i has an incoming rn role
    pr = {rn: [fresh_var() for pInd in range(size)] for rn in rolenames(sigma)}

    # Conceptnames of product individuals
    hc = {cn: [fresh_var() for pInd in range(size)] for cn in conceptnames(sigma)}

    # MAJ-EXT NEW
    # mj[i][j] is true if there is an edge between i and j and this edge is interpreted as a majority quantifier,
    # otherwise it is interpreted as an existential quantifier
    mj = [
        {pInd2: fresh_var() for pInd2 in range(pInd1 + 1, size)}
        for pInd1 in range(size)
    ]

    return Variables(simul, pi, pr, hc, mj)


def tree_query_constraints(size: int, sigma: Signature, v: Variables):
    pi = v.pi
    pr = v.pr
    mj = v.mj

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

    #MAJ-EXT NEW
    #Mj flag can only be existend if there exists an pi edge
    for i in range(1,size):
        for j in range(i + 1, size):
            yield (-mj[i][j], pi[i][j])

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

    for c in tree_query_constraints(size, sigma, mapping):
        pysolvers.glucose41_add_cl(g.glucose, c)

    for c in simulation_constraints(size, sigma, A, mapping):
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
