import re
import traceback
from typing import List, Tuple
from qiscord.toolkit import function_kit
from qiscord.toolkit.chara import Chara

class CharaPrintFilter:
    def __init__(self, filters: List[str]=[]):
        self.print_enhance_skill = False
        self.print_ex_skill = False
        self.print_translate = False
        self.rank_list = []

        self.print_card_all = True
        self.print_connect = False
        self.print_magia = False
        self.print_doppel = False
        self.print_cardinfo = False

        for filter in filters:
            if filter.find("强化") != -1 or filter in ["A", "S", "a", "s"]:
                self.print_enhance_skill = True
            if filter.find("ex") != -1 or filter.find("Ex") != -1 or filter.find("EX") != -1:
                self.print_ex_skill = True
            if filter.find("翻译") != -1:
                self.print_translate = True
            if filter in ["connect", "Connect", "CONNECT", "连携", "C", "c"]:
                self.print_card_all = False
                self.print_connect = True
            if filter in ["magia", "Magia", "MAGIA", "大招", "M", "m"]:
                self.print_card_all = False
                self.print_magia = True
            if (filter.find("魔女") != -1) or (filter in ["doppel", "Doppel", "DOPPEL", "d", "D"]):
                self.print_card_all = False
                self.print_doppel = True
            if filter.find("数") != -1:
                self.print_card_all = False
                self.print_cardinfo = True
            level_regex = re.search("(\d)星*", filter)
            if level_regex is not None:
                self.rank_list.append(int(level_regex.group(1)))

def print_chara(chara:Chara, filter: CharaPrintFilter) -> str:
    '''
    显示角色详细资料
    '''
    try:
        result = "%s: %s"%(chara.id, chara.name)
        if chara.zh_name is not None:
            result += "(%s)"%chara.zh_name
        
        result += "\n"
        for t in range(0, chara.min_rank):
            result += "★"
        for t in range(0, chara.max_rank - chara.min_rank):
            result += "☆"
        result += " %s/%s"%(chara.attribute, chara.chara_type)
        result += " " + "".join(chara.disc)
        result += " MP效率：%d%%/%d%%"%(chara.attack_mp_rate / 10, chara.def_mp_rate / 10)

        if filter.print_translate:
            result += "\nConnect: %s"%chara.connect_name
            if chara.connect_zhname is not None:
                result += "(%s)"%chara.connect_zhname
            
            result += "\nMagia: %s"%chara.magia_name
            if chara.magia_zhname is not None:
                result += "(%s)"%chara.magia_zhname
            
            result += "\nDoppel: %s"%chara.doppel_name
            if chara.doppel_zhname is not None:
                result += "(%s)"%chara.doppel_zhname
        
        if filter.print_ex_skill:
            if len(chara.ex_nmlb_skill.art_list) > 0:
                result += "\nEx技能1：" + function_kit.skill_to_str(chara.ex_nmlb_skill)
            if len(chara.ex_mlb_skill.art_list) > 0:
                result += "\nEx技能2：" + function_kit.skill_to_str(chara.ex_mlb_skill)

        if filter.print_enhance_skill:
            result += "\n精神强化效果："
            if len(chara.enhance_skill_list) == 0:
                result += "无"
            else:
                for skill in chara.enhance_skill_list:
                    result += "\n* " + function_kit.skill_to_str(skill)
        
        result += __print_chara_card(chara, filter)

        return result
    except Exception as e:
        traceback.print_exc()
        return str(e.args[0])

def __print_chara_card(chara:Chara, filter: CharaPrintFilter) -> str:
    if len(filter.rank_list) == 0:
        if filter.print_card_all:
            return ""
        else:
            filter.rank_list.append(chara.card_list[-1].rank)
    
    result = ""
    for card in chara.card_list:
        if card.rank in filter.rank_list:
            result += "\n\n%d星："%card.rank
            if filter.print_card_all or filter.print_cardinfo:
                result += "\nHP:%d/%s"%(card.min_hp, __calculate_final_hpatkdef(card.max_hp, chara.enhance_hp, card.awaken_hp_percent)[0])
                result += "\nATK:%d/%s"%(card.min_atk, __calculate_final_hpatkdef(card.max_atk, chara.enhance_atk, card.awaken_atk_percent)[0])
                result += "\nDEF:%d/%s"%(card.min_def, __calculate_final_hpatkdef(card.max_def, chara.enhance_def, card.awaken_def_percent)[0])
                result += "\nAccele:" + __calculate_final_abc(card.awaken_accele_percent, chara.enhance_accele)[0]
                result += "\nBlast:" + __calculate_final_abc(card.awaken_blast_percent, chara.enhance_blast)[0]
                result += "\nCharge:" + __calculate_final_abc(card.awaken_charge_percent, chara.enhance_charge)[0]
            if filter.print_card_all or filter.print_connect:
                result += "\nConnect效果：" + function_kit.artlist_to_str(card.connect_artlist)
            if filter.print_card_all or filter.print_magia:
                result += "\nMagia效果：" + function_kit.artlist_to_str(card.magia_artlist)
            if filter.print_card_all or filter.print_doppel:
                if len(card.random_doppel_list) > 0:
                    result += "\nDoppel效果："
                    for random_d in card.random_doppel_list:
                        result += "\n" + random_d.get_cent() + function_kit.artlist_to_str(random_d.art_list)
                elif len(card.doppel_artlist) > 0:
                    result += "\nDoppel效果：" + function_kit.artlist_to_str(card.doppel_artlist)

    return result

def __calculate_final_hpatkdef(max_num: int, enhance_num: int, percent: int) -> Tuple[str, int, int]:
    '''
    根据觉醒、强化计算HP/ATK/DEF的理想值和完美值
    '''
    ideal_num = max_num
    total_num = max_num
    if percent > 0:
        total_num = max_num * (1 + percent / 1000)
        ideal_num = max_num * (1 + percent / 1000)
        if enhance_num > 0:
            ideal_num = total_num + enhance_num * 0.6
            total_num = total_num + enhance_num
    return ("%d/%d/%d"%(max_num, ideal_num, total_num), ideal_num, total_num)

def __calculate_final_abc(card_abc: int, enhance_abc: int) -> Tuple[str, int]:
    '''
    根据觉醒、强化计算Accele/Blast/Charge增幅
    '''
    abc_num = card_abc + enhance_abc
    result = "%d%%"%(card_abc / 10)
    if enhance_abc > 0:
        result += "+%d%%=%d%%"%(enhance_abc / 10, abc_num / 10)
    return (result, abc_num)

def print_chara_thumb(chara:Chara) -> str:
    '''
    显示角色缩略资料
    '''
    result = "[%d/%d-%s]%s"%(chara.min_rank, chara.max_rank, chara.attribute, chara.name)
    if chara.zh_name is not None:
        result += "(%s)"%chara.zh_name
    return result
