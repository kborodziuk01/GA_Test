import pynetlogo
import random
from deap import base
from deap import creator
from deap import tools




def setup_and_run(netlogo):
    # set parameters
    netlogo.command("set model-version \"sheep-wolves-grass\"")
    netlogo.command("set initial-number-sheep 100")
    netlogo.command("set initial-number-wolves 50")
    netlogo.command("set grass-regrowth-time 30")

    netlogo.command("setup")
    netlogo.command("repeat 1000 [go]")

    ended = False
    c = 0
    while c < 1000 :
        c = int(netlogo.report("ticks"))
        ended = bool(netlogo.report("ended"))
        if ended == True:
            c = 1001



def init_GA_values(netlogo,sf, wf, sr, wr):
    netlogo.command("set sheep-gain-from-food " + str(sf))
    netlogo.command("set wolf-gain-from-food " + str(wf))
    netlogo.command("set sheep-reproduce " + str(sr))
    netlogo.command("set wolf-reproduce " + str(wr))


def get_results(netlogo):
    m_sheep = float(netlogo.report("mean_sheep"))
    m_wolves = float(netlogo.report("mean_wolves"))

    return [m_sheep, m_wolves]


def gen_chromosome(sf, wf, sr, wr):
    chromosome = [sf, wf, sr, wr]
    return chromosome


def gen_ind(netlogo):
    sf, wf, sr, wr = gen_init_val()

    chromosome = gen_chromosome(sf, wf, sr, wr)

    init_GA_values(netlogo,sf, wf, sr, wr)
    setup_and_run(netlogo)
    res = get_results(netlogo)

    return [res, chromosome]


def run_ind(netlogo, chromosome):
    init_GA_values(netlogo, chromosome[0], chromosome[1], chromosome[2], chromosome[3])
    setup_and_run(netlogo)
    res = get_results(netlogo)

    return [res, chromosome]


def gen_init_val():
    sf = random.randint(1, 50)
    wf = random.randint(1, 100)
    sr = random.randint(1, 20)
    wr = random.randint(1, 20)

    return sf, wf, sr, wr


def fitness_2_animal(ind):
    w_val = 100
    s_val = 200
    m_sheap = ind[0][0][0]
    m_wolves = ind[0][0][1]

    d_sheep = abs(s_val - m_sheap)
    d_wolves = abs(w_val - m_wolves)

    return [d_sheep, d_wolves]


def fitness_ratio(ind):
    # expected ratio of 0.5 for wolves over sheep
    # expect 2x the amount of sheep that wolves
    # absolute value taken of ratio - expected ratio
    # to calculate the distance from the expected answer
    w_val = 125
    s_val = 345

    exp_ratio = w_val / s_val

    m_sheap = ind[0][0][0]
    m_wolves = ind[0][0][1]

    d_sheep = abs(s_val - m_sheap) / 100
    d_wolves = abs(w_val - m_wolves) / 100

    if d_sheep == 0:
        d_sheep = 999
    if d_wolves == 0:
        d_wolves = 999

    try:
        ratio = m_wolves / m_sheap
    except ZeroDivisionError:
        ratio = 999

    final_fit = abs(ratio - exp_ratio) + (d_wolves + d_sheep)


    return [final_fit]


def format_mut_zeromax(new_chro,maxes):
    MAX_SF = maxes[0]
    MAX_WF = maxes[1]
    MAX_SR = maxes[2]
    MAX_WR = maxes[3]

    if new_chro[0] > MAX_SF:
        new_chro[0] = MAX_SF
    elif new_chro[0] <= 0:
        new_chro[0] = 1

    if new_chro[1] > MAX_WF:
        new_chro[1] = MAX_WF
    elif new_chro[1] <= 0:
        new_chro[1] = 1

    if new_chro[2] > MAX_SR:
        new_chro[2] = MAX_SR
    elif new_chro[2] <= 0:
        new_chro[2] = 1

    if new_chro[3] > MAX_WR:
        new_chro[3] = MAX_WR
    elif new_chro[3] <= 0:
        new_chro[3] = 1


def format_mut_add_remove(chro, new_chro, n,maxes):
    rate = random.randint(1, n)

    MAX_SF = maxes[0]
    MAX_WF = maxes[1]
    MAX_SR = maxes[2]
    MAX_WR = maxes[3]

    if new_chro[0] > MAX_SF:
        new_chro[0] = chro[0] - rate
    elif new_chro[0] <= 0:
        new_chro[0] = chro[0] + rate

    if new_chro[1] > MAX_WF:
        new_chro[1] = chro[1] - rate
    elif new_chro[1] <= 0:
        new_chro[1] = chro[1] + rate

    if new_chro[2] > MAX_SR:
        new_chro[2] = chro[2] - rate
    elif new_chro[2] <= 0:
        new_chro[2] = chro[2] + rate

    if new_chro[3] > MAX_WR:
        new_chro[3] = chro[3] - rate
    elif new_chro[3] <= 0:
        new_chro[3] = chro[3] + rate


def mutate(ind, n, prob,maxes):
    chro = ind[0][1]
    new_chro = []



    for x in chro:
        if random.random() < prob:
            rate = random.randint(1, n)
            if random.random() < 0.5:
                x = x + rate
                new_chro.append(x)
            else:
                x = x - rate
                new_chro.append(x)
        else:
            new_chro.append(x)

    format_mut_add_remove(chro, new_chro, n,maxes)

    ind[0][1] = [x for x in new_chro]


def prep_res_1_fit(fits, pop,l_min,l_wolves,l_sheep,hof):
    length = len(pop)
    mean = sum(fits) / length
    sum2 = sum(x * x for x in fits)
    std = abs(sum2 / length - mean ** 2) ** 0.5



    print("  Min Fitness %s" % min(fits))
    print("  Max Fitness %s" % max(fits))
    print("  Avg Fitness %s" % mean)
    print("  Std %s" % std)

    indx = fits.index(min(fits))

    wolves = pop[indx][0][0][1]
    sheep = pop[indx][0][0][0]
    print(pop[indx])
    print("Best Performing: Fitness: " + str(pop[indx].fitness.values) +  " Wolves: " + str(wolves) + " Sheep: " + str(sheep) + " Chromosome: " + str(pop[indx][0][1]))
    if len(hof) == 0:
        hof.append([min(fits), pop[indx]])
    elif len(hof) >= 1 and min(fits) < hof[-1][0]:
        hof.append([min(fits), pop[indx]])

    l_min.append(pop[indx].fitness.values[0])
    l_wolves.append(wolves)
    l_sheep.append(sheep)

def prep_res_2_fit(fits,hof,hof2,pop):
    sheep = [x[0] for x in fits]
    wolves = [x[1] for x in fits]

    print("  Min Sheep %s" % min(sheep))
    print("  Min Wolves %s" % min(wolves))

    print("  Max Sheep %s" % max(sheep))
    print("  Max Wolves %s" % max(wolves))

    # print("  Avg %s" % mean)
    # print("  Std %s" % std)

    s_indx = sheep.index(min(sheep))
    print(pop[s_indx])
    if len(hof) == 0:
        hof.append([min(sheep), pop[s_indx]])
    elif len(hof) >= 1 and min(sheep) < hof[-1][0]:
        hof.append([min(sheep), pop[s_indx]])

    w_indx = wolves.index(min(wolves))
    print(pop[w_indx])
    if len(hof2) == 0:
        hof2.append([min(wolves), pop[w_indx]])
    elif len(hof2) >= 1 and min(wolves) < hof2[-1][0]:
        hof2.append([min(wolves), pop[w_indx]])




def percent_label(l):
    b = list(set(l))
    for x in b:
        c = l.count(x)
        per = (c / len(l)) * 100
        print("Label : '" + str(x) + "' constitutes " + str(round(per, 2)) + "% of the data.")