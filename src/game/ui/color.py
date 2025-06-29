from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from functools import cache
from math import sin
from typing import ClassVar
from typing import Final
from typing import Self


@dataclass(frozen=True)
class Color:
    """Цвет"""

    _rgb_888_max: ClassVar = 255
    """Максимальное значение канала в формате RGB888"""

    _luma_r: ClassVar = 0.2126
    _luma_g: ClassVar = 0.7152
    _luma_b: ClassVar = 0.0722

    red: float
    """Компонента красного [0;1]"""
    green: float
    """Компонента зеленого [0;1]"""
    blue: float
    """Компонента синего [0;1]"""

    def __post_init__(self) -> None:
        assert 0.0 <= self.red <= 1.0
        assert 0.0 <= self.green <= 1.0
        assert 0.0 <= self.blue <= 1.0

    # from

    @classmethod
    def fromHex(cls, _hex: str) -> Self:
        """Создать цвет на основе HEX строки"""
        assert len(_hex) == 7
        assert _hex[0] == '#'

        r = int(_hex[1:3], 16)
        g = int(_hex[3:5], 16)
        b = int(_hex[5:7], 16)

        return cls.fromRGB888(r, g, b)

    @classmethod
    def fromRGB888(cls, r: int, g: int, b: int) -> Self:
        """Создать из формата RGB888"""
        return cls(
            r / cls._rgb_888_max,
            g / cls._rgb_888_max,
            b / cls._rgb_888_max,
        )

    @classmethod
    def fromHSL(cls, hue: float, saturation: float, lightness: float) -> Self:
        """Создать из формата HSL
        :param hue: от 0 до 360
        :param saturation: [0;1]
        :param lightness:  [0;1]
        :return:
        """

        c = (1 - abs(2 * lightness - 1)) * saturation
        x = c * (1 - abs((hue / 60) % 2 - 1))
        m = lightness - c / 2

        index = int(hue // 60) % 6

        table = (
            (c, x, 0),
            (x, c, 0),
            (0, c, x),
            (0, x, c),
            (x, 0, c),
            (c, 0, x),
        )

        r, g, b = table[index]
        return cls(r + m, g + m, b + m)

    # to

    def toRGB888(self) -> tuple[int, int, int]:
        """Преобразовать в формат RGB888"""
        return (
            int(self.red * self._rgb_888_max),
            int(self.green * self._rgb_888_max),
            int(self.blue * self._rgb_888_max)
        )

    def toHex(self) -> str:
        """Преобразовать в HEX представление"""
        r, g, b = self.toRGB888()
        return f"#{r:02x}{g:02x}{b:02x}"

    # methods

    def brightness(self) -> float:
        """Вычислить нормализованную яркость"""
        return self._luma_r * self.red + self._luma_g * self.green + self._luma_b * self.blue

    def withBright(self, k: float) -> Self:
        """Изменить яркость"""
        return Color(
            self.red * k,
            self.green * k,
            self.blue * k,
        )

    def brighter(self) -> Self:
        """Ярче"""
        return self.withBright(1.2)

    def darker(self) -> Self:
        """Тусклее"""
        return self.withBright(0.8)


white: Final = Color.fromHex("#ffffff")
black: Final = Color.fromHex("#000000")


class ValueGenerator[T](ABC):
    """Генератор последовательности значений на основании входа"""

    @abstractmethod
    def calc(self, x: int) -> T:
        """Рассчитать значение"""


@dataclass(frozen=True, kw_only=True)
class PhasedAmplitudeGenerator(ValueGenerator[float]):
    """Фазовый амплитудный генератор значений"""

    scale: float
    """Масштаб значения"""
    base: float
    """Базовое значение"""
    amplitude: float
    """Амплитуда значения"""

    def calc(self, x: int) -> float:
        return self.base + self.amplitude * sin(x * self.scale)


@dataclass(frozen=True, kw_only=True)
class LoopStepGenerator(ValueGenerator[float]):
    """Закольцованный шагающий генератор"""

    start: float
    """Начальное значение"""
    step: float
    """Шаг"""
    loop: float
    """Модуль"""

    def calc(self, x: int) -> float:
        return (self.start + x * self.step) % self.loop


@dataclass(frozen=True, kw_only=True)
class ColorGenerator(ValueGenerator[Color]):
    """Генератор цвета"""

    hue: ValueGenerator[float]
    saturation: ValueGenerator[float]
    light: ValueGenerator[float]

    def calc(self, x: int) -> Color:
        return Color.fromHSL(
            self.hue.calc(x),
            self.saturation.calc(x),
            self.light.calc(x)
        )


_team_color_gen = ColorGenerator(
    hue=LoopStepGenerator(
        start=15,
        step=200,
        loop=360,
    ),
    saturation=PhasedAmplitudeGenerator(
        scale=1.618,
        base=0.6,
        amplitude=0.2
    ),
    light=PhasedAmplitudeGenerator(
        scale=0.618,
        base=0.7,
        amplitude=0.2
    )
)


@cache
def get_team_color(team: int) -> Color:
    """Генерация уникального цвета для команды"""
    return _team_color_gen.calc(team)
