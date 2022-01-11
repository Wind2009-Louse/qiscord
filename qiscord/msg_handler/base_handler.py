from typing import List
import abc

class Base_handler(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self.enable = True
        self._method_name = ""
        self._method_detail: List[str] = []
        self._trigger_list: List[str] = []
        pass
    
    def get_method_name(self):
        return self._method_name
    
    def get_method_detail(self):
        return self._method_detail
    
    def is_trigger(self, data: List[str]) -> bool:
        if not self.enable or len(data) <= 0:
            return False
        for trigger_arg in self._trigger_list:
            if data[0].lower() == trigger_arg.lower():
                return True
        return False
    
    @abc.abstractmethod
    def exec(self, req: dict, data: List[str]) -> str:
        return None