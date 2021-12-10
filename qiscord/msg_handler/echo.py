from qiscord.msg_handler.base_handler import *
from qiscord.decorator import singleton

@singleton
class Echo(Base_handler):
    def __init__(self):
        super().__init__()
        self._method_name = "复读"
        self._method_detail = ["复读机"]
        self._trigger_list = ["复读", "echo"]
    
    def exec(self, req: dict, data: List[str]) -> str:
        if not self.is_trigger(data):
            return None
        return " ".join(data[1:])