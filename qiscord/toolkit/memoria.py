import traceback
import json
import threading
import requests
import re
import math
from urllib.parse import quote
from typing import Dict, List, Tuple, Set
from qiscord.decorator import singleton
from qiscord.toolkit import function_kit, skill_effect

query_url = "https://magireco.moe/api.php?action=query&prop=revisions&rvslots=%2A&rvprop=content&formatversion=2&format=json&titles="
TYPE_DICT= {"SKILL": "技能型", "ABILITY": "能力型"}

class Memoria:
    def __init__(self) -> None:
        self.id : id = None
        self.name : str = None
        self.zh_name : str = None
        self.type : str = None
        self.rank : str = None

        self.owner_id: List[int] = []
        self.owner_chara: List[str] = []

        self.min_hp = 0
        self.min_atk = 0
        self.min_def = 0
        self.max_hp = 0
        self.max_atk = 0
        self.max_def = 0
        self.cd_nmlb = 0
        self.cd_mlb = 0
        self.artlist_nmlb : List[dict] = []
        self.artlist_mlb : List[dict] = []

        self.fetch_way = ""
    
    def to_skill_format(self, max=True) -> skill_effect.Skill:
        result = skill_effect.Skill()
        if max:
            result.current_turn = self.cd_mlb
            result.turn = self.cd_mlb
            result.art_list.extend(self.artlist_mlb)
        else:
            result.current_turn = self.cd_nmlb
            result.turn = self.cd_nmlb
            result.art_list.extend(self.artlist_nmlb)
        if result.current_turn > 0:
            result.effect_type = "SKILL"
        else:
            result.effect_type = "ABILITY"
        return result

class MemoriaSearchFilter:
    def __init__(self, filters: List[str]=[]) -> None:
        self.empty_search = False
        self.origin_key_list = filters
        self.origin_key = " ".join(filters)

        self.rank_set: Set[str] = []
        self.type_set: Set[str] = []
        self.key_list = []
        for key in filters:
            transformed = False

            # 等级
            reg_r = re.match("^([\d]+星)", key)
            if reg_r is not None:
                self.rank_set.append(reg_r.group(1))
                transformed = True
            reg_r2 = re.match("^([\d]+)", key)
            if reg_r2 is not None:
                self.rank_set.append(reg_r2.group(1) + "星")
                transformed = True

            # 类型
            reg_t = re.match("^([\S]+型)", key)
            if reg_t is not None:
                self.type_set.append(reg_t.group(1))
                transformed = True
            elif key in TYPE_DICT.values():
                self.type_set.append(key)
                transformed = True
            
            # 关键字
            if not transformed:
                self.key_list.append(key)
        
        if len(filters) == 0:
            self.empty_search = True

@singleton
class MemoriaDb:
    memo_data: Dict[str, Memoria]
    trans_data: dict
    alias_data: dict
    __async_thread: threading.Thread
    __json_path: str
    __trans_path: str
    __alias_path: str

    def __init__(self, json_path=None, trans_path=None, alias_path=None) -> None:
        self.alias_data = {}
        self.trans_data = {}
        self.memo_data : Dict[str, Memoria] = {}
        self.__async_thread = None
        self.__json_path = None
        self.__trans_path = None
        self.__alias_path = None
        self.reload_data(json_path, trans_path, alias_path)

    def reload_data(self, json_path=None, trans_path=None, alias_path=None):
        '''
        重新加载本地的数据
        '''
        if json_path is None:
            if self.__json_path is not None:
                json_path = self.__json_path
            else:
                json_path = "git_data/memoria.json"
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self.__load_memo(json.loads(text))
            self.__json_path = json_path
        except Exception:
            traceback.print_exc()
        
        if trans_path is None:
            if self.__trans_path is not None:
                trans_path = self.__trans_path
            else:
                trans_path = "bot_data/memo_trans.json"
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
                alias_path = "bot_data/memo_alias.json"
        try:
            with open(alias_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self.alias_data = json.loads(text)
            self.__alias_path = alias_path
        except Exception:
            traceback.print_exc()
        return True

    def __load_translate(self, trans_dict: Dict[str, dict]):
        for k, v in trans_dict.items():
            if k in self.memo_data:
                memo = self.memo_data[k]
                zh_name = function_kit.get_v_from_d(v, "zh_name")
                if zh_name is not None:
                    memo.zh_name = zh_name
                get_way = function_kit.get_v_from_d(v, "get_way")
                if get_way is not None:
                    get_way = re.sub(r"\[\[([^\|\]]+?)\]\]", r"\1", get_way)
                    get_way = re.sub(r"\[\[([^\]]+?)\|([^\]]+?)\]\]", r"\2", get_way)
                    memo.fetch_way = get_way

    def __load_memo(self, memo_dict: Dict[str, dict]):
        temp_data = {}
        for k, d in memo_dict.items():
            current_memo = Memoria()

            current_memo.id = k
            current_memo.name = function_kit.get_v_from_d(d, "pieceName")
            if current_memo.name is None:
                continue
            type_str = function_kit.get_v_from_d(d, "pieceType", "")
            current_memo.type = function_kit.get_v_from_d(TYPE_DICT, type_str, type_str)
            current_memo.rank = function_kit.get_v_from_d(d, "rank", "RANK_0")[-1] + "星"

            current_memo.min_hp = function_kit.get_v_from_d(d, "hp", 0)
            current_memo.min_atk = function_kit.get_v_from_d(d, "attack", 0)
            current_memo.min_def = function_kit.get_v_from_d(d, "defense", 0)
            current_memo.max_hp = math.floor(current_memo.min_hp * 2.5)
            current_memo.max_atk = math.floor(current_memo.min_atk * 2.5)
            current_memo.max_def = math.floor(current_memo.min_def * 2.5)

            chara_list = function_kit.get_v_from_d(d, "charaList", [])
            if len(chara_list) > 0:
                for own in chara_list:
                    current_memo.owner_id.append(function_kit.get_v_from_d(own, "charaId", 0))

            current_memo.cd_nmlb, current_memo.artlist_nmlb = self.__load_memo_skill(function_kit.get_v_from_d(d, "pieceSkill", {}))
            current_memo.cd_mlb, current_memo.artlist_mlb = self.__load_memo_skill(function_kit.get_v_from_d(d, "pieceSkill2", {}))

            temp_data[k] = current_memo
        
        self.memo_data = temp_data
    
    def __load_memo_skill(self, skill_dict: dict) -> Tuple[int, List[dict]]:
        turn = function_kit.get_v_from_d(skill_dict, "intervalTurn", 0)
        art_list = function_kit.get_artlist_from_skill(skill_dict)
        return (turn, art_list)

    def search_memoria(self, key_list: List[str], redirect=True) -> List[Memoria]:
        '''
        根据key检索记忆
        '''
        filter = MemoriaSearchFilter(key_list)
        result_id_list = []
        if filter.empty_search:
            return result_id_list
        
        if redirect:
            alias_key = function_kit.get_v_from_d(self.alias_data, filter.origin_key)
            if alias_key is not None:
                res = self.search_memoria([alias_key], False)
                if len(res) > 0:
                    return res

        if filter.origin_key in self.memo_data:
            return [self.memo_data[filter.origin_key]]
        
        # 从原数据中读取
        for m in self.memo_data.values():
            if filter.origin_key in [m.name, m.zh_name]:
                return [m]
            
            filter_match = True
            # 根据等级搜索
            if len(filter.rank_set) > 0:
                if m.rank not in filter.rank_set:
                    filter_match = False
            # 根据类型搜索
            if len(filter.type_set) > 0:
                if m.type not in filter.type_set:
                    filter_match = False
            # 根据名称搜索
            for key in filter.key_list:
                if (m.name.find(key) == -1) and (m.zh_name is None or m.zh_name.find(key) == -1) :
                    filter_match = False
                    break
            if filter_match:
                result_id_list.append(m)
        
        return result_id_list
    
    def add_alias(self, m:Memoria, alias:str) -> bool:
        m_name = m.name
        if m_name is None:
            return False
        self.alias_data[alias] = m_name
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
        发起更新记忆中文译名请求
        '''
        if self.__async_thread is not None:
            print("已在更新记忆译名")
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
        current_raw_data = self.memo_data.copy()
        for k, v in current_raw_data.items():
            m_name = v.name
            m_zhname = None
            m_way = None
            if m_name is not None:
                total_name = "Template:记忆数据表/" + m_name
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
                                regex_s = re.search("中文名 *= *([^\n]+?)\n", content)
                                if regex_s is not None:
                                    m_zhname = regex_s.group(1)
                                regex_get = re.search("入手方式 *= *([^\n]+?)\n", content)
                                if regex_get is not None:
                                    m_way = regex_get.group(1).strip()
                    if k not in self.trans_data.keys():
                        self.trans_data[k] = {}
                    if m_zhname is not None and len(m_zhname) > 0:
                        self.trans_data[k]["zh_name"] = m_zhname
                    if m_way is not None and len(m_way) > 0:
                        self.trans_data[k]["get_way"] = m_way
                    print("%s="%k, self.trans_data[k])
                except Exception:
                    traceback.print_exc()
        
        print("更新记忆结果：")
        print(self.trans_data)
        with open(self.__trans_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.trans_data, ensure_ascii=False))
        self.__load_translate(self.trans_data)

        # 结束
        ses.close()
        self.__async_thread = None