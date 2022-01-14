import re
from qiscord.msg_handler.base_handler import *
from qiscord.decorator import singleton
from qiscord.toolkit import chara, chara_printer, function_kit, memoria, quest_calculate_kit, quest_data
from qiscord.toolkit.quest_data import QUEST_OPERATE

@singleton
class MP_Calculation_Handler(Base_handler):
    __memo_kit: memoria.MemoriaDb
    __chara_db: chara.CharaDb

    def __init__(self):
        super().__init__()
        self.__chara_db = chara.CharaDb()
        self.__memo_kit = memoria.MemoriaDb()

        self._method_name = "查MP"
        self._method_detail = [
            "查询角色MP量。\n用法：\n查MP <角色名> [记忆/参数...] [镜层/出盘/受击/自回...]\n* 记忆：直接输入记忆关键词\n* 参数：修改角色参数，如：\n** +10%%mpup\n** -10%%ampup",
            "* 镜层：以镜层模式计算MP\n* 出盘：接受A/B/C/O/M/D六种盘，小写时为其他角色使用的盘（不计入MP）。如：\n** aBo\n* 受击：根据受击次数计算MP。普通攻击为h，弱点属性攻击为H，如：\n** hhH\n自回：计算自回MP"]
        self._trigger_list = ["查MP", "MP"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data):
            return None
        if len(data) < 2:
            return None
        
        chara_name = data[1]
        chara_rank = -1
        split_idx = chara_name.find("-")
        if split_idx != -1:
            chara_rank_str = chara_name[split_idx + 1:]
            chara_name = chara_name[:split_idx]
            chara_rank = function_kit.trans_str_to_int(chara_rank_str, -1)

        chara_search_result = self.__chara_db.search_chara([chara_name])
        if len(chara_search_result) == 0:
            return "找不到角色：" + chara_name
        elif len(chara_search_result) > 1:
            result = "找到%d个角色"%(len(chara_search_result))
            if len(chara_search_result) > 10:
                result += "，以下只显示前10条："
                
            max_count = 10
            for res in chara_search_result:
                m_name = chara_printer.print_chara_thumb(res)
                if m_name is None:
                    continue
                result += "\n" + m_name
                max_count -= 1
                if max_count <= 0:
                    break
            return result
        
        current_chara = chara_search_result[0]

        quest_chara = quest_data.QuestUnit(current_chara, chara_rank)
        operate_list: List[QUEST_OPERATE] = []

        disc_status = quest_data.QuestDiscStatus()
        for arg in data[2:]:
            # 判断是否使用记忆
            memo_arg_split_list = arg.split("-")
            mlb_flag = True
            level = -1
            if len(memo_arg_split_list) > 1:
                for memo_arg in memo_arg_split_list[1:]:
                    if memo_arg in ["n", "N"]:
                        mlb_flag = False
                        continue
                    level = function_kit.trans_str_to_int(memo_arg, level)
            memo_search_list = self.__memo_kit.search_memoria(memo_arg_split_list[:1])
            if len(memo_search_list) == 1:
                memo = memo_search_list[0]
                quest_chara.load_memoria(memo, mlb_flag, level)
                continue

            # 判断是否自回
            if arg in ["自回", "regen"]:
                ope = QUEST_OPERATE(QUEST_OPERATE.REGEN)
                operate_list.append(ope)
                continue
            
            # 判断受击
            reg_hit = re.match("^[hHMm]+", arg)
            if reg_hit is not None:
                ope = QUEST_OPERATE(QUEST_OPERATE.DEFENSE)
                ope.value = arg
                operate_list.append(ope)
                continue
            
            # 判断是否按照镜层方式计算MP
            if arg in ["镜层", "镜界"]:
                disc_status.in_mirror = True
                continue

            # 判断出盘
            reg_disc = re.match("^([AaBbCcOoMD]{3})", arg)
            if reg_disc is not None:
                ope = QUEST_OPERATE(QUEST_OPERATE.ATTACK)
                ope.value = arg
                operate_list.append(ope)
                continue
            reg_c_plus = re.match("^([\d]+)[cC][harge|HARGE]{0,1}", arg)
            if reg_c_plus is not None:
                new_c_count = function_kit.trans_str_to_int(reg_c_plus.group(1), 0)
                if new_c_count > 0:
                    ope = QUEST_OPERATE(QUEST_OPERATE.CHANGE_C)
                    ope.value = new_c_count
                    operate_list.append(ope)
                    continue

            ope = QUEST_OPERATE(QUEST_OPERATE.ADJUST)
            ope.value = arg
            operate_list.append(ope)

        quest_chara.load_art_from_memoria()

        turn_count = 0
        turn_last_action = 99

        # 基础信息
        result = current_chara.name
        if current_chara.zh_name is not None:
            result += "(%s)"%current_chara.zh_name
        result += "\nMP效率：%d%%/%d%%"%(quest_chara.attack_mp_rate // 10, quest_chara.defense_mp_rate // 10)

        new_turn = False
        for operation in operate_list:
            # 判断是否进入下一回合
            if turn_last_action >= QUEST_OPERATE.ATTACK and turn_last_action >= operation.type:
                # 刷新回合信息
                new_turn = True
                if turn_count > 0:
                    quest_chara.turn_update()
                turn_count += 1

            # 判断是否展示MP信息
            if new_turn and operation.type >= QUEST_OPERATE.ATTACK:
                new_turn = False
                result += "\n----\nTurn %d\n%s"%(turn_count, quest_chara.print_mp_stat())
            turn_last_action = operation.type

            # 攻击MP
            if operation.type == QUEST_OPERATE.ATTACK:
                disc_status.load(operation.value, [quest_chara])
                if disc_status.loaded:
                    if disc_status.is_accele_combo():
                        quest_chara.inc_mp(200)
                    while disc_status.loaded:
                        try:
                            origin_mp = quest_chara.current_mp
                            self_act, add_mp = quest_calculate_kit.calc_attack_mp(quest_chara, disc_status)
                            new_mp = quest_chara.current_mp
                            if self_act:
                                result += "\n攻击MP：%.1f+%.1f=%.1f"%(origin_mp / 10, add_mp / 10, new_mp / 10)
                        except ValueError as ve:
                            result += "\n%s"%str(ve.args[0])
            # 受击MP
            elif operation.type == QUEST_OPERATE.DEFENSE:
                hit_list = operation.value
                for hit_idx in range(0, len(hit_list)):
                    hit_type = hit_list[hit_idx]
                    origin_mp = quest_chara.current_mp
                    add_mp = 0
                    if hit_type == "H":
                        add_mp = quest_calculate_kit.calc_defense_mp(quest_chara, disc_status, True)
                    elif hit_type == "M":
                        add_mp = quest_calculate_kit.calc_defense_mp(quest_chara, disc_status, True, True)
                    elif hit_type == "m":
                        add_mp = quest_calculate_kit.calc_defense_mp(quest_chara, disc_status, False, True)
                    else:
                        add_mp = quest_calculate_kit.calc_defense_mp(quest_chara, disc_status)
                    new_mp = quest_chara.current_mp
                    result += "\n受击MP：%.1f+%.1f=%.1f"%(origin_mp / 10, add_mp / 10, new_mp / 10)
            # 自回MP
            elif operation.type == QUEST_OPERATE.REGEN:
                origin_mp = quest_chara.current_mp
                add_mp = quest_calculate_kit.calc_regen_mp(quest_chara)
                new_mp = quest_chara.current_mp
                result += "\n自动回复MP：%.1f+%.1f=%.1f"%(origin_mp / 10, add_mp / 10, new_mp / 10)
            
            # 设定c数
            elif operation.type == QUEST_OPERATE.CHANGE_C:
                disc_status.current_charge = operation.value
            # 调整数值
            elif operation.type == QUEST_OPERATE.ADJUST:
                quest_chara.adjust_by_arg(operation.value)

        return result