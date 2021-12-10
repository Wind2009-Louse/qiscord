from re import S
from qiscord.msg_handler.base_handler import *
from qiscord.decorator import singleton
from qiscord.toolkit import chara, user_db, chara_printer

@singleton
class Char_Handler(Base_handler):
    __chara_db: chara.CharaDb
    __user_db: user_db.DB

    def __init__(self):
        super().__init__()
        self.__chara_db = chara.CharaDb()
        self.__user_db = user_db.DB()
        self._method_name = "查角色"
        self._method_detail = ["查角色 <角色id/角色名> [角色信息...]：\n查询角色的指定信息。\n支持查询的信息：\n* 星级数据、Connect、Magia、Doppel、精神强化数据、ex数据、翻译信息等。如：\n查角色 1001 精神强化 5星 Connect Magia\n查角色 圆神 ex Doppel", "查角色 添加简称 <角色id/角色名> <简称>：\n为角色添加简称（需要1级权限）。\n查角色 删除简称 <简称>：\n删除角色简称（需要1级权限）。\n查角色 reload：\n重新加载角色信息（需要4级权限）。\n查角色 fetch：\n重新抓取译名（需要4级权限）。"]
        self._trigger_list = ["查角色", "角色", "查烧酒", "烧酒"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data):
            return None
        if len(data) < 2:
            return None
        key = " ".join(data[1:])
        if key == "reload":
            if self.__user_db.check_auth_by_req(req) < 4:
                return "无权操作！"
            return str(self.__chara_db.reload_data())
            
        elif key == "fetch":
            if self.__user_db.check_auth_by_req(req) < 4:
                return "无权操作！"
            return str(self.__chara_db.refresh_trans())

        elif data[1] in ["添加简称", "增加简称"]:
            if self.__user_db.check_auth_by_req(req) < 1:
                return "无权操作！"
            if len(data) < 4:
                return "参数不足！"
            search_key = data[2:-1]
            short_name = data[-1]
            memo_list = self.__chara_db.search_chara(search_key)
            if len(memo_list) == 0:
                return "以下关键字找不到角色：" + " ".join(search_key)
            elif len(memo_list) > 1:
                result = "找到多于一个角色，请修改关键词！"
            else:
                return str(self.__chara_db.add_alias(memo_list[0], short_name))

        elif data[1] == "删除简称":
            if self.__user_db.check_auth_by_req(req) < 1:
                return "无权操作！"
            if len(data) < 3:
                return "参数不足！"
            short_name = data[2]
            return str(self.__chara_db.del_alias(short_name))

        else:
            key_list = data[1:]
            last_exists_result = []
            for filter_idx in range(1, len(key_list) + 1):
                search_key_list = key_list[0:filter_idx]
                show_key_list = key_list[filter_idx:]
                result_list = self.__chara_db.search_chara(search_key_list)
                if len(result_list) == 1:
                    return chara_printer.print_chara(result_list[0], chara_printer.CharaPrintFilter(show_key_list))
                elif len(result_list) > 1:
                    last_exists_result = result_list

            if len(last_exists_result) == 0:
                return "以下关键字找不到角色：" + key
            elif len(last_exists_result) > 1:
                result = "找到%d个角色"%(len(last_exists_result))
                if len(last_exists_result) > 10:
                    result += "，以下只显示前10条："
                    
                max_count = 10
                for res in last_exists_result:
                    m_name = chara_printer.print_chara_thumb(res)
                    if m_name is None:
                        continue
                    result += "\n" + m_name
                    max_count -= 1
                    if max_count <= 0:
                        break
                return result