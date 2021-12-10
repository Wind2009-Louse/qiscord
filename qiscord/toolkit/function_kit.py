from typing import List

from qiscord.toolkit.skill_effect import Skill

def get_v_from_d(d: dict, k, default=None, need_str=False):
    if k not in d:
        return default
    res = d[k]
    if need_str and type(res) != str:
        res = str(res)
    return res

ATTR_LIST = {"FIRE": "火",
             "TIMBER" : "木",
             "WATER": "水",
             "DARK": "暗",
             "LIGHT": "光",
             "VOID": "无"}
BAD_LIST = {"POISON" : "毒",
            "BURN" : "烧伤",
            "CURSE" : "诅咒",
            "CHARM" : "魅惑",
            "STUN" : "眩晕",
            "RESTRAINT" : "拘束",
            "FOG" : "雾",
            "DARKNESS" : "黑暗",
            "BLINDNESS" : "幻惑",
            "BAN_SKILL" : "技能封印",
            "BAN_MAGIA" : "Magia封印",
            "INVALID_HEAL_HP" : "HP回复禁止",
            "INVALID_HEAL_MP" : "MP回复禁止",
            "DAMAGE_UP_BAD_NUM" : "虚弱",
            "DEBUFF" : "DEBUFF",
            "CONDITION_BAD": "异常状态"}
GOOD_LIST = {"AUTO_HEAL" : "自动回复",
             "AVOID" : "回避",
             "COUNTER" : "反击",
             "CRITICAL" : "暴击",
             "DAMAGE_DOWN" : "伤害削减",
             "DAMAGE_DOWN_NODISK" : "Magia伤害削减",
             "DAMAGE_DOWN_ACCEL" : "Accele伤害削减",
             "DAMAGE_DOWN_BLAST" : "Blast伤害削减",
             "DAMAGE_DOWN_CHARGE" : "Charge后伤害削减",
             "DAMAGE_DOWN_CHARGING" : "Charge盘伤害削减",
             "DAMAGE_DOWN_DARK" : "暗属性伤害削减",
             "DAMAGE_DOWN_LIGHT" : "光属性伤害削减",
             "DAMAGE_DOWN_WATER" : "水属性伤害削减",
             "DAMAGE_DOWN_FIRE" : "火属性伤害削减",
             "DAMAGE_DOWN_TIMBER" : "木属性伤害削减",
             "DAMAGE_DOWN_VOID" : "无属性伤害削减",
             "DAMAGE_UP" : "伤害上升",
             "DAMAGE_UP_BAD" : "敌方状态异常时伤害UP",
             "DEFENSE_IGNORED" : "防御无视",
             "MP_PLUS_WEAKED" : "被弱点属性攻击时MPUP",
             "MP_PLUS_DAMAGED" : "被攻击时MPUP",
             "PROTECT" : "保护",
             "PROVOKE" : "挑衅",
             "PURSUE" : "追击",
             "SKILL_QUICK" : "技能冷却加速",
             "GUTS" : "忍耐",
             "SURVIVE" : "Survive",
             "MP_PLUS_BLAST" : "Blast攻击时获得MP",
             "IMITATE_ATTRIBUTE" : "Variable",
             "NO_COST_CHARGE" : "Charge无消耗",
             "C_COMBO_PLUS": "Charge Combo时C计数+",
             "BARRIER" : "屏障"}
CHANCE_GOOD_LIST = ["AVOID","COUNTER","CRITICAL","DAMAGE_DOWN","DAMAGE_UP",
                    "DEFENSE_IGNORED","PROVOKE","PROTECT","PURSUE","INVALID_HEAL_HP",
                    "SKILL_QUICK"]
WORDS_TRANS = {"ATTACK" : "攻击力",
               "DEF" : "防御力",
               "DEFENSE" : "防御力",
               "MP_GAIN" : "MP获得量",
               "MP_GAIN_OVER100" : "MP100以上时MP获得量",
               "RESIST" : "异常状态耐性",
               "ACCEL" : "Accele MP",
               "BLAST" : "Blast伤害",
               "CHARGE" : "Charge后伤害",
               "CHARGING" : "Charge盘伤害",
               "MAGIA" : "Magia伤害",
               "DOPPEL" : "Doppel",
               "DAMAGE" : "造成伤害",
               "WEAK_BLAST" : "Blast伤害",
               "WEAK_CHARGE_DONE" : "Charge后伤害",
               "WEAK_FIRE" : "火属性伤害",
               "WEAK_WATER" : "水属性伤害",
               "WEAK_TIMBER" : "木属性伤害",
               "WEAK_DARK" : "暗属性伤害",
               "WEAK_LIGHT" : "光属性伤害",
               "ATTACK_FIRE" : "火属性攻击力",
               "ATTACK_TIMBER" : "木属性攻击力",
               "ATTACK_WATER" : "水属性攻击力",
               "ATTACK_LIGHT" : "光属性攻击力",
               "ATTACK_DARK" : "暗属性攻击力"}
REVOKE_TYPES = {"BUFF" : "Buff解除",
                "DEBUFF" : "Debuff解除",
                "BAD" : "状态异常解除",
                "GOOD" : "赋予效果解除"}
CODE_MAP = {"BUFF" : "%sUP",
            "BUFF_DYING" : "濒死时%sUP",
            "BUFF_HPMAX" : "HP最大时%sUP",
            "BUFF_PARTY_DIE" : "同伴死亡时%sUP",
            "BUFF_DIE" : "死亡时同伴%sUP",
            "DRAW": "重抽%s"}
DISC_TYPE = {
    "AGAIN": "再次重抽",
    "ALIGNMENT": "重抽同属性",
    "CHARACTER": "重抽自身",
    "ACCEL": "重抽Accele盘",
    "BLAST": "重抽Blast盘",
    "CHARGE": "重抽Charge盘",
}
TYPE_WILL_ON_ENEMY = {"CONDITION_BAD","DEBUFF"}
LIMIT_TARGET = {"WITCH":"魔女","RUMOR":"谣","HUMAN":"魔法少女","EMOTION":"心魔"}

def art_to_str(this_art):
    '''将art转换为字符串'''
    this_mem_str = ""
    if this_art["verbCode"] == "ENCHANT":
        sub_state = BAD_LIST[this_art["effectCode"]]
        if this_art["probability"] < 1000:
            this_mem_str += '攻击时概率(%.1f%%)赋予%s(%dT)状态' % (this_art["probability"] / 10 ,sub_state, this_art["enableTurn"])
        elif this_art["probability"] == 1000:
            this_mem_str += "攻击时必定赋予%s(%dT)状态" % (sub_state, this_art["enableTurn"])
        elif this_art["probability"] > 1000:
            this_mem_str += '攻击时必定(%.1f%%)赋予%s(%dT)状态' % (this_art["probability"] / 10 ,sub_state, this_art["enableTurn"])
    elif this_art["verbCode"] == "CONDITION_GOOD":
        this_mem_str += rate_append(this_art["effectCode"], this_art["probability"])
        this_art_str = GOOD_LIST[this_art["effectCode"]]
        effect_not_used = True
        if this_art_str == "反击" and this_art["effectValue"] > 800:
            this_art_str = '交叉反击(%.1f%%)'%(this_art["effectValue"] / 10)
        elif this_art_str == "自动回复":
            if "genericValue" in this_art.keys() and this_art["genericValue"] == "MP":
                this_art_str = "MP自动回复"
                this_art_str = "%s(%d)" % (this_art_str, this_art["effectValue"] / 10)
            else:
                this_art_str = "HP自动回复"
                this_art_str = "%s(%d%%)" % (this_art_str, this_art["effectValue"] / 10)
        elif this_art_str == "保护" and this_art["targetId"] == "DYING":
            this_art_str = "保护濒死的同伴"
        elif this_art_str == "Survive":
            this_art_str = 'Survive(%.1f%%)'%(this_art["effectValue"] / 10)
        elif this_art_str == "屏障":
            this_art_str = '屏障(%d)'%(this_art["effectValue"])
        elif this_art_str == "Charge Combo时C计数+":
            this_art_str = 'Charge Combo时C计数+%d'%(this_art["effectValue"] / 1000)
        else:
            effect_not_used = False
        if this_art_str == "保护" and "param" in this_art.keys():
            this_art_str += "(必定保护特定角色)"
        if not effect_not_used and "effectValue" in this_art:
            this_mem_str += '%s(%.1f%%)' % (this_art_str, this_art["effectValue"] / 10)
        else:
            this_mem_str += this_art_str
    elif this_art["verbCode"] == "CONDITION_BAD":
        this_mem_str += rate_append(this_art["effectCode"], this_art["probability"])
        this_art_str = BAD_LIST[this_art["effectCode"]]
        if this_art_str == "毒" and this_art["effectValue"] > 100:
            this_art_str = "强化毒"
        if this_art_str == "诅咒" and this_art["effectValue"] > 200:
            this_art_str = "强化诅咒"
        if "effectValue" in this_art:
            this_mem_str += '%s(%.1f%%)' % (this_art_str, this_art["effectValue"] / 10)
        else:
            this_mem_str += this_art_str
    elif this_art["verbCode"] == "IGNORE":
        this_mem_str += rate_append(this_art["effectCode"], this_art["probability"])
        if this_art["effectCode"] in GOOD_LIST.keys():
            this_mem_str += "%s无效" % (GOOD_LIST[this_art["effectCode"]])
        elif this_art["effectCode"] in BAD_LIST.keys():
            this_mem_str += "%s无效" % (BAD_LIST[this_art["effectCode"]])
        else:
            print("CODE IGNORE新SUB:%s" % this_art["effectCode"])
    elif this_art["verbCode"] == "HEAL":
        if this_art["effectCode"] == "HP":
            this_mem_str += "HP回复"
        elif this_art["effectCode"] == "MP_DAMAGE":
            this_mem_str += "MP伤害"
        elif this_art["effectCode"] == "MP":
            this_mem_str += "MP回复"
        else:
            print("HEAL新sub:", this_art["effectCode"])
    elif this_art["verbCode"] == "REVOKE":
        if this_art["effectCode"] in REVOKE_TYPES.keys():
            this_mem_str += REVOKE_TYPES[this_art["effectCode"]]
        else:
            print("REVOKE新sub: ",this_art["effectCode"])
    elif this_art["verbCode"] == "LIMITED_ENEMY_TYPE":
        target_name = LIMIT_TARGET[this_art["genericValue"]]
        if "effectValue" in this_art:
            this_mem_str += '对%s%s(%.1f%%)' % (target_name, GOOD_LIST[this_art["effectCode"]],this_art["effectValue"] / 10)
        else:
            this_mem_str += "对%s%s" % (target_name,GOOD_LIST[this_art["effectCode"]])
    elif this_art["verbCode"] == "DEBUFF":
        if "effectValue" in this_art:
            if "WEAK" in this_art["effectCode"]:
                this_mem_str += '%s耐性DOWN(%.1f%%)' % (WORDS_TRANS[this_art["effectCode"]], this_art["effectValue"] / 10)
            else:
                this_mem_str += '%sDOWN(%.1f%%)' % (WORDS_TRANS[this_art["effectCode"]], this_art["effectValue"] / 10)
        else:
            this_mem_str += "%sDOWN" % (WORDS_TRANS[this_art["effectCode"]])
    elif this_art["verbCode"] == "INITIAL" and this_art["effectCode"] == "MP":
        this_mem_str += "初始%dMP" % (this_art["effectValue"] / 10)
    elif this_art["verbCode"] == "RESURRECT":
        this_mem_str += "苏生"
    elif this_art["verbCode"] == "DRAW":
        this_mem_str += DISC_TYPE[this_art["effectCode"]]
    elif this_art["verbCode"] == "ATTACK":
        sub_str = ""
        if "effectCode" in this_art:
            if this_art["effectCode"] == "DAMAGE_UP_BADS":
                sub_str += "异常增伤"
            elif this_art["effectCode"] == "LINKED_DAMAGE":
                sub_str += "低HP威力UP"
            elif this_art["effectCode"] == "ALIGNMENT":
                sub_str += "属性强化"
            elif this_art["effectCode"] == "DUMMY":
                return "DUMMY"
        if this_art["targetId"] == "TARGET":
            this_mem_str += "对敌方单体%s伤害"%sub_str
        elif this_art["targetId"] == "ALL":
            this_mem_str += "对敌方全体%s伤害"%sub_str
        elif this_art["targetId"][0:6] == "RANDOM":
            this_mem_str += "随机%s次 %s伤害"%(this_art["targetId"][-1],sub_str)
        elif this_art["targetId"] == "HORIZONTAL":
            this_mem_str += "横方向%s伤害"%sub_str
        elif this_art["targetId"] == "VERTICAL":
            this_mem_str += "纵方向%s伤害"%sub_str
        else:
            print("新攻击：%s",str(this_art))
        if "effectValue" in this_art:
            this_mem_str = '%s(%.1f%%)'%(this_mem_str, this_art["effectValue"] / 10)
    else:
        if this_art["verbCode"] in CODE_MAP:
            temp_str = CODE_MAP[this_art["verbCode"]]
            if "effectValue" in this_art:
                temp_str = temp_str + "(%.1f%%)"
                this_mem_str += temp_str % (WORDS_TRANS[this_art["effectCode"]], this_art["effectValue"] / 10)
            else:
                this_mem_str += temp_str % (WORDS_TRANS[this_art["effectCode"]])
        else:
            print("ART新CODE:", this_art["verbCode"])
    return this_mem_str

def rate_append(type,rate):
    if type in CHANCE_GOOD_LIST or type in BAD_LIST.keys():
        if rate > 1000:
            return '必定(%.1f%%)'%(rate/10)
        elif rate == 1000:
            return "必定"
        else:
            return '概率(%.1f%%)'%(rate/10)
    else:
        return ""

def range_to_str(this_art):
    result_str = ""
    # Magia无范围
    if this_art["verbCode"] == "ATTACK":
        return ""
    if this_art["targetId"] == "SELF":
        if this_art["verbCode"] == "HEAL":
            # 如 (自/10%)
            if this_art["effectCode"] == "MP" or this_art["effectCode"] == "MP_DAMAGE":
                result_str += "(自/%d)" % (this_art["effectValue"]/10)
            else:
                result_str += "(自/%d%%)" % (this_art["effectValue"]/10)
        elif "enableTurn" in this_art.keys():
            # 如 (自/3T)
            result_str += "(自/%dT)" % (this_art["enableTurn"])
        else:
            result_str += "(自)"
    else:
        temp_str = ""
        # 敌单 敌全 单 全
        if (this_art["verbCode"] == "REVOKE" and (this_art["effectCode"] == "BUFF" or this_art["effectCode"] == "GOOD")) \
            or this_art["verbCode"] in TYPE_WILL_ON_ENEMY \
            or (this_art["verbCode"] == "HEAL" and this_art["effectCode"] == "MP_DAMAGE"):
            temp_str += "敌"

        if this_art["targetId"] == "ALL":
            temp_str += "全"
        elif this_art["targetId"] == "ONE" or this_art["targetId"] == "targetId":
            temp_str += "单"
        elif this_art["targetId"] == "CONNECT":
            temp_str = ""
        elif this_art["targetId"] == "LIMITED":
            temp_str = "限定对象"

        temp_str_add = temp_str
        if len(temp_str) > 0:
            temp_str_add += "/"

        if "enableTurn" in this_art.keys():
            # 如 (敌单/1T)
            result_str += "(%s%dT)" % (temp_str_add, this_art["enableTurn"])
        elif this_art["verbCode"] == "HEAL":
            # 如 (全/30%)
            if this_art["effectCode"] == "MP" or this_art["effectCode"] == "MP_DAMAGE":
                result_str += "(%s%d)" % (temp_str_add,this_art["effectValue"]/10)
            else:
                result_str += "(%s%d%%)" % (temp_str_add,this_art["effectValue"]/10)
        elif this_art["verbCode"] == "RESURRECT":
            result_str += "(%s%d%%)" % (temp_str_add,this_art["effectValue"]/10)
        elif len(temp_str) > 0:
            # 如 (敌全)
            result_str += "(%s)" % temp_str
    return result_str

def artlist_to_str(art_list: List[dict]):
    '''
    将效果列表输出为文字
    '''
    result = ""
    for art_id in range(len(art_list)):
        if art_id > 0:
            result += "&"
        this_art = art_list[art_id]
        result += art_to_str(this_art)
        # 判断是否需要输出效果范围(和下一个效果相同则不输出)
        this_range = range_to_str(this_art)
        if (art_id != len(art_list)-1):
            next_range = range_to_str(art_list[art_id+1])
        else:
            next_range = ""
        if this_range != next_range:
            result += this_range
    return result

def skill_to_str(skill: Skill):
    '''
    输出Skill的描述
    '''
    art_str = artlist_to_str(skill.art_list)
    if skill.turn > 0:
        art_str += "[%dT]"%skill.turn
    if skill.effect_type == "STARTUP":
        art_str = "战斗开始时获得" + art_str
    if skill.effect_range == "QUEST":
        art_str = "【仅Quest】" + art_str
    return art_str

def get_artlist_from_skill(skill_dict : dict) -> List[dict]:
    '''
    从各种skill中获取art_list
    '''
    result = []
    for art_idx in range(1, 100):
        art = get_v_from_d(skill_dict, "art%d"%art_idx)
        if art is not None:
            result.append(art)
    
    return result