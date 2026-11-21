"""lightkit 核心 API：点光源衰减与多光源能量守恒叠加。

衰减核
------
以到光源中心的归一化距离 ``t = d / radius`` 为参数，使用三次 smoothstep
的补函数::

    f(t) = 1 - (3t^2 - 2t^3) = (1 - t)^2 * (1 + 2t)

性质：

* ``f(0) = 1``（距离 0 取 1）；
* ``f(1) = 0``（半径处取 0，半径外常量 0）；
* ``f'(t) = 6t(t - 1) <= 0``，在 ``(0, 1)`` 上严格递减；
* ``f'(0) = f'(1) = 0``，与半径外的常量 0 拼接后一阶连续（soft radius）。

叠加
----
每个光源按单位峰值能量计，总能量为光源数量；叠加结果按总能量归一
（取平均），因此光源数量增加不会整体过曝，且结果与输入顺序无关。
"""

import math

__all__ = [
    "Light",
    "LightError",
    "InvalidRadiusError",
    "NonFiniteCoordinateError",
    "EmptyLightListError",
]


class LightError(ValueError):
    """lightkit 参数错误基类。

    继承 :class:`ValueError`，因此既有的 ``except ValueError`` 调用方
    无需改动即可捕获全部参数错误。
    """


class InvalidRadiusError(LightError):
    """半径非法：非有限值，或 ``<= 0``。"""


class NonFiniteCoordinateError(LightError):
    """坐标非法：包含 NaN / Inf，或不是二维数值坐标。"""


class EmptyLightListError(LightError):
    """光源列表为空（可区分错误，供严格校验路径使用）。"""


def _coord_pair(value, what):
    """把坐标转换为两个有限浮点数，否则抛出可区分的错误。"""
    try:
        x = float(value[0])
        y = float(value[1])
    except (TypeError, ValueError, IndexError, KeyError) as exc:
        raise NonFiniteCoordinateError(
            f"{what} must be a pair of finite numbers, got {value!r}"
        ) from exc
    if not (math.isfinite(x) and math.isfinite(y)):
        raise NonFiniteCoordinateError(
            f"{what} must be finite, got {value!r}"
        )
    return x, y


class Light:
    """二维点光源。

    实例在构造后不再变更，``attenuation`` 只读取自身属性并使用局部变量，
    因此同一光源被多线程并发求值是安全的。
    """

    __slots__ = ("_x", "_y", "_r", "_r2")

    def __init__(self, position, radius):
        x, y = _coord_pair(position, "position")
        try:
            r = float(radius)
        except (TypeError, ValueError) as exc:
            raise InvalidRadiusError(
                f"radius must be a finite number > 0, got {radius!r}"
            ) from exc
        if not math.isfinite(r) or r <= 0.0:
            raise InvalidRadiusError(
                f"radius must be a finite number > 0, got {radius!r}"
            )
        # 初始化后只读，保证并发求值安全。
        self._x = x
        self._y = y
        self._r = r
        self._r2 = r * r

    @property
    def position(self):
        return (self._x, self._y)

    @property
    def radius(self):
        return self._r

    def attenuation(self, point):
        """返回光源在 ``point`` 处的衰减系数，取值 ``[0, 1]``。"""
        try:
            px = point[0]
            py = point[1]
        except (TypeError, IndexError, KeyError) as exc:
            raise NonFiniteCoordinateError(
                f"point must be a pair of finite numbers, got {point!r}"
            ) from exc
        try:
            finite = math.isfinite(px) and math.isfinite(py)
        except TypeError as exc:  # 非数值坐标
            raise NonFiniteCoordinateError(
                f"point must be a pair of finite numbers, got {point!r}"
            ) from exc
        if not finite:
            raise NonFiniteCoordinateError(
                f"point must be finite, got {point!r}"
            )

        dx = px - self._x
        dy = py - self._y
        d2 = dx * dx + dy * dy
        r2 = self._r2
        if d2 >= r2:  # 半径处及半径外取 0
            return 0.0
        t = math.sqrt(d2) / self._r  # 0 <= t < 1
        u = 1.0 - t
        # f(t) = (1-t)^2 (1+2t)：f(0)=1、f(1)=0、f'(0)=f'(1)=0、单调递减
        return u * u * (1.0 + 2.0 * t)

    @staticmethod
    def combine(lights, point):
        """按总能量归一叠加多个光源在 ``point`` 处的衰减。

        * 每个光源按单位峰值能量计，总能量为 ``len(lights)``；
        * 结果 = ``sum(contribution_i) / len(lights)``，恒在 ``[0, 1]``，
          光源数量增加不会整体过曝；
        * 使用 :func:`math.fsum`，结果与输入顺序无关（可交换）；
        * 只读取光源、复制容器，不修改输入光源及其顺序。

        空光源列表按恒等元返回 ``0.0``（与既有行为一致）。
        """
        _coord_pair(point, "point")  # 先校验坐标，非有限坐标始终报错

        items = list(lights)  # 复制容器，后续不触碰输入
        if not items:
            return 0.0

        total = math.fsum(light.attenuation(point) for light in items)
        return total / len(items)

    @classmethod
    def combine_strict(cls, lights, point):
        """同 :meth:`combine`，但空光源列表抛出 :class:`EmptyLightListError`。

        供需要把“没有光源”与“光照为 0”区分开的调用方使用；默认
        :meth:`combine` 保持恒等元 ``0.0`` 的既有行为。
        """
        items = list(lights)
        if not items:
            raise EmptyLightListError("lights must not be empty")
        return cls.combine(items, point)
