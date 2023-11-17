class HeartBeatReply:
    """
    心跳包回复（人气值）
    """

    def __init__(self, msg: dict):
        self.value = msg['data']

    def __str__(self):
        return f"人气值: {self.value}"

    def __repr__(self):
        return f"[心跳包回复]{self.__str__()}"


class DanmuMsg:
    """
    弹幕
    """

    def __init__(self, msg: dict):
        data = msg["info"]
        self.uid: int = data[2][0]
        self.name: str = data[2][1]
        self.message: str = data[1]
        self.is_emotion: bool = 'url' in data[0][13]
        self.emotion_pic: str = data[0][13]['url'] if self.is_emotion else ''

    def __str__(self):
        if self.is_emotion:
            return f"{self.name}: [表情 {self.message}]"
        else:
            return f"{self.name}: {self.message}"

    def __repr__(self):
        return f"[弹幕]{self.__str__()}"


class SuperChatMessage:
    """
    醒目留言
    """

    def __init__(self, msg: dict):
        data = msg['data']
        self.uid: int = data['uid']  # 用户ID
        self.name: str = data['user_info']['uname']  # 用户名
        self.message: str = data['message']  # 消息
        self.face: str = data['user_info']['face']  # 头像链接
        self.price: str = data['price']  # 价格（SC打赏费用）

    def __str__(self):
        return f"{self.name}: [醒目留言] {self.message}"

    def __repr__(self):
        return f"[醒目留言]{self.__str__()}"


class EntryEffect:
    """
    舰长进入直播间提醒
    """

    def __init__(self, msg: dict):
        data = msg['data']
        self.uid: str = data['uid']
        self.message: str = data['copy_writing']
        self.face: str = data['face']

    @property
    def name(self) -> str:
        start = self.message.find('<%')
        end = self.message.find('%>')
        return self.message[start + 2:end]

    def __str__(self):
        return f"{self.message.replace('<%', '【').replace('%>', '】')}"

    def __repr__(self):
        return f"[舰长入场]{self.__str__()}"


class DanmuAggregation:
    """
    集体弹幕,推测为出现过多相同弹幕时的优化,也可能只是单纯的抽奖弹幕
    """

    def __init__(self, msg: dict):
        data = msg['data']
        self.message = data['msg']
        self.aggregation_num = data['aggregation_num']
        self.aggregation_icon = data['aggregation_icon']

    def __str__(self):
        return f"{self.message} × {self.aggregation_num}"

    def __repr__(self):
        return f"[集体弹幕]{self.__str__()}"


class GuardBuy:
    def __init__(self, msg: dict):
        data = msg['data']
        self.name = data['username']
        self.uid = data['uid']
        self.gift = data['gift_name']

        self.price = data['price']

    def __str__(self):
        return f"{self.name} 成为了 {self.gift}"

    def __repr__(self):
        return f"[大航海]{self.__str__()}"


class SendGift:
    def __init__(self, msg: dict):
        data = msg['data']
        self.name = data['uname']
        self.uid = data['uid']
        self.gift = data['giftName']
        self.gift_num = data['']
        self.face = data['face']
        self.action = data['action']
        self.total_coin = data['combo_total_coin']


class ComboSend:
    def __init__(self, msg: dict):
        data = msg['data']
        self.name = data['uname']
        self.uid = data['uid']
        self.gift = data['gift_name']
        self.gift_num = data['combo_num']
        self.action = data['action']
        self.total_coin = data['combo_total_coin']

    def __str__(self):
        return f"{self.name} {self.action} {self.gift} × {self.gift_num}"

    def __repr__(self):
        return f"[连续礼物]{self.__str__()}"
