import traceback
from qiscord.toolkit import function_kit, memoria, chara
TYPE_DICT= {"SKILL": "技能型", "ABILITY": "能力型"}

def print_memo(m : memoria.Memoria) -> str:
    '''
    显示记忆详细资料
    '''
    try:
        result = m.id + ":" + m.name
        if m.zh_name is not None:
            result += "(%s)"%m.zh_name
        result += "\n%s %s"%(m.type, m.rank)
        result += "\nHP：%d->%d"%(m.min_hp, m.max_hp)
        result += "\nATK：%d->%d"%(m.min_atk, m.max_atk)
        result += "\nDEF：%d->%d"%(m.min_def, m.max_def)

        if len(m.owner_id) > 0:
            if len(m.owner_chara) == 0:
                chara_db = chara.CharaDb()
                for id in m.owner_id:
                    c = chara_db.search_chara([str(id)])
                    if c is not None and len(c) == 1:
                        if c[0].zh_name is not None:
                            m.owner_chara.append(c[0].zh_name)
                        elif c[0].name is not None:
                            m.owner_chara.append(c[0].name)
            result += "\n可装备：" + ",".join(m.owner_chara)

        if m.type == "技能型":
            result += "\nCD：%d->%d"%(m.cd_nmlb, m.cd_mlb)
        if len(m.artlist_nmlb) > 0:
            result += "\n效果：%s"%(function_kit.artlist_to_str(m.artlist_nmlb))
        if len(m.artlist_mlb) > 0:
            result += "\n满破效果：%s"%(function_kit.artlist_to_str(m.artlist_mlb))
        if len(m.fetch_way) > 0:
            result += "\n入手方式：" + m.fetch_way
        
        return result
    except Exception as e:
        traceback.print_exc()
        return str(e.args[0])

def print_memo_thumb(m:memoria.Memoria) -> str:
    '''
    显示记忆缩略资料
    '''
    result = "[%s-%s]%s"%(m.id, m.rank, m.name)
    if m.zh_name is not None:
        result += "(%s)"%m.zh_name
    return result