import socket
import requests
import json
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Set
from qiscord.msg_handler.base_handler import Base_handler
from qiscord.msg_handler import echo, memo_handler, user_handler, chara_handler
from qiscord.decorator import singleton
from qiscord.toolkit import function_kit

HttpResponseHeader = '''HTTP/1.1 200 OK
Content-Type: text/html

OK
'''

MSG        = "message"
MT         = "message_type"
MT_PRIVATE = "private"
MT_GROUP   = "group"
MT_GUILD   = "guild"
RM         = "raw_message"
SI         = "self_id"
SI_T       = "self_tiny_id"
GID        = "group_id"
CID        = "guild_id"
CCID       = "channel_id"
UID        = "user_id"
MID        = "message_id"

@singleton
class Listenter(threading.Thread):
    def __init__(self, port=19198, print_info=False):
        super().__init__()
        self.__running = False
        self.__port = port
        self.__flag = False
        self.print_info = print_info
        self.__sk: socket.socket = None
        self.__ses = requests.Session()
        self.__handler_list: Set[Base_handler] = set()
        self.__threadPool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="handler_")
        self.restart_sk()
    
    def run(self):
        '''
        线程启动
        '''
        self.load_default_handler()
        if self.print_info:
            print("开始监听端口：", self.__port)
        while(self.__flag):
            if not self.__running:
                continue
            try:
                conn, addr = self.__sk.accept()
                req = conn.recv(102400).decode(encoding='utf-8')
                req = req[req.find("{"):]
                conn.sendall((HttpResponseHeader).encode(encoding='utf-8'))
                conn.close()
                if len(req) > 0:
                    if self.print_info:
                        print(req)
                    self.__threadPool.submit(self.__handle_request, req)
            except Exception:
                traceback.print_exc()
                continue

    def __handle_request(self, req_str: str):
        '''
        处理信息
        '''
        try:
            json_data = json.loads(req_str)
            is_at, arg_list_str = self.is_call_self(json_data)
            if not is_at:
                return
            arg_list = self.build_arg_list(arg_list_str)
            for hdl in self.__handler_list:
                response = hdl.exec(json_data, arg_list)
                if response is not None:
                    self.response(json_data, response, True)
                    break
        except Exception:
            traceback.print_exc()

    def restart_sk(self):
        '''
        重启socket并监听
        '''
        if self.__sk is not None:
            try:
                self.__sk.close()
                self.__sk = None
                self.__running = False
            except Exception:
                traceback.print_exc()
                print("重启socket失败！")
                return

        self.__sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sk.bind(('0.0.0.0', self.__port))
        self.__sk.listen(100)
        self.__running = True
        self.__flag = True
    
    def change_port(self, new_port: int):
        '''
        修改socket监听端口，并重启socket
        '''
        self.__port = new_port
        if self.__running:
            self.restart_sk()
    
    def stop(self):
        '''
        停止服务，重新启动需要另外创建实例
        '''
        if not self.__running:
            print("服务暂未启动！")
            return
        if self.__sk is not None:
            try:
                self.__sk.close()
                self.__sk = None
                self.__running = False
            except Exception:
                traceback.print_exc()
                return
        self.__flag = False

    def build_arg_list(self, arg:str) -> list:
        '''
        将信息拆分成列表
        '''
        result_list = []
        if arg is None:
            return result_list
        
        for s in arg.strip().split(" "):
            ss = s.strip()
            if len(ss) > 0:
                result_list.append(ss)
        
        return result_list

    def response(self, req:dict, response:str, at:bool=False):
        '''
        回复信息
        '''
        message_type = function_kit.get_v_from_d(req, MT)

        # 判断是否需要加at标识
        if at and message_type != MT_PRIVATE:
            uid = function_kit.get_v_from_d(req, UID, need_str=True)
            if uid is not None:
                response = "[CQ:at,qq=" + uid + "] " + response
        
        # 构建结构体
        data = {MSG: response}
        url = "http://127.0.0.1:5700/send_msg"
        if message_type == MT_GUILD:
            url = "http://127.0.0.1:5700/send_guild_channel_msg"
            data[CID] = function_kit.get_v_from_d(req, CID)
            data[CCID] = function_kit.get_v_from_d(req, CCID)
        else:
            data[GID] = function_kit.get_v_from_d(req, GID)
            data[UID] = function_kit.get_v_from_d(req, UID)
            data[MT]  = message_type
        
        if self.print_info:
            print("reply: " + response)

        try:
            res = self.__ses.post(url, headers={"content-type": "application/json; charset=UTF-8"}, data=json.dumps(data))
            mid = function_kit.get_v_from_d(req, MID)
            if type(mid) != str:
                mid = str(mid)
            if self.print_info:
                print("reply(%s)'s resposne: %s"%(mid, res.text))

        except Exception:
            traceback.print_exc()

    def is_call_self(self, req):
        '''
        判断消息内容是否atBot或者私聊，并返回at以外的信息内容
        '''
        message_type = function_kit.get_v_from_d(req, MT)
        message = function_kit.get_v_from_d(req, MSG)
        if MT_PRIVATE == message_type:
            return True, message
        else:
            self_id = function_kit.get_v_from_d(req, SI, need_str=True)
            if MT_GUILD == message_type:
                self_id = function_kit.get_v_from_d(req, SI_T, need_str=True)
            at_str = "[CQ:at,qq=" + self_id + "]"
            if not message.startswith(at_str):
                return False, None
            else:
                return True, message[len(at_str):]
    
    def load_default_handler(self):
        '''
        加载默认的处理器
        '''
        self.__handler_list.add(Help())
        self.__handler_list.add(echo.Echo())
        self.__handler_list.add(user_handler.User_Handler())
        self.__handler_list.add(memo_handler.Memo())
        self.__handler_list.add(chara_handler.Char_Handler())

    def get_current_handler(self) -> List[Base_handler]:
        '''
        获取当前加载中的处理器
        '''
        return self.__handler_list

    def add_handler(self, h: Base_handler):
        '''
        装载自己的处理器
        '''
        if h is None:
            return
        for c_h in self.__handler_list:
            if h == c_h:
                if self.print_info:
                    print("[WARNING]该功能重复装载：", h.get_method_name)
                return
        self.__handler_list.add(h)

@singleton
class Help(Base_handler):
    __listener: Listenter

    def __init__(self):
        super().__init__()
        self.__listener = Listenter()
        self._method_name = "帮助"
        self._method_detail = ["帮助 <功能>：\n查阅功能说明"]
        self._trigger_list = ["帮助", "help", "h"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data):
            return None
        sub_method = None
        page = 1
        if len(data) > 1:
            sub_method = data[1]
        if len(data) > 2:
            page_str = data[2]
            try:
                page = int(page_str)
            except Exception:
                pass
        handler_list = self.__listener.get_current_handler()
        # 指定了子功能，输出该功能自带的说明
        if sub_method is not None:
            for h in handler_list:
                if not h.is_trigger([sub_method]):
                    continue
                help_data_list = h.get_method_detail()
                help_name = h.get_method_name()
                if len(help_data_list) == 0:
                    return "%s：\n该功能没有填写帮助信息。"%help_name
                if page <= 0:
                    page = 1
                if page > len(help_data_list):
                    page = len(help_data_list)
                help_text = help_data_list[page - 1]
                return "%s：(%d/%d)\n%s"%(help_name, page, len(help_data_list), help_text)
        
        # 找不到功能说明，输出所有功能名称
        result = "当前可用功能：\n"
        print_idx = 0
        for handler in handler_list:
            if not handler.enable:
                continue
            if print_idx > 0:
                if print_idx % 5 == 0:
                    result += "\n"
                else:
                    result += "、"
            result += handler.get_method_name()
            print_idx += 1
        result += "\n请使用“帮助 <功能名>查阅具体帮助。”"
        return result