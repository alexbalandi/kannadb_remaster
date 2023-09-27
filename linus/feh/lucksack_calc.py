from collections import defaultdict


def ListSum(l1, l2):
    l3 = [0] * max(len(l1), len(l2))
    for i in range(len(l3)):
        if len(l1) > i:
            l3[i] += l1[i]
        if len(l2) > i:
            l3[i] += l2[i]
    return l3


def ListMulti(l1, multi):
    return [x * multi for x in l1]


def RemoveZeroTrail(l1):
    while len(l1) and l1[-1] == 0:
        l1 = l1[:-1]
    return l1


# input: number of orbs, list: [
orb_costs = [5, 4, 4, 4, 3]
max_rolls_for_guaranteed = 120
avg_unit_cost = 4


def GetChances(orbs, summon_no_pity, units_aggregate, memo):

    # units aggregate:
    # is_target, is_same_color, is_break_pity: map to chance

    if orbs < orb_costs[0]:
        return [1.0]

    memokey = orbs
    if memokey in memo:
        return memo[memokey]

    total_ssr = 0
    for ((_, _, is_break_pity), chance) in units_aggregate.items():
        if is_break_pity:
            total_ssr += chance

    assert total_ssr > 0

    ssr_chance = total_ssr + (summon_no_pity // 5) * 0.5
    if summon_no_pity > 120:
        ssr_chance = 1.0

    ssr_multi = ssr_chance / total_ssr
    if total_ssr >= 1:
        common_multi = 0
    else:
        common_multi = (1.0 - ssr_chance) / (1.0 - total_ssr)

    def SimCircle(orbs, remain, opens, pitybroken, memo):
        if remain == 0:
            ns = summon_no_pity + opens
            if pitybroken:
                ns = 0
            return GetChances(orbs, ns, units_aggregate, memo)

        minimemokey = ("linus", orbs, remain, opens, pitybroken)
        if minimemokey in memo:
            return memo[minimemokey]

        res = [0] * (orbs // avg_unit_cost)

        for (
            (is_target, is_same_color, is_break_pity),
            raw_chance,
        ) in units_aggregate.items():
            if is_break_pity:
                chance = ssr_multi * raw_chance
            else:
                chance = common_multi * raw_chance
            if orbs >= orb_costs[opens] and (is_same_color or (opens == 0 and remain == 1)):
                # open this circle.
                minires = SimCircle(
                    orbs - orb_costs[opens],
                    remain - 1,
                    opens + 1,
                    pitybroken or is_break_pity,
                    memo,
                )
                if is_target:
                    minires = [0] + minires

            else:
                # do not open
                minires = SimCircle(orbs, remain - 1, opens, pitybroken, memo)

            minires = ListMulti(minires, chance)
            minires = RemoveZeroTrail(minires)
            res = ListSum(res, minires)

        res = RemoveZeroTrail(res)
        memo[minimemokey] = res
        return res

    memo[memokey] = SimCircle(orbs, len(orb_costs), 0, 0, memo)
    return memo[memokey]


def FehSnipeProbability(orbs, units, target_unit_id):
    # units: a list of (unit_id, color_id, is_break_pity, chance_of_appearing)

    unit_sum_chance = 0
    for _, _, _, chance in units:
        assert 0 <= chance <= 1, chance
        unit_sum_chance += chance
    assert abs(unit_sum_chance - 1.0) < 1e-9, unit_sum_chance

    # get target unit
    found = False
    for unit_id, color_id, is_break_pity, chance in units:
        if unit_id == target_unit_id:
            found = True
            target_color = color_id

    assert found

    units_aggregate = defaultdict(float)
    # is_target, is_same_color, is_break_pity: map to chance

    for unit_id, color_id, is_break_pity, chance in units:
        mapkey = (unit_id == target_unit_id, color_id == target_color, is_break_pity)
        units_aggregate[mapkey] += chance

    memo = {}
    return GetChances(orbs, 0, units_aggregate, memo)
