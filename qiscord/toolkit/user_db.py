import sqlite3
import traceback
from qiscord.decorator import singleton
from qiscord.toolkit import function_kit

@singleton
class DB:
    db: sqlite3.Connection
    __db_path = "bot_data/user.db"

    def __init__(self):
        super()
        self.db = sqlite3.connect(self.__db_path, check_same_thread=False)
    
    def close(self):
        self.db.close()
    
    def check_auth_by_req(self, req: dict, user_id: str=None) -> int:
        if user_id is None:
            user_id = function_kit.get_v_from_d(req, "user_id", default="", need_str=True)
        channel_id = function_kit.get_v_from_d(req, "channel_id", default="", need_str=True)
        return self.check_auth(user_id, channel_id)

    def check_auth(self, user_id:str, channel_id:str) -> int:
        '''
        检查用户权限
        '''
        c = self.db.cursor()
        c.execute("select level from user where user_id=? and channel_id=? limit 1", (user_id,channel_id))
        res = c.fetchone()
        if res is None:
            return 0
        return res[0]
    
    def add_or_update_auth_by_req(self, req:dict, user_id:str, auth:int) -> bool:
        channel_id = function_kit.get_v_from_d(req, "channel_id", default="", need_str=True)
        return self.add_or_update_auth(user_id, channel_id, auth)

    def add_or_update_auth(self, user_id:str, channel_id:str, auth:int) -> bool:
        '''
        增改用户权限
        '''
        c = self.db.cursor()
        c.execute("select level from user where user_id=? and channel_id=? limit 1", (user_id,channel_id))
        res = c.fetchone()
        try:
            if res is not None:
                # 用户已存在，修改权限
                c.execute("update user set level=? where user_id=? and channel_id=? ", (auth,user_id,channel_id))
            elif auth > 0:
                # 用户不存在，添加权限
                c.execute("insert into user values(?,?,?)", (user_id,channel_id,auth))
            else:
                return False
            self.db.commit()
            return True
        except Exception:
            traceback.print_exc()
            return False
        finally:
            try:
                c.close()
            except Exception as e:
                pass