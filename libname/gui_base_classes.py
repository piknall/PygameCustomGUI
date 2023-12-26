from __future__ import annotations

import abc
import typing

import pygame


class Dimensions:
    def __init__(self,
                 position: tuple[int, int] | None = None,
                 size: tuple[int, int] | None = None,
                 ):
        self._position = position if position is not None else (None, None)
        self._size = size if size is not None else (None, None)

    @property
    def x(self) -> int:
        return self._position[0]

    @x.setter
    def x(self, value: int) -> None:
        self._position = (value, self._position[1])

    @property
    def y(self) -> int:
        return self._position[1]

    @y.setter
    def y(self, value: int) -> None:
        self._position = (self._position[0], value)

    @property
    def width(self) -> int:
        return self._size[0]

    @width.setter
    def width(self, value: int) -> None:
        self._size = (value, self._size[1])

    @property
    def height(self) -> int:
        return self._size[1]

    @height.setter
    def height(self, value: int) -> None:
        self._size = (self._size[0], value)

    @property
    def right(self) -> int:
        return self._position[0] + self._size[0]

    @right.setter
    def right(self, value: int) -> None:
        self._position = (value - self._size[0], self._position[1])

    @property
    def bottom(self) -> int:
        return self._position[1] + self._size[1]

    @bottom.setter
    def bottom(self, value: int) -> None:
        self._position = (self._position[0], value - self._size[1])

    @property
    def position(self) -> tuple[int, int]:
        return self._position

    @property
    def size(self) -> tuple[int, int]:
        return self._size


class PositionValueSpecifier:
    STATIC_EXPRESSION = "static_expression"
    PROPORTION_EXPRESSION = "proportion_expression"
    CALLABLE_EXPRESSION = "callable_expression"
    HORIZONTAL = "horizontal_orientation"
    VERTICAL = "vertical_orientation"

    def __init__(self,
                 expression: int | typing.Callable[[], int] | float | str,
                 master: Dimensions | None = None,
                 horizontal: bool = False,
                 vertical: bool = False,
                 ):
        self.expression, self.expression_type = self._get_expression_type_and_value(expression)
        self.master = master
        self.check_for_master()
        if horizontal and vertical:
            self.orientation = None
        elif horizontal:
            self.orientation = self.HORIZONTAL
        elif vertical:
            self.orientation = self.VERTICAL
        else:
            self.orientation = None

    def _get_expression_type_and_value(self, expression: int | typing.Callable[[], int] | float | str) \
            -> tuple[int | typing.Callable[[], int] | float, str]:
        if type(expression) is int:
            return expression, self.STATIC_EXPRESSION

        if callable(expression):
            return expression, self.CALLABLE_EXPRESSION

        if type(expression) is float:
            if not 0 <= expression <= 1:
                raise ValueError(f"expression: {expression}, interpreted as proportion, has to be >= 0.0 and <= 1.0")
            return expression, self.PROPORTION_EXPRESSION

        if type(expression) is str:
            str_expression = expression.strip()
            if str_expression[-1] != "%":
                raise ValueError(f"invalid str expression: {expression}, "
                                 f"an percentage expression has to be indicated with an ending '%' character")
            proportion = int(str_expression[:-1]) / 100
            try:
                return self._get_expression_type_and_value(proportion)
            except ValueError as proportion_exception:
                raise ValueError(f"invalid str expression: {expression}, evaluated proportion {proportion} let to:\n "
                                 f"ValueError: {proportion_exception.__notes__[0]}")

    def check_for_master(self) -> None:
        if self.expression_type == self.PROPORTION_EXPRESSION and self.master is None:
            raise ValueError(f"if an proportional expression ({self.expression} is chosen an master has to be set")

    def evaluate(self) -> int:
        if self.expression_type == self.STATIC_EXPRESSION:
            return self.expression

        if self.expression_type == self.PROPORTION_EXPRESSION:
            if self.orientation == self.HORIZONTAL:
                return round(self.master.width * self.expression)
            if self.orientation == self.VERTICAL:
                return round(self.master.height * self.expression)
            raise ValueError(f"dimensions has to be defined to be horizontal or vertical to evaluate "
                             f"proportion expression")

        return self.expression()


class SpaceSpecifier(Dimensions):
    def __init__(
            self,
            master: GuiElementMaster,
            left_nodes: typing.Iterable[SpaceSpecifier] | None,
            right_nodes: typing.Iterable[SpaceSpecifier] | None,
            min_width: int = 0,
            max_width: int | None = None,
            min_height: int = 0,
            max_height: int | None = None,
            horizontal_priority: tuple[int, int] | None = None,
            vertical_priority: tuple[int, int] | None = None,
            horizontal_grow_rate: int | float | None = None,
            vertical_grow_rate: int | float | None = None,
            left_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            right_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            top_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            bottom_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            left_padding: int | tuple[int | None, ...] = None,
            right_padding: int | tuple[int | None, ...] = None,
            top_padding: int | tuple[int | None, ...] = None,
            bottom_padding: int | tuple[int | None, ...] = None,
    ):
        super().__init__()

        self.master = master
        self.left_nodes = []
        self.right_nodes = []

    def add_left_node(self, specifier: SpaceSpecifier) -> None:
        self.left_nodes.append(specifier)
        specifier.add_right_node(self)

    def add_right_node(self, specifier: SpaceSpecifier) -> None:
        self.right_nodes.append(specifier)
        specifier.add_left_node(self)


class GuiElement(SpaceSpecifier):
    def __init__(
            self,
            master: GuiElementMaster,
            left_nodes: typing.Iterable[SpaceSpecifier] | None,
            right_nodes: typing.Iterable[SpaceSpecifier] | None,
            min_width: int = 0,
            max_width: int | None = None,
            min_height: int = 0,
            max_height: int | None = None,
            horizontal_priority: tuple[int, int] | None = None,
            vertical_priority: tuple[int, int] | None = None,
            horizontal_grow_rate: int | float | None = None,
            vertical_grow_rate: int | float | None = None,
            left_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            right_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            top_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            bottom_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            left_padding: int | tuple[int | None, ...] = None,
            right_padding: int | tuple[int | None, ...] = None,
            top_padding: int | tuple[int | None, ...] = None,
            bottom_padding: int | tuple[int | None, ...] = None,
    ):
        super().__init__(
            master=master,
            left_nodes=left_nodes,
            right_nodes=right_nodes,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            horizontal_priority=horizontal_priority,
            vertical_priority=vertical_priority,
            horizontal_grow_rate=horizontal_grow_rate,
            vertical_grow_rate=vertical_grow_rate,
            left_fixed_position=left_fixed_position,
            right_fixed_position=right_fixed_position,
            top_fixed_position=top_fixed_position,
            bottom_fixed_position=bottom_fixed_position,
            left_padding=left_padding,
            right_padding=right_padding,
            top_padding=top_padding,
            bottom_padding=bottom_padding,
        )

    @abc.abstractmethod
    def get_mutate_surfaces(self, surface, position) -> tuple[pygame.Surface, ...]:
        pass

    @abc.abstractmethod
    def get_general_surfaces(self, surface, position) -> tuple[pygame.Surface, ...]:
        pass

    @abc.abstractmethod
    def set_size(self) -> None:
        pass


class GuiElementMaster(GuiElement):
    def __init__(
            self,
            master: GuiElementMaster | WindowMaster,
            left_nodes: typing.Iterable[SpaceSpecifier] | None,
            right_nodes: typing.Iterable[SpaceSpecifier] | None,
            min_width: int = 0,
            max_width: int | None = None,
            min_height: int = 0,
            max_height: int | None = None,
            horizontal_priority: tuple[int, int] | None = None,
            vertical_priority: tuple[int, int] | None = None,
            horizontal_grow_rate: int | float | None = None,
            vertical_grow_rate: int | float | None = None,
            left_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            right_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            top_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            bottom_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            left_padding: int | tuple[int | None, ...] = None,
            right_padding: int | tuple[int | None, ...] = None,
            top_padding: int | tuple[int | None, ...] = None,
            bottom_padding: int | tuple[int | None, ...] = None,
    ):
        super().__init__(
            master=master,
            left_nodes=left_nodes,
            right_nodes=right_nodes,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            horizontal_priority=horizontal_priority,
            vertical_priority=vertical_priority,
            horizontal_grow_rate=horizontal_grow_rate,
            vertical_grow_rate=vertical_grow_rate,
            left_fixed_position=left_fixed_position,
            right_fixed_position=right_fixed_position,
            top_fixed_position=top_fixed_position,
            bottom_fixed_position=bottom_fixed_position,
            left_padding=left_padding,
            right_padding=right_padding,
            top_padding=top_padding,
            bottom_padding=bottom_padding,
        )

        self.elements = []

    def add_element(self, element: GuiElement) -> None:
        self.elements.append(element)

    @abc.abstractmethod
    def get_mutate_surfaces(self, surface, position) -> None:
        pass

    @abc.abstractmethod
    def get_general_surfaces(self, surface, position) -> None:
        pass

    @abc.abstractmethod
    def set_size(self) -> None:
        pass


class WindowMaster:
    pass
