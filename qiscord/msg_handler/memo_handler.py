from qiscord.msg_handler.base_handler import *
from qiscord.decorator import singleton
from qiscord.toolkit import memoria, user_db, memoria_printer

@singleton
class Memo(Base_handler):
    __memo_kit: memoria.MemoriaDb
    __user_db: user_db.DB

    def __init__(self):
        super().__init__()
        self.__memo_kit = memoria.MemoriaDb()
        self.__user_db = user_db.DB()
        self._method_name = "查记忆"
        self._method_detail = ["查记忆 <记忆id/记忆名>：\n查询记忆信息。\n查记忆 添加简称 <记忆id/记忆名> <简称>：\n为记忆添加简称（需要1级权限）。\n查记忆 删除简称 <简称>：\n删除记忆简称（需要1级权限）。\n查记忆 reload：\n重新加载记忆信息（需要4级权限）。\n查记忆 fetch：\n重新抓取译名（需要4级权限）。"]
        self._trigger_list = ["查记忆", "记忆"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data):
            return None
        if len(data) < 2:
            return None
        key = " ".join(data[1:])
        if key == "reload":
            if self.__user_db.check_auth_by_req(req) < 4:
                return "无权操作！"
            return str(self.__memo_kit.reload_data())
            
        elif key == "fetch":
            if self.__user_db.check_auth_by_req(req) < 4:
                return "无权操作！"
            return str(self.__memo_kit.refresh_trans())

        elif data[1] in ["添加简称", "增加简称"]:
            if self.__user_db.check_auth_by_req(req) < 1:
                return "无权操作！"
            if len(data) < 4:
                return "参数不足！"
            search_key = data[2]
            short_name = data[3]
            memo_list = self.__memo_kit.search_memoria(search_key)
            if len(memo_list) == 0:
                return "以下关键字找不到记忆：" + search_key
            elif len(memo_list) > 1:
                result = "找到多于一个记忆，请修改关键词！"
            else:
                return str(self.__memo_kit.add_alias(memo_list[0], short_name))

        elif data[1] == "删除简称":
            if self.__user_db.check_auth_by_req(req) < 1:
                return "无权操作！"
            if len(data) < 3:
                return "参数不足！"
            short_name = data[2]
            return str(self.__memo_kit.del_alias(short_name))

        else:
            result_list = self.__memo_kit.search_memoria(key)
            if len(result_list) == 0:
                return "以下关键字找不到记忆：" + key
            elif len(result_list) > 1:
                result = "找到%d个记忆"%(len(result_list))
                if len(result_list) > 10:
                    result += "，以下只显示前10条："
                max_count = 10
                for res in result_list:
                    m_name = memoria_printer.print_memo_thumb(res)
                    if m_name is None:
                        continue
                    result += "\n" + m_name
                    max_count -= 1
                    if max_count <= 0:
                        break
                return result
            elif len(result_list) == 1:
                return memoria_printer.print_memo(result_list[0])