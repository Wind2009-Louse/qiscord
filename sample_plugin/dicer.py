from typing import Tuple
from qiscord.msg_handler.base_handler import *
from qiscord.decorator import singleton
import re
import random
import traceback

class Dice:
    def __init__(self, dice_str: str) -> None:
        regex_fixed = re.match("^(\d+)", dice_str)
        if regex_fixed is not None:
            self.is_random = False
            self.dice_count = 1
            self.dice_maxnum = int(regex_fixed.group(1))
        
        regex_random = re.match("^(\d*)[Dd](\d+)", dice_str)
        if regex_random is not None:
            self.is_random = True
            count_str = regex_random.group(1)
            if len(count_str) == 0:
                self.dice_count = 1
            else:
                self.dice_count = int(regex_random.group(1))
                if self.dice_count <= 0:
                    raise ValueError("不能不丢骰子！")
            self.dice_maxnum = int(regex_random.group(2))
            if self.dice_maxnum <= 0:
                raise ValueError("不能丢0面骰！")
        
        if regex_fixed is None and regex_random is None:
            raise ValueError("骰子格式错误！")
    def roll(self) -> Tuple[int, str]:
        if self.is_random:
            result_str_list = []
            result_sum = 0
            for times in range(0, self.dice_count):
                cur = random.randint(1, self.dice_maxnum)
                result_sum += cur
                result_str_list.append(str(cur))
            return (result_sum, "(%s)"%("+".join(result_str_list)))
        else:
            return (self.dice_maxnum, str(self.dice_maxnum))

@singleton
class Dicer(Base_handler):
    def __init__(self):
        super().__init__()
        self._method_name = "骰子"
        self._method_detail = ["骰娘指令：\nr 1d100\nr 3d100+50+1d10"]
        self._trigger_list = ["骰子", "丢骰子", "骰", "r"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data) or len(data) < 2:
            return None
        data_arg = data[1]
        arg_list = data_arg.split("+")
        dice_list: List[Dice] = []
        dice_count = 0
        try:
            for arg in arg_list:
                dice = Dice(arg)
                dice_count += dice.dice_count
                dice_list.append(dice)
            if dice_count > 100:
                raise ValueError("一次只能丢最多100个骰子！")
            sum = 0
            result = data_arg + "="
            result_str_list: List[str] = []
            for d in dice_list:
                num, res = d.roll()
                sum += num
                result_str_list.append(res)
            result += "+".join(result_str_list) + "=" + str(sum)
            return result
        except ValueError as v:
            return str(v.args[0])
        except Exception:
            traceback.print_exc()
            return None