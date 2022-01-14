import json
import math
import re
import copy
from typing import Dict, List

from requests.sessions import should_bypass_proxies
from qiscord.toolkit import chara, function_kit, skill_effect
from qiscord.toolkit.chara import Chara
from qiscord.toolkit.memoria import Memoria

MAX_MP = 1500
ORIGINAL_FLAG = "ORIGINAL_FLAG"
ENABLE_TURN = "enableTurn"

CHARM = "CHARM"
STUN = "STUN"
RESTRAINT = "RESTRAINT"
POISON = "POISON"
BURN = "BURN"
CURSE = "CURSE"
FOG = "FOG"
DARKNESS = "DARKNESS"
BLINDNESS = "BLINDNESS"

BAN_SKILL = "BAN_SKILL"
BAN_MAGIA = "BAN_MAGIA"

BAN_HEAL_HP = "INVALID_HEAL_HP"
BAN_HEAL_MP = "INVALID_HEAL_MP"

### TODO
ADJUST_PLUS_PERCENT_TABLE = {
    "BUFF": {
        "ACCEL": ["ampup", "accelempup"],
        "ATTACK": ["atkup","攻","剑"],
        "ATTACK_DARK": ["暗atkup","atkup_dark","暗攻","暗剑"],
        "ATTACK_FIRE": ["火atkup","atkup_fire","火攻","火剑"],
        "ATTACK_LIGHT": ["光atkup","atkup_light","光攻","光剑"],
        "ATTACK_TIMBER": ["木atkup","atkup_timber","atkup_forese","木攻","木剑"],
        "ATTACK_WATER": ["水atkup","atkup_water","水攻","水剑"],
        "BLAST": ["blastup","b伤"],
        "CHARGE": ["chargeup","c后伤"],
        "CHARGING": ["chargingup","c伤"],
        "DAMAGE": ["damageup","dmgup","红伤"],
        "DEFENSE": ["def","defup","防"],
        "DOPPEL": ["dup", "doppelup", "d伤"],
        "MAGIA": ["mup", "magiaup", "m伤"],
        "MP_GAIN": ["mpup"],
        "RESIST": ["resist", "耐性", "瓶子"]
    },
    "CONDITION_GOOD": {
        # AUTO_HEAL
        # AVOID
        # BARRIER
        # C_COMBO_PLUS
        # COUNTER
        # CRITICAL
        # DAMAGE_DOWN
        # DAMAGE_DOWN_ACCEL
        # DAMAGE_DOWN_BLAST
        # DAMAGE_DOWN_DARK
        # DAMAGE_DOWN_FIRE
        # DAMAGE_DOWN_LIGHT
        # DAMAGE_DOWN_NODISK
        # DAMAGE_DOWN_TIMBER
        # DAMAGE_DOWN_WATER
        # DAMAGE_UP
        # DAMAGE_UP_BAD
        # DEFENSE_IGNORED
        # GUTS
        # IMITATE_ATTRIBUTE
        # MP_PLUS_BLAST
        # MP_PLUS_DAMAGED
        # MP_PLUS_WEAKED
        # PROTECT
        # PROVOKE
        # PURSUE
        # SKILL_QUICK
        # SURVIVE
    }
}

### TODO
ADJUST_MINUS_PERCENT_TABLE = {
    "DEBUFF": {
        "ACCEL": ["ampup", "accelempup"],
        "ATTACK": ["atkup"],
        # BLAST
        # DAMAGE
        # DEFENSE
        "MAGIA": ["mup", "magiaup"],
        "MP_GAIN": ["mpup"],
        # RESIST
        # WEAK_CHARGE_DONE
        # WEAK_DARK
        # WEAK_FIRE
        # WEAK_LIGHT
        # WEAK_TIMBER
        # WEAK_WATER
    }
}

### TODO
ADJUST_PROBABILITY_TABLE = {
    "CONDITION_GOOD": {
        "NO_COST_CHARGE": [["c不消耗","无c"], {"effectValue": 1000}]
    },
    "ENCHANT": {
        CHARM: [["魅惑", "概率魅惑"], {}], STUN: [["眩晕", "概率眩晕", "晕", "概率晕"], {}], RESTRAINT: [["拘束", "概率拘束", "绑", "概率绑"], {}],
        POISON: [["毒","概率毒"], {"effectValue": 50}], BURN: [["烧伤", "概率烧伤", "烧"], {"effectValue": 100}], CURSE: [["诅咒", "概率诅咒"], {"effectValue": 150}],
        FOG: [["雾", "概率雾"], {"effectValue": 250}], DARKNESS: [["黑暗", "概率黑暗"], {"effectValue": 350}], BLINDNESS: [["幻惑", "概率幻惑"], {"effectValue": 500}],
        BAN_SKILL: [["技能封印", "技能不可", "封技能", "沉默", "概率技能封印", "概率技能不可", "概率封技能", "概率沉默"], {}],
        BAN_MAGIA: [["magia封印", "magia不可", "封magia", "封m", "概率magia封印", "概率magia不可", "概率封magia", "概率封m"], {}]
    }
}

ARG_ADJUST_TABLE = {"^\+([\S]+)%([\S]+)": ADJUST_PLUS_PERCENT_TABLE, "^\-([\S]+)%([\S]+)": ADJUST_MINUS_PERCENT_TABLE}

class QuestUnit:
    def __init__(self, c: Chara=None, rank: int=-1) -> None:
        self.jp_name = ""
        self.zh_name = ""

        self.current_hp = 0
        self.current_mp = 0

        self.attribute = ""
        self.hp = 0
        self.atk = 0
        self.defense = 0
        self.hp_percent = 1000
        self.atk_percent = 1000
        self.def_percent = 1000
        self.accele_percent = 1000
        self.blast_percent = 1000
        self.charge_percent = 1000

        self.attack_mp_rate = 1000
        self.defense_mp_rate = 1000

        self.memoria_list: List[skill_effect.Skill] = []
        self.connect_art_list = []
        self.magia_art_list = []
        self.doppel_art_list = []

        self.buff_list = []
        self.buff_hpmax_list = []
        self.buff_dying_list = []
        self.condition_goods_list = []
        self.debuff_list = []
        self.condition_bad_list = []

        self.ignore_list  = []
        self.enchant_list = []

        self.__reset_stat()
        if c is not None:
            self.load_chara(c, rank)
    
    def __reset_stat(self):
        '''
        单元数据初始化
        '''
        self.attribute_atk_stat = 0
        self.atk_stat           = 1000
        self.defense_stat       = 1000
        self.damage_buff_stat   = 1000
        self.damage_good_plus   = 0
        self.damage_cut_stat    = 0
        self.damage_bad_plus    = 0
        self.damage_cut_special_stat = []
        self.damage_limit_type_stat  = []
        self.attribute_weak_stat     = []

        self.blast_plus   = 0
        self.charge_dmg_stat  = 1000
        self.charging_plus = 0

        self.magia_dmg_stat  = 1000
        self.doppel_dmg_stat = 1000

        self.hp_regen_stat   = 0
        self.accele_mp_stat  = 1000
        self.mp_stat         = 1000
        self.mp_over100_plus = 0
        self.mp_regen_num    = 0
        self.mp_hit_num      = 0
        self.mp_hit_weak_num = 0
        self.mp_blast_num    = 0

        self.critical_stat           = 0
        self.avoid_stat              = 0
        self.ignore_cut_stat         = 0
        self.ignore_def_art_list     = []
        self.counter_art_list        = []
        self.provoke_art_list        = []
        self.protect_art_list        = []
        self.chase_art_list          = []
        self.ignore_avoid_art_list   = []
        self.ignore_counter_art_list = []
        self.ignore_provoke_art_list = []

        self.resist_plus             = 0
        self.skill_quict_art_list    = []
        self.variable_stat           = 0
        self.no_c_cost_stat          = 0
        self.c_combo_plus_stat       = 0
    
    def __resize_stat(self):
        '''
        调整单元数据在区间内
        '''
        self.attribute_atk_stat = max(0, self.attribute_atk_stat)
        self.atk_stat           = function_kit.get_value_in_between(self.atk_stat, 50, 2000)
        self.defense_stat       = function_kit.get_value_in_between(self.defense_stat, 50, 2000)
        self.damage_buff_stat   = function_kit.get_value_in_between(self.damage_buff_stat, 50, 2000)
        self.damage_good_plus   = max(0, self.damage_good_plus)
        self.damage_cut_stat    = max(0, self.damage_cut_stat)
        self.damage_bad_plus    = max(0, self.damage_bad_plus)

        self.blast_plus       = function_kit.get_value_in_between(self.blast_plus, -950, 1000)
        self.charge_dmg_stat  = function_kit.get_value_in_between(self.charge_dmg_stat, 50, 2000)
        self.charging_plus    = function_kit.get_value_in_between(self.charging_plus, -950, 1000)

        self.magia_dmg_stat  = function_kit.get_value_in_between(self.magia_dmg_stat, 50, 2000)
        self.doppel_dmg_stat = function_kit.get_value_in_between(self.doppel_dmg_stat, 50, 2000)

        self.hp_regen_stat   = max(0, self.hp_regen_stat)
        self.accele_mp_stat  = function_kit.get_value_in_between(self.accele_mp_stat, 50, 2000)
        self.mp_stat         = function_kit.get_value_in_between(self.mp_stat, 50, 2000)
        self.mp_over100_plus = function_kit.get_value_in_between(self.mp_over100_plus, -950, 1000)
        self.mp_regen_num    = max(0, self.mp_regen_num)
        self.mp_hit_num      = max(0, self.mp_hit_num)
        self.mp_hit_weak_num = max(0, self.mp_hit_weak_num)
        self.mp_blast_num    = max(0, self.mp_blast_num)

        self.critical_stat       = max(0, self.critical_stat)
        self.avoid_stat          = max(0, self.avoid_stat)
        self.ignore_cut_stat     = max(0, self.ignore_cut_stat)

        self.resist_plus         = function_kit.get_value_in_between(self.resist_plus, -950, 1000)
        self.variable_stat       = max(0, self.variable_stat)
        self.no_c_cost_stat      = max(0, self.no_c_cost_stat)
        self.c_combo_plus_stat   = max(0, self.c_combo_plus_stat)

    def load_chara(self, c: Chara, rank: int=-1):
        '''
        根据角色设置单元
        '''
        if c is None:
            raise
        chara_card = None
        if rank > 0:
            for card in c.card_list:
                if card.rank == rank:
                    chara_card = card
                    break
        if chara_card is None:
            chara_card = c.card_list[-1]
        self.attribute = c.attribute
        self.hp = chara_card.max_hp
        self.atk = chara_card.max_atk
        self.defense = chara_card.max_def
        self.current_hp = self.hp
        self.hp_percent += chara_card.awaken_hp_percent
        self.atk_percent += chara_card.awaken_atk_percent
        self.def_percent += chara_card.awaken_def_percent
        self.accele_percent += chara_card.awaken_accele_percent + c.enhance_accele
        self.blast_percent += chara_card.awaken_blast_percent + c.enhance_blast
        self.charge_percent += chara_card.awaken_charge_percent + c.enhance_charge

        self.attack_mp_rate = chara_card.attack_mp_rate
        self.defense_mp_rate = chara_card.def_mp_rate
        self.connect_art_list.extend(chara_card.connect_artlist)
        self.magia_art_list.extend(chara_card.magia_artlist)
        self.doppel_art_list.extend(chara_card.doppel_artlist)
        
        self.memoria_list.append(chara_card.ex_mlb_skill)
        self.memoria_list.extend(c.enhance_skill_list)
    
    def adjust_by_arg(self, arg: str) -> bool:
        '''
        根据参数自定义调整角色数据
        '''
        match_arg = arg

        # 判断回合数
        enable_turn = 0
        reg_turn = re.match("^([\S\s]+)[（\()](\d+)[Tt][）\)]", arg)
        if reg_turn is not None:
            match_arg = reg_turn.group(1)
            enable_turn = function_kit.trans_str_to_int(reg_turn.group(2), 0)

        # 添加状态
        triggered = False
        for reg_str, adjust_table in ARG_ADJUST_TABLE.items():
            if triggered:
                break
            reg = re.match(reg_str, match_arg)
            if reg is not None:
                percent_float_str = reg.group(1)
                adjust_type = reg.group(2)
                percent_float = function_kit.trans_str_to_float(percent_float_str, 0)
                if percent_float > 0:
                    effect_value = int(percent_float * 10)

                    for verb_code, detail_dict in adjust_table.items():
                        if triggered:
                            break
                        for effect_code, trigger_list in detail_dict.items():
                            for trigger in trigger_list:
                                if adjust_type.lower() == trigger.lower():
                                    triggered = True
                                    break
                            if not triggered:
                                continue
                            adjust_art = {"verbCode": verb_code, "effectCode": effect_code, "targetId": "SELF", "effectValue": effect_value, "probability": 1000}
                            if enable_turn > 0:
                                adjust_art[ENABLE_TURN] = enable_turn
                            self.apply_art(adjust_art)
                            break
        
        # 调整MP
        if not triggered:
            reg = re.match("^([\+\-\=])([\S]+)(?:MP|mp)", match_arg)
            if reg is not None:
                mp_trigger_type = reg.group(1)
                mp_value = int(function_kit.trans_str_to_float(reg.group(2), 0) * 10)
                if mp_value > 0 and mp_trigger_type != "=":
                    triggered = True
                    if mp_trigger_type == "+":
                        self.current_mp += mp_value
                    elif mp_trigger_type == "-":
                        self.current_mp -= mp_value
                if mp_trigger_type == "=":
                    triggered = True
                    self.current_mp = mp_value
            if triggered:
                self.current_mp = function_kit.get_value_in_between(self.current_mp, 0, MAX_MP)

        # 添加概率状态
        if not triggered:
            probability = 1000
            for verb_code, art_dict in ADJUST_PROBABILITY_TABLE.items():
                if triggered:
                    break
                target_arg = ""
                reg_percent = re.match("^(?:\+){0,1}([\S]+)%([\S]+)", match_arg)
                if reg_percent is not None:
                    percent_str = reg_percent.group(1)
                    curr_pb = int(function_kit.trans_str_to_float(percent_str, 0) * 10)
                    if curr_pb > 0:
                        probability = curr_pb
                        target_arg = reg_percent.group(2)
                
                if len(target_arg) == 0:
                    reg_guarantee = re.match("^必定([\S]+)", match_arg)
                    if reg_guarantee is not None:
                        target_arg = reg_guarantee.group(1)

                if len(target_arg) == 0:
                    target_arg = match_arg

                for effect_code, detail in art_dict.items():
                    search_arg_list = detail[0]
                    if target_arg not in search_arg_list:
                        continue
                    triggered = True
                    origin_art = copy.deepcopy(detail[1])
                    origin_art["verbCode"] = verb_code
                    origin_art["effectCode"] = effect_code
                    origin_art["targetId"] = "SELF"
                    origin_art["probability"] = probability
                    if enable_turn > 0:
                        origin_art[ENABLE_TURN] = enable_turn
                    self.apply_art(origin_art)
                    break

        return triggered

    def apply_art(self, origin_art: Dict) -> bool:
        '''
        根据art类型，适用效果。
        返回是否应该移除该art（记忆中避免重复适用）
        '''
        art = copy.deepcopy(origin_art)

        result = False
        verb_code = function_kit.get_v_from_d(art, "verbCode")
        effect_code = function_kit.get_v_from_d(art, "effectCode")
        effect_value = function_kit.get_v_from_d(art, "effectValue", 0)
        if verb_code == "BUFF":
            self.buff_list.append(art)
        elif verb_code == "BUFF_DYING":
            self.buff_dying_list.append(art)
        elif verb_code == "BUFF_HPMAX":
            self.buff_hpmax_list.append(art)
        # TODO BUFF_PARTY_DIE
        elif verb_code == "CONDITION_BAD":
            self.condition_goods_list.append(art)
        elif verb_code == "CONDITION_GOOD":
            self.condition_goods_list.append(art)
        # TODO DAMAGE
        elif verb_code == "DEBUFF":
            self.debuff_list.append(art)
        # TODO DRAW
        elif verb_code == "ENCHANT":
            self.enchant_list.append(art)
        elif verb_code == "HEAL":
            effect_code = function_kit.get_v_from_d(art, "effectCode")
            effect_value = function_kit.get_v_from_d(art, "effectValue", 0)
            if effect_code == "HP":
                effect_value = math.floor(effect_value * self.hp / 1000)
                self.hp_heal(effect_value)
            elif effect_code == "MP":
                if not self.find_condition_bad([BAN_HEAL_MP]):
                    effect_value = math.floor(effect_value * self.get_mp_stat() / 1000)
                    self.inc_mp(effect_value)
            elif effect_code == "MP_DAMAGE":
                self.dec_mp(effect_value)
        elif verb_code == "IGNORE":
            self.ignore_list.append(art)
        # 初始MP直接添加
        elif verb_code == "INITIAL" and effect_code == "MP":
            result = True
            self.current_mp += MAX_MP * effect_value // 1000
        # TODO LIMITED_ENEMY_TYPE
        # TODO RESURRECT
        # TODO REVOKE
        else:
            print("无法添加的art:" + json.dumps(art))
        
        self.art_list_to_effect()
        return result

    def load_memoria(self, memo: Memoria, is_mlb=True, level=-1):
        '''
        根据记忆给角色添加数值和效果
        '''
        # TODO 根据等级获取记忆数值
        self.hp += memo.max_hp
        self.atk += memo.max_atk
        self.defense += memo.max_def

        skill = memo.to_skill_format(is_mlb)
        self.memoria_list.append(skill)
        pass

    def load_art_from_memoria(self):
        '''
        将单元中的memo_list装配到buff、condition等列表中
        '''
        for memo_idx in range(len(self.memoria_list)-1, -1, -1):
            memo = self.memoria_list[memo_idx]
            # startup型技能直接添加效果
            if memo.effect_type == "STARTUP":
                self.memoria_list.pop(memo_idx)
                for art in memo.art_list:
                    self.apply_art(art)
            if memo.effect_type == "ABILITY":
                should_pop = False
                for art in memo.art_list:
                    # 无法被移除的flag
                    art[ORIGINAL_FLAG] = 1
                    should_pop |= self.apply_art(art)
                if should_pop:
                    self.memoria_list.pop(memo_idx)
    
    def art_list_to_effect(self):
        '''
        根据角色身上的状态，计算数值
        '''
        self.__reset_stat()

        calu_buff_list = self.buff_list
        if self.current_hp >= self.hp:
            calu_buff_list.extend(self.buff_hpmax_list)
        elif self.current_hp <= self.hp // 5:
            calu_buff_list.extend(self.buff_dying_list)
    
        for art in calu_buff_list:
            effect_code = function_kit.get_v_from_d(art, "effectCode")
            effect_value = function_kit.get_v_from_d(art, "effectValue", 0)
            if effect_code == "ACCEL":
                self.accele_mp_stat += effect_value
            elif effect_code == "ATTACK":
                self.atk_stat += effect_value
            elif effect_code[0:6] == "ATTACK":
                atk_attr = function_kit.get_v_from_d(chara.ATTR_MAP, effect_code[7:])
                if atk_attr == self.attribute:
                    self.attribute_atk_stat += effect_value
            elif effect_code == "BLAST":
                self.blast_plus += effect_value
            elif effect_code == "CHARGE":
                self.charge_dmg_stat += effect_value
            elif effect_code == "CHARGING":
                self.charging_plus += effect_value
            elif effect_code == "DAMAGE":
                self.damage_buff_stat += effect_value
            elif effect_code == "DEFENSE":
                self.defense_stat += effect_value
            elif effect_code == "DOPPEL":
                self.doppel_dmg_stat += effect_value
            elif effect_code == "MAGIA":
                self.magia_dmg_stat += effect_value
            elif effect_code == "MP_GAIN":
                self.mp_stat += effect_value
            elif effect_code == "MP_GAIN_OVER100":
                self.mp_over100_plus += effect_value
            elif effect_code == "RESIST":
                self.resist_plus += effect_value
        
        for art in self.debuff_list:
            effect_code = function_kit.get_v_from_d(art, "effectCode")
            effect_value = function_kit.get_v_from_d(art, "effectValue", 0)
            if effect_code == "ACCEL":
                self.accele_mp_stat -= effect_value
            elif effect_code == "ATTACK":
                self.atk_stat -= effect_value
            elif effect_code == "BLAST":
                self.blast_plus -= effect_value
            elif effect_code == "DAMAGE":
                self.damage_buff_stat -= effect_value
            elif effect_code == "DEFENSE":
                self.defense_stat -= effect_value
            elif effect_code == "MAGIA":
                self.magia_dmg_stat -= effect_value
            elif effect_code == "MP_GAIN":
                self.mp_stat -= effect_value
            elif effect_code == "RESIST":
                self.resist_plus -= effect_value
            elif effect_code[0:4] == "WEAK":
                self.attribute_weak_stat.append(art)
    
        for art in self.condition_goods_list:
            effect_code = function_kit.get_v_from_d(art, "effectCode")
            effect_value = function_kit.get_v_from_d(art, "effectValue", 0)
            if effect_code == "AUTO_HEAL":
                generic_value = function_kit.get_v_from_d(art, "genericValue")
                if generic_value == "MP":
                    self.mp_regen_num += effect_value
                else:
                    self.hp_regen_stat += effect_value
            elif effect_code == "AVOID":
                self.avoid_stat = max(self.avoid_stat, effect_value)
            elif effect_code == "C_COMBO_PLUS":
                self.c_combo_plus_stat += effect_value
            elif effect_code == "COUNTER":
                self.counter_art_list.append(art)
            elif effect_code == "CRITICAL":
                self.critical_stat = max(self.critical_stat, effect_value)
            elif effect_code == "DAMAGE_DOWN":
                self.damage_cut_stat += effect_value
            elif effect_code[0:11] == "DAMAGE_DOWN":
                self.damage_cut_special_stat.append(art)
            elif effect_code == "DAMAGE_UP":
                self.damage_good_plus += effect_value
            elif effect_code == "DAMAGE_UP_BAD":
                self.damage_bad_plus += effect_value
            elif effect_code == "DEFENSE_IGNORED":
                self.ignore_def_art_list.append(art)
            elif effect_code == "IMITATE_ATTRIBUTE":
                self.variable_stat = 1
            elif effect_code == "MP_PLUS_BLAST":
                self.mp_blast_num += effect_value
            elif effect_code == "MP_PLUS_DAMAGED":
                self.mp_hit_num += effect_value
            elif effect_code == "MP_PLUS_WEAKED":
                self.mp_hit_weak_num += effect_value
            elif effect_code == "NO_COST_CHARGE":
                self.no_c_cost_stat = 1
            elif effect_code == "PROTECT":
                self.protect_art_list.append(art)
            elif effect_code == "PROVOKE":
                self.provoke_art_list.append(art)
            elif effect_code == "PURSUE":
                self.chase_art_list.append(art)
            elif effect_code == "SKILL_QUICK":
                self.skill_quict_art_list.append(art)
            
        self.__resize_stat()

    def inc_mp(self, mp: int):
        '''增加MP，同时检查上限'''
        for bad_status in self.condition_bad_list:
            if function_kit.get_v_from_d(bad_status, "effectCode") == "INVALID_HEAL_MP":
                return
        self.current_mp = min(MAX_MP, self.current_mp + mp)
    def dec_mp(self, mp: int):
        '''减少MP，同时检查下限'''
        self.current_mp = max(0, self.current_mp - mp)
    def get_mp_stat(self):
        '''获取MP倍率，主要判断是否超过100'''
        if self.current_mp >= 1000:
            return self.mp_stat + self.mp_over100_plus
        return self.mp_stat

    def hp_damage(self, damage: int, ignore_barrier=False):
        '''
        处理HP伤害，需要做屏障、忍耐、生存等判断
        '''
        # TODO
        pass
    def hp_heal(self, heal: int):
        '''
        处理HP恢复，需要判断能否回复HP
        '''
        # TODO
        pass

    def turn_end_resolve(self):
        '''回合结束时，判断自动回复、自动伤害等内容'''
        # TODO
        pass

    def turn_update(self):
        '''
        进入下一回合，更新状态适用回合。
        '''
        # 更新角色状态回合
        all_status_list = [
            self.buff_list, self.buff_hpmax_list, self.buff_dying_list,
            self.condition_goods_list, self.debuff_list, self.condition_bad_list,
            self.ignore_list, self.enchant_list]
        for status_list in all_status_list:
            for status_idx in range(len(status_list)-1, -1, -1):
                status = status_list[status_idx]
                enable_turn = function_kit.get_v_from_d(status, ENABLE_TURN, -1)
                if enable_turn > 0:
                    enable_turn -= 1
                    if enable_turn == 0:
                        status_list.pop(status_idx)
                    else:
                        status[ENABLE_TURN] = enable_turn

        # 更新完毕后重新计算状态
        self.art_list_to_effect()

    def print_mp_stat(self) -> str:
        '''
        输出角色MP状态信息
        '''
        result = "Accele MP:%.1f%%\nMP:%.1f%%+%.1f%%"%(self.accele_mp_stat / 10, self.mp_stat / 10, self.mp_over100_plus / 10)
        if self.current_mp > 0:
            result += "\n当前MP：%.1f"%(self.current_mp / 10)
        if self.mp_hit_num > 0:
            result += "\n受击MP：%.1f"%(self.mp_hit_num / 10)
        if self.mp_hit_weak_num > 0:
            result += "\n弱点受击MP：%.1f"%(self.mp_hit_num / 10)
        if self.mp_blast_num > 0:
            result += "\nBlast MP：%.1f"%(self.mp_blast_num / 10)
        if self.mp_regen_num > 0:
            result += "\nMP自动回复：%.1f"%(self.mp_regen_num / 10)
        return result
        
    def find_condition_bad(self, bad_list: List[str]=[]) -> bool:
        '''
        判断角色是否拥有某种异常状态
        '''
        for bad_str in bad_list:
            for c_bad in self.condition_bad_list:
                bad_status = function_kit.get_v_from_d(c_bad, "effectCode")
                if bad_str == bad_status:
                    return True
        return False

'''
盘状态
'''
class QuestDiscStatus:
    def __init__(self) -> None:
        self.disc = ""
        self.current_charge = 0
        self.disc_index = 0
        self.in_mirror = False
        self.loaded = False

    def load(self, disc: str, chara_list: List[QuestUnit]=[]):
        self.disc = disc
        if len(self.disc) != 3:
            self.loaded = False
            return
        self.disc_index = 0
        if self.disc.lower() == "ccc":
            self.current_charge += 2
            for c in chara_list:
                if c is not None:
                    self.current_charge += c.c_combo_plus_stat // 2000
        self.loaded = True

    def is_first_accele(self):
        return self.disc[0].lower() == "a"
    def is_accele_combo(self):
        return self.disc.lower() == "aaa"
    
    def move_to_next(self):
        self.disc_index += 1
        if self.disc_index > 2:
            self.loaded = False

'''
关卡操作
'''
class QUEST_OPERATE:
    UNKNOWN = 0
    ADJUST = 1
    CHANGE_C = 2
    ATTACK = 3
    DEFENSE = 4
    REGEN = 5
    def __init__(self, t=UNKNOWN) -> None:
        self.type = t
        self.value = None
