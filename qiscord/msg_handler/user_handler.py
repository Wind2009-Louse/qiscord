from qiscord.msg_handler.base_handler import *
from qiscord.decorator import singleton
from qiscord.toolkit import user_db, function_kit
import re

@singleton
class User_Handler(Base_handler):
    __db: user_db.DB

    def __init__(self):
        super().__init__()
        self.__db = user_db.DB()
        self._method_name = "权限"
        self._method_detail = ["权限：\n查看自身权限。\n权限 <at> <权限等级>：\n授予用户权限。"]
        self._trigger_list = ["权限"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data):
            return None
        user_id = function_kit.get_v_from_d(req, "user_id", default="", need_str=True)
        method = 1
        target_user_id = None
        new_level = 0
        if len(data) > 2:
            regex_s = re.search("\[CQ:at,qq=(\d+)\]", data[1])
            if regex_s is not None:
                target_user_id = regex_s.group(1)
                try:
                    new_level = int(data[2])
                    method = 2
                except Exception:
                    pass
        self_auth = self.__db.check_auth_by_req(req)
        if method == 1:
            return "你当前的权限等级为：" + str(self_auth)
        elif method == 2:
            if user_id == target_user_id:
                return "不能修改自己的权限等级！"
            elif self_auth <= new_level:
                return "你可以授权的等级最高为" + str(self_auth - 1) + "!"
            else:
                target_auth = self.__db.check_auth_by_req(req, user_id=target_user_id)
                if target_auth >= self_auth:
                    return "你无权修改该用户的权限！"
                if self.__db.add_or_update_auth_by_req(req, target_user_id, new_level):
                    return "修改权限等级成功！"
                else:
                    return "修改权限等级失败！"