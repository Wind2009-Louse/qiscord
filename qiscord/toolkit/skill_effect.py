from typing import List


class Skill:
    '''
    技能信息
    '''
    def __init__(self):
        # 技能适用范围（ALL/QUEST）
        self.effect_range = ""
        # 技能类型（ABILITY/SKILL/STARTUP）
        self.effect_type = ""
        # 冷却时间
        self.turn = 0
        self.current_turn = 0
        # 效果列表
        self.art_list : List[dict] = []
        # 自身发动的概率
        self.self_cent = 1
        # 合计发生的概率
        self.total_cent = 1
    
    def get_cent(self) -> str:
        '''
        获取发动概率
        '''
        if self.total_cent == 0:
            return ""
        return "[%d%%]"%(self.self_cent * 100 / self.total_cent)