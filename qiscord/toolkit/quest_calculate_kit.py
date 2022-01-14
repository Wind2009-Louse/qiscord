import math
from typing import Tuple
from qiscord.toolkit import quest_data
from qiscord.toolkit.function_kit import get_v_from_d
from qiscord.toolkit.quest_data import *

ATTACK_ORIGIN_MP = {"A": 70, "B": 0, "C": 20}
CHARGE_UP_MP = {0: 1.0, 1: 1.3, 2: 1.6, 3: 1.9, 4: 2.2, 5: 2.5, 6: 2.7, 7: 2.9, 8: 3.1, 9: 3.3, 10: 3.5, 11: 3.9, 12: 4.3, 13: 4.7, 14: 5.1, 15: 5.5, 16: 6.0, 17: 6.5, 18: 7.0, 19: 7.5, 20: 8.0}

##################
# 状态计算
##################

'''
判断对象是否为空，并适用状态
'''
def apply_art_notnull(art: Dict, target: QuestUnit=None):
    if target is not None:
        target.apply_art(art)

'''
判断对象是否为空，批量适用状态
'''
def apply_art_batch(art: Dict, team_list: List[QuestUnit]=[]):
    for tg in team_list:
        apply_art_notnull(art, tg)

'''
计算状态的适用对象
'''
def alloc_status(
    art_list: List[Dict],
    src_unit: QuestUnit, src_team_list: List[QuestUnit]=[],
    tgt_unit: QuestUnit=None, tgt_team_list: List[QuestUnit]=[]):

    for art in art_list:
        verb_code = get_v_from_d(art, "verbCode")
        effect_code = get_v_from_d(art, "effectCode")
        target_id = get_v_from_d(art, "targetId")
        if target_id == "ALL":
            if verb_code in ["BUFF", "CONDITION_GOOD", "IGNORE", "LIMITED_ENEMY_TYPE"]:
                apply_art_batch(art, src_team_list)
            elif verb_code in ["DEBUFF", "CONDITION_BAD"]:
                apply_art_batch(art, tgt_team_list)
            elif verb_code == "HEAL":
                if effect_code == "MP_DAMAGE":
                    apply_art_batch(art, tgt_team_list)
                else:
                    apply_art_batch(art, src_team_list)
            elif verb_code == "REVOKE":
                if effect_code in ["BUFF", "GOOD"]:
                    apply_art_batch(art, tgt_team_list)
                elif effect_code in ["DEBUFF", "BAD"]:
                    apply_art_batch(art, src_team_list)
        elif target_id == "CONNECT":
            if len(src_team_list) > 0:
                connect_target = src_team_list[0]
                apply_art_notnull(art, connect_target)
        # TODO 指定对象适用效果
        elif target_id == "LIMITED":
            pass
        elif target_id == "ONE":
            if verb_code == "CONDITION_GOOD":
                apply_art_notnull(art, tgt_unit)
            elif verb_code == "REVOKE":
                if effect_code == "BUFF":
                    apply_art_notnull(art, tgt_unit)
                elif effect_code == "BAD":
                    # TODO
                    pass
            # TODO 有些东西不好算
        elif target_id == "SELF":
            apply_art_notnull(art, src_unit)
        elif target_id == "TARGET":
            apply_art_notnull(art, tgt_unit)

##################
# MP计算
##################

'''计算攻击MP'''
def calc_attack_mp(unit: QuestUnit, disc_status: QuestDiscStatus, calc_charge_change=True) -> Tuple[bool, int]:
    current_disc = disc_status.disc[disc_status.disc_index]

    # 是否其他人出盘
    if current_disc.lower() == "o":
        disc_status.move_to_next()
        return False, 0
    
    # 是否自己使用Magia/Doppel
    if current_disc in ["M", "D"]:
        apply_art_list = unit.magia_art_list
        cost_mp = 1000
        if current_disc == "D":
            apply_art_list = unit.doppel_art_list
            cost_mp = 1500
        if len(apply_art_list) == 0:
            disc_status.move_to_next()
            raise ValueError("该角色没有对应效果！")
        if cost_mp > unit.current_mp:
            disc_status.move_to_next()
            raise ValueError("当前MP不足！")
        unit.dec_mp(cost_mp)
        gain_mp = 0
        for apply_art in apply_art_list:
            verb_code = get_v_from_d(apply_art, "verbCode")
            effect_code = get_v_from_d(apply_art, "effectCode")
            # MP回复，先算一下
            if verb_code == "HEAL" and effect_code == "MP":
                effect_value = get_v_from_d(apply_art, "effectValue")
                gain_mp += math.floor(effect_value * (unit.get_mp_stat() / 1000))
            alloc_status([apply_art], unit, [unit])
        disc_status.move_to_next()
        return True, gain_mp

    # 是否其他人使用ABC
    if current_disc not in ["A", "B", "C"]:
        if calc_charge_change:
            if current_disc != "c":
                disc_status.current_charge = 0
            else:
                disc_status.current_charge += 1
        disc_status.move_to_next()
        return False, 0
    
    # round (单盘基础MP × 格位加成 × 镜界系数 + 首A奖励)
    origin_mp = function_kit.get_v_from_d(ATTACK_ORIGIN_MP, current_disc, 0) * (1 + disc_status.disc_index * 0.5)
    if disc_status.in_mirror:
        origin_mp *= 1.5
    if disc_status.is_first_accele():
        origin_mp += 30
    origin_mp = round(origin_mp)

    # floor (round (单盘原始MP × AcceleMP Buff) × 叠C倍率)
    after_accele_mp = origin_mp
    if current_disc == "A":
        after_accele_mp = round(after_accele_mp * (unit.accele_mp_stat / 1000))
        after_accele_mp = math.floor(after_accele_mp * function_kit.get_v_from_d(CHARGE_UP_MP, disc_status.current_charge, 0))
    
    # floor (after_accele_mp × 角色的攻击MP率 × MP获得量Buff)
    attack_mp = math.floor(after_accele_mp * (unit.attack_mp_rate / 1000) * (unit.get_mp_stat() / 1000))

    if current_disc == "B" and unit.mp_blast_num > 0:
        attack_mp += unit.mp_blast_num * 3

    unit.inc_mp(attack_mp)

    if calc_charge_change:
        if current_disc != "C" and unit.no_c_cost_stat == 0:
            disc_status.current_charge = 0
        elif current_disc == "C":
            disc_status.current_charge += 1
    
    disc_status.move_to_next()
    return True, attack_mp

'''计算受击MP'''
def calc_defense_mp(unit: QuestUnit, disc_status: QuestDiscStatus, is_weak_hit=False, is_magia=False) -> int:
    def_mp = 0

    if is_weak_hit and unit.mp_hit_weak_num > 0:
        weak_mp = math.floor(unit.mp_hit_weak_num * (unit.defense_mp_rate / 1000) * (unit.get_mp_stat() / 1000))
        unit.inc_mp(weak_mp)
        def_mp += weak_mp

    if not is_magia:
        basic_mp = 40
        if disc_status.in_mirror:
            basic_mp *= 1.5
        basic_mp = math.floor(basic_mp * (unit.defense_mp_rate / 1000) * (unit.get_mp_stat() / 1000))
        unit.inc_mp(basic_mp)
        def_mp += basic_mp
    
        if unit.mp_hit_num > 0:
            hit_mp = math.floor(unit.mp_hit_num * (unit.defense_mp_rate / 1000) * (unit.get_mp_stat() / 1000))
            unit.inc_mp(hit_mp)
            def_mp += hit_mp
    
    return def_mp

'''计算自回MP'''
def calc_regen_mp(unit: QuestUnit) -> int:
    regen_mp = math.floor(unit.mp_regen_num * (unit.get_mp_stat() / 1000))
    unit.inc_mp(regen_mp)
    return regen_mp
