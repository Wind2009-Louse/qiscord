import traceback
import json
import threading
import requests
import re
import math
from urllib.parse import quote
from typing import Dict, List, Set
from qiscord.decorator import singleton
from qiscord.toolkit import function_kit, skill_effect

query_url = "https://magireco.moe/api.php?action=query&prop=revisions&rvslots=%2A&rvprop=content&formatversion=2&format=json&titles="
ATTR_MAP = {"FIRE": "火","TIMBER" : "木","WATER": "水","DARK": "暗","LIGHT": "光","VOID": "无"}
CHARA_TYPE_MAP = {"ATTACK": "攻击", "DEFENSE": "防御", "MAGIA": "Magia", "SUPPORT": "辅助", "BALANCE": "均衡", "HEAL": "治疗", "ULTIMATE": "究极", "EXCEED": "超越", "ARUTEMETTO": "究极"}
DISC_MAP = {"MPUP": "A", "RANGE_H": "B↔", "RANGE_V": "B↕", "CHARGE": "C", "RANGE_S": "B╱", "RANGE_B": "B╲"}

GROW_BASE_MAP = {"BALANCE": (1,1,1), "ATTACK": (0.98, 1.03, 0.97), "DEFENSE": (0.97, 0.98, 1.05), "HP": (1.04, 0.97, 0.98), "ATKDEF": (0.99, 1.02, 1.01), "ATKHP": (1.02, 1.01, 0.99), "DEFHP": (1.01, 0.99, 1.02)}
RANK_GROW_MAP = {"1":2,"2":2.2,"3":2.4,"4":2.6,"5":3}

CHARA_NAME_ZH = "zh_name"
CONNECT_NAME_ZH = "zh_cnname"
MAGIA_NAME_ZH = "zh_mgname"
DOPPEL_NAME_ZH = "zh_dpname"

class CharaCard:
    def __init__(self) -> None:
        self.rank = 0
        self.grow_type = "None"
        self.min_hp = 0
        self.max_hp = 0
        self.min_atk = 0
        self.max_atk = 0
        self.min_def = 0
        self.max_def = 0
        self.attack_mp_rate = 0
        self.def_mp_rate = 0
        self.disc = []

        self.awaken_hp_percent = 0
        self.awaken_atk_percent = 0
        self.awaken_def_percent = 0
        self.awaken_accele_percent = 0
        self.awaken_blast_percent = 0
        self.awaken_charge_percent = 0

        self.connect_name = None
        self.connect_zhname = None
        self.magia_name = None
        self.magia_zhname = None
        self.doppel_name = None
        self.doppel_zhname = None
        self.connect_artlist = []
        self.magia_artlist = []
        self.doppel_artlist = []

        self.ex_nmlb_artlist = []
        self.ex_mlb_artlist = []

        self.random_doppel_list: List[skill_effect.Skill] = []

class Chara:
    def __init__(self) -> None:
        self.id : str = None
        self.name : str = None
        self.zh_name : str = None
        self.min_rank = 0
        self.max_rank = 0
        self.attribute : str = None
        self.chara_type : str = None
        self.disc: List[str] = []
        
        self.attack_mp_rate : int = None
        self.def_mp_rate : int = None

        self.enhance_hp = 0
        self.enhance_atk = 0
        self.enhance_def = 0
        self.enhance_accele = 0
        self.enhance_blast = 0
        self.enhance_charge = 0
        self.enhance_skill_list: List[skill_effect.Skill] = []

        self.ex_nmlb_artlist : List[dict] = []
        self.ex_mlb_artlist : List[dict] = []

        self.connect_name : str = None
        self.connect_zhname : str = None
        self.magia_name : str = None
        self.magia_zhname : str = None
        self.doppel_name : str = None
        self.doppel_zhname : str = None

        self.card_list: List[CharaCard] = []

class CharaSearchFilter:
    def __init__(self, filters: List[str]=[]) -> None:
        self.empty_search = False
        self.origin_key_list = filters
        self.origin_key = " ".join(filters)

        self.attribute_set: Set[str] = []
        self.type_set: Set[str] = []

        self.key_list = []
        for key in filters:
            transformed = False

            # 属性
            reg_a = re.match("^([\S]+)属性", key)
            if reg_a is not None:
                self.attribute_set.append(reg_a.group(1))
                transformed = True
            elif key in ATTR_MAP.values():
                self.attribute_set.append(key)
                transformed = True
            
            # 类型
            reg_t = re.match("^([\S]+)型", key)
            if reg_t is not None:
                self.type_set.append(reg_t.group(1))
                transformed = True
            elif key in CHARA_TYPE_MAP.values():
                self.type_set.append(key)
                transformed = True
            
            # 关键字
            if not transformed:
                self.key_list.append(key)

        if len(filters) == 0:
            self.empty_search = True

@singleton
class CharaDb:
    chara_data: Dict[str, Chara]
    trans_data: dict
    alias_data: dict
    __async_thread: threading.Thread
    __json_path: str
    __trans_path: str
    __alias_path: str

    def __init__(self, json_path=None, trans_path=None, alias_path=None) -> None:
        self.chara_data = {}
        self.trans_data = {}
        self.alias_data = {}
        self.__json_path = None
        self.__trans_path = None
        self.__alias_path = None
        self.__async_thread = None
        self.reload_data(json_path, trans_path, alias_path)
    
    def reload_data(self, json_path=None, trans_path=None, alias_path=None):
        '''
        重新加载本地的数据
        '''
        if json_path is None:
            if self.__json_path is not None:
                json_path = self.__json_path
            else:
                json_path = "git_data/charaCard.json"
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                text = f.read()
                raw_data = json.loads(text)
                self.__load_chara(raw_data)
            self.__json_path = json_path
        except Exception:
            traceback.print_exc()

        if trans_path is None:
            if self.__trans_path is not None:
                trans_path = self.__trans_path
            else:
                trans_path = "bot_data/chara_trans.json"
        try:
            with open(trans_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self.trans_data = json.loads(text)
                self.__load_translate(self.trans_data)
            self.__trans_path = trans_path
        except Exception:
            traceback.print_exc()

        if alias_path is None:
            if self.__alias_path is not None:
                alias_path = self.__alias_path
            else:
                alias_path = "bot_data/chara_alias.json"
        try:
            with open(alias_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self.alias_data = json.loads(text)
            self.__alias_path = alias_path
        except Exception:
            traceback.print_exc()
        return True

    def __load_translate(self, trans_name:dict):
        for k, v in trans_name.items():
            if k in self.chara_data:
                chara = self.chara_data[k]
                zh_name = function_kit.get_v_from_d(v, CHARA_NAME_ZH)
                if zh_name is not None:
                    chara.zh_name = zh_name
                
                zh_cnname = function_kit.get_v_from_d(v, CONNECT_NAME_ZH)
                zh_mgname = function_kit.get_v_from_d(v, MAGIA_NAME_ZH)
                zh_dpname = function_kit.get_v_from_d(v, DOPPEL_NAME_ZH)

                for c in chara.card_list:
                    if zh_cnname is not None and c.connect_name is not None:
                        c.connect_zhname = zh_cnname
                        chara.connect_zhname = zh_cnname
                    if zh_mgname is not None and c.magia_name is not None:
                        c.magia_zhname = zh_mgname
                        chara.magia_zhname = zh_mgname
                    if zh_dpname is not None and c.doppel_name is not None:
                        c.doppel_zhname = zh_dpname
                        chara.doppel_zhname = zh_dpname

    def __load_chara(self, raw_data: dict) -> None:
        '''
        加载角色数据
        '''
        temp_data = {}
        for k, d in raw_data.items():
            current_chara = Chara()
            current_chara.min_rank = 0
            current_chara.max_rank = 0
            current_chara.id  = k
            current_chara.name = function_kit.get_v_from_d(d, "name", "")
            title = function_kit.get_v_from_d(d, "title")
            if title is not None:
                current_chara.name += "（%s）"%title

            # 属性/类型
            origin_attribute = function_kit.get_v_from_d(d, "attributeId", "")
            current_chara.attribute = function_kit.get_v_from_d(ATTR_MAP, origin_attribute, default=origin_attribute)
            origin_type = function_kit.get_v_from_d(d, "initialType", "")
            current_chara.chara_type = function_kit.get_v_from_d(CHARA_TYPE_MAP, origin_type, default=origin_type)

            # 卡面数据
            # 默认卡面
            current_chara.card_list = []
            default_card_dict = function_kit.get_v_from_d(d, "defaultCard")
            if default_card_dict is None:
                continue
            default_card = self.__load_chara_card(default_card_dict)
            current_chara.min_rank = default_card.rank
            current_chara.max_rank = default_card.rank
            current_chara.disc = default_card.disc
            current_chara.attack_mp_rate = default_card.attack_mp_rate
            current_chara.def_mp_rate = default_card.def_mp_rate
            current_chara.card_list.append(default_card)

            # 升阶卡面
            for id in range(1, 10):
                card_id_key = "evolutionCard%d"%id
                if card_id_key not in d:
                    break
                evo_card = self.__load_chara_card(d[card_id_key])
                current_chara.max_rank = max(evo_card.rank, current_chara.max_rank)
                current_chara.card_list.append(evo_card)
            # 根据最后一张卡，拿connect/magia/doppel/EX技能数据
            last_card = current_chara.card_list[-1]
            current_chara.connect_name = last_card.connect_name
            current_chara.magia_name = last_card.magia_name
            current_chara.doppel_name = last_card.doppel_name
            current_chara.ex_nmlb_artlist = last_card.ex_nmlb_artlist
            current_chara.ex_mlb_artlist = last_card.ex_mlb_artlist

            # 精神强化数据
            enhance_cell_list = function_kit.get_v_from_d(d, "enhancementCellList")
            if enhance_cell_list is not None:
                for enhance_cell in enhance_cell_list:
                    cell_type = function_kit.get_v_from_d(enhance_cell,"enhancementType")
                    cell_value = function_kit.get_v_from_d(enhance_cell,"effectValue", 0)
                    if cell_type == "HP":
                        current_chara.enhance_hp += cell_value
                    elif cell_type == "ATTACK":
                        current_chara.enhance_atk += cell_value
                    elif cell_type == "DEFENSE":
                        current_chara.enhance_def += cell_value
                    elif cell_type == "DISK_ACCELE":
                        current_chara.enhance_accele += cell_value
                    elif cell_type == "DISK_BLAST":
                        current_chara.enhance_blast += cell_value
                    elif cell_type == "DISK_CHARGE":
                        current_chara.enhance_charge += cell_value
                    elif cell_type == "SKILL":
                        enhance_skill = function_kit.get_v_from_d(enhance_cell,"emotionSkill")
                        if enhance_skill is None:
                            continue
                        current_skill = skill_effect.Skill()
                        current_skill.effect_type = function_kit.get_v_from_d(enhance_skill, "type", 0)
                        current_skill.turn = function_kit.get_v_from_d(enhance_skill, "intervalTurn", 0)
                        current_skill.effect_range = function_kit.get_v_from_d(enhance_skill, "skillEffectRange", 0)
                        art_effect_max_turn = 0
                        for art_idx in range(1, 100):
                            art_key = "art%d"%art_idx
                            if art_key not in enhance_skill:
                                break
                            current_skill.art_list.append(enhance_skill[art_key])
                            art_effect_turn = function_kit.get_v_from_d(enhance_skill[art_key], "enableTurn", 0)
                            art_effect_max_turn = max(art_effect_max_turn, art_effect_turn)
                        if art_effect_max_turn > 0 and current_skill.effect_type == "ABILITY":
                            current_skill.effect_type = "STARTUP"
                        current_chara.enhance_skill_list.append(current_skill)

            temp_data[k] = current_chara
        
        self.chara_data = temp_data
    
    def __load_chara_card(self, card_data: dict) -> CharaCard:
        '''
        加载不同稀有度的角色数据
        '''
        card = CharaCard()
        rank_str = function_kit.get_v_from_d(card_data, "rank", "RANK_0")[-1]
        card.rank = int(rank_str)
        card.disc = []
        for disc_idx in range(1, 10):
            disc_key = "commandType%d"%disc_idx
            disc = function_kit.get_v_from_d(card_data, disc_key)
            if disc is None:
                break
            card.disc.append(function_kit.get_v_from_d(DISC_MAP, disc, default=disc))

        # 计算HP、ATK、DEF
        card.grow_type = function_kit.get_v_from_d(card_data, "growthType", "")
        card.min_hp = function_kit.get_v_from_d(card_data, "hp", default=0)
        card.min_atk = function_kit.get_v_from_d(card_data, "attack", default=0)
        card.min_def = function_kit.get_v_from_d(card_data, "defense", default=0)
        grow_tuple = GROW_BASE_MAP[card.grow_type]
        card.max_hp = math.floor(card.min_hp + card.min_hp * grow_tuple[0] * function_kit.get_v_from_d(RANK_GROW_MAP, rank_str, default=0))
        card.max_atk = math.floor(card.min_atk + card.min_atk * grow_tuple[1] * function_kit.get_v_from_d(RANK_GROW_MAP, rank_str, default=0))
        card.max_def = math.floor(card.min_def + card.min_def * grow_tuple[2] * function_kit.get_v_from_d(RANK_GROW_MAP, rank_str, default=0))
        # 计算MP效率
        card.attack_mp_rate = function_kit.get_v_from_d(card_data, "rateGainMpAtk", 0)
        card.def_mp_rate = function_kit.get_v_from_d(card_data, "rateGainMpDef", 0)

        # 获取ex技能数据
        ex_data_dict = function_kit.get_v_from_d(card_data, "pieceSkillList", [])
        if len(ex_data_dict) > 0:
            card.ex_nmlb_artlist = function_kit.get_artlist_from_skill(ex_data_dict[0])
        ex_data_dict = function_kit.get_v_from_d(card_data, "maxPieceSkillList", [])
        if len(ex_data_dict) > 0:
            card.ex_mlb_artlist = function_kit.get_artlist_from_skill(ex_data_dict[0])

        # 获取觉醒数据
        awaken_data = function_kit.get_v_from_d(card_data, "cardCustomize")
        if awaken_data is not None:
            for awaken_idx in range(1, 100):
                code_key = "bonusCode%d"%awaken_idx
                num_key = "bonusNum%d"%awaken_idx
                if code_key not in awaken_data or num_key not in awaken_data:
                    continue
                if awaken_data[code_key] == "HP":
                    card.awaken_hp_percent += awaken_data[num_key]
                if awaken_data[code_key] == "ATTACK":
                    card.awaken_atk_percent += awaken_data[num_key]
                if awaken_data[code_key] == "DEFENSE":
                    card.awaken_def_percent += awaken_data[num_key]
                if awaken_data[code_key] == "ACCEL":
                    card.awaken_accele_percent += awaken_data[num_key]
                if awaken_data[code_key] == "BLAST":
                    card.awaken_blast_percent += awaken_data[num_key]
                if awaken_data[code_key] == "CHARGE":
                    card.awaken_charge_percent += awaken_data[num_key]

        # 获取Connect数据
        connect_dict = function_kit.get_v_from_d(card_data, "cardSkill")
        if connect_dict is not None:
            card.connect_name = function_kit.get_v_from_d(connect_dict, "name")
            card.connect_artlist = function_kit.get_artlist_from_skill(connect_dict)

        # 获取Magia数据
        magia_dict = function_kit.get_v_from_d(card_data, "cardMagia")
        if magia_dict is not None:
            card.magia_name = function_kit.get_v_from_d(magia_dict, "name")
            for art_idx in range(1, 100):
                magia_art = function_kit.get_v_from_d(magia_dict, "art%d"%art_idx)
                if magia_art is not None:
                    growth_point = function_kit.get_v_from_d(magia_art, "growPoint", 0)
                    if "effectValue" in magia_art:
                        magia_art["effectValue"] += growth_point * 4
                    card.magia_artlist.append(magia_art)

        # 获取Doppel数据
        doppel_dict = function_kit.get_v_from_d(card_data, "doppelCardMagia")
        if doppel_dict is not None:
            card.doppel_name = function_kit.get_v_from_d(doppel_dict, "name")
            for art_idx in range(1, 100):
                doppel_art = function_kit.get_v_from_d(doppel_dict, "art%d"%art_idx)
                if doppel_art is not None:
                    growth_point = function_kit.get_v_from_d(doppel_art, "growPoint", 0)
                    if "effectValue" in doppel_art:
                        doppel_art["effectValue"] += growth_point * 4
                    card.doppel_artlist.append(doppel_art)
        
        # 获取随机Doppel数据
        random_doppel_dict = function_kit.get_v_from_d(card_data, "randomDoppelCardMagiaMap")
        if random_doppel_dict is not None:
            random_doppel_cent_dict = function_kit.get_v_from_d(card_data, "randomDoppelMagiaMap", {})
            total_cent = 0
            for rd_id, rd_dict in random_doppel_dict.items():
                # 获取随机概率
                current_d = skill_effect.Skill()
                for cent_k, cent in random_doppel_cent_dict.items():
                    if cent_k[0:len(rd_id)] == rd_id:
                        current_d.self_cent = cent
                        total_cent += cent
                        break
                # 获取效果
                for art_idx in range(1, 100):
                    doppel_art = function_kit.get_v_from_d(rd_dict, "art%d"%art_idx)
                    if doppel_art is not None:
                        growth_point = function_kit.get_v_from_d(doppel_art, "growPoint", 0)
                        if "effectValue" in doppel_art:
                            doppel_art["effectValue"] += growth_point * 4
                        current_d.art_list.append(doppel_art)
                card.random_doppel_list.append(current_d)
            # 设置总体概率
            for d in card.random_doppel_list:
                d.total_cent = total_cent

        return card

    def search_chara(self, key_list: List[str], redirect=True) -> List[Chara]:
        '''
        根据key检索角色
        '''
        filter = CharaSearchFilter(key_list)

        result_id_list = []
        if filter.empty_search:
            return result_id_list
        
        if redirect:
            for key in filter.origin_key_list:
                if key in self.alias_data.keys():
                    alias_key = self.alias_data[key]
                    res = self.search_chara([alias_key], False)
                    if len(res) > 0:
                        return res
        
        if filter.origin_key in self.chara_data:
            return [self.chara_data[filter.origin_key]]
        
        # 从原数据中读取
        for c in self.chara_data.values():
            if filter.origin_key in [c.name, c.zh_name]:
                return [c]
            
            filter_match = True
            # 根据属性搜索
            if len(filter.attribute_set) > 0:
                if c.attribute not in filter.attribute_set:
                    filter_match = False
            # 根据类型搜索
            if len(filter.type_set) > 0:
                if c.chara_type not in filter.type_set:
                    filter_match = False
            # 根据名称搜索
            for key in filter.key_list:
                if (c.name.find(key) == -1) and (c.zh_name is None or c.zh_name.find(key) == -1):
                    filter_match = False
                    break
            if filter_match:
                result_id_list.append(c)
        
        return result_id_list
    
    def add_alias(self, m:Chara, alias:str) -> bool:
        self.alias_data[alias] = m.name
        self.__save_alias()
        return True

    def del_alias(self, alias:str) -> bool:
        if alias not in self.alias_data:
            return False
        del self.alias_data[alias]
        self.__save_alias()
        return True
    
    def __save_alias(self):
        with open(self.__alias_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.alias_data, ensure_ascii=False))

    def refresh_trans(self) -> bool:
        '''
        发起更新角色中文译名请求
        '''
        if self.__async_thread is not None:
            print("已在更新角色译名")
            return False
        try:
            self.__async_thread = threading.Thread(target=self.__async_refresh_trans)
            self.__async_thread.start()
            return True
        except Exception:
            traceback.print_exc()
            return False

    def __async_refresh_trans(self):
        '''
        更新记忆中文译名异步过程
        '''
        print("开始更新译名")
        ses = requests.Session()
        current_chara_data = self.chara_data.copy()
        for k, v in current_chara_data.items():
            chara_name = v.name
            chara_zhname = None
            cn_zhname = None
            mg_zhname = None
            dp_zhname = None
            if chara_name is not None:
                total_name = "Template:角色数据表/" + chara_name
                url = query_url + quote(total_name)
                try:
                    res = ses.get(url)
                    res_data = json.loads(res.text)
                    page_list = function_kit.get_v_from_d(function_kit.get_v_from_d(res_data, "query", default={}), "pages")
                    if page_list is not None:
                        for page in page_list:
                            if function_kit.get_v_from_d(page, "title") != total_name:
                                continue
                            for rev in function_kit.get_v_from_d(page, "revisions", default=[]):
                                content = function_kit.get_v_from_d(
                                            function_kit.get_v_from_d(
                                                function_kit.get_v_from_d(rev, "slots", default={}),
                                             "main", default={}),
                                        "content")
                                if content is None:
                                    continue
                                regex_cn = re.search("角色中文名 *= *([^\n]+?)\n", content)
                                if regex_cn is not None:
                                    chara_zhname = regex_cn.group(1).strip()
                                regex_cnn = re.search("连携中文 *= *([^\n]+?)\n", content)
                                if regex_cnn is not None:
                                    cn_zhname = regex_cnn.group(1).strip()
                                regex_mg = re.search("magia中文 *= *([^\n]+?)\n", content)
                                if regex_mg is not None:
                                    mg_zhname = regex_mg.group(1).strip()
                                regex_dp = re.search("doppel中文 *= *([^\n]+?)\n", content)
                                if regex_dp is not None:
                                    dp_zhname = regex_dp.group(1).strip()
                    if k not in self.trans_data.keys():
                        self.trans_data[k] = {}
                    if chara_zhname is not None and len(chara_zhname) > 0:
                        self.trans_data[k][CHARA_NAME_ZH] = chara_zhname
                    if cn_zhname is not None and len(cn_zhname) > 0:
                        self.trans_data[k][CONNECT_NAME_ZH] = cn_zhname
                    if mg_zhname is not None and len(mg_zhname) > 0:
                        self.trans_data[k][MAGIA_NAME_ZH] = mg_zhname
                    if dp_zhname is not None and len(dp_zhname) > 0:
                        self.trans_data[k][DOPPEL_NAME_ZH] = dp_zhname
                    print("%s="%k, self.trans_data[k])
                except Exception:
                    traceback.print_exc()
        
        print("更新角色结果：")
        print(self.trans_data)
        with open(self.__trans_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.trans_data, ensure_ascii=False))

        # 结束
        ses.close()
        self.__load_translate(self.trans_data)
        self.__async_thread = None