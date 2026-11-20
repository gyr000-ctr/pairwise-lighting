"""lightkit 核心 API（初始未实现）。"""


class Light:
    def __init__(self, position, radius):
        """构造"""
        raise NotImplementedError

    def attenuation(self, point):
        """衰减"""
        raise NotImplementedError

    def combine(self, lights, point):
        """叠加"""
        raise NotImplementedError
