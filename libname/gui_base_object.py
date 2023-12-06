from __future__ import annotations

import typing


class Dimensions:
    def __init__(self,
                 position: tuple[int, int] = None,
                 size: tuple[int, int] = None,
                 ):
        self._position = position
        self._size = size

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

    def get_position(self) -> tuple[int, int]:
        return self._position

    def get_size(self) -> tuple[int, int]:
        return self._size
        
        
class PositionValueSpecifier:
    STATIC_EXPRESSION = "static_expression"
    PROPORTION_EXPRESSION = "proportion_expression"
    CALLABLE_EXPRESSION = "callable_expression"
    
    def __init__(self, 
                 expression: int | typing.Callable[[], int] | float | str,
                 master: Dimensions | None = None,
                 ):
        self.expression, self.expression_type = self._get_expression_type_and_value(expression)
        self.master = master
        self.check_for_master()

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

    def evaluate(self, horizontal: bool = False, vertical: bool = False) -> int:
        if self.expression_type == self.STATIC_EXPRESSION:
            return self.expression

        if self.expression_type == self.PROPORTION_EXPRESSION:
            if horizontal:
                return round(self.master.width * self.expression)
            if vertical:
                return round(self.master.height * self.expression)
            raise ValueError(f"dimensions has to be defined to be horizontal or vertical to evaluate "
                             f"proportion expression")

        return self.expression()


class SpaceSpecifier(Dimensions):
    def __init__(
            self,
            master: SpaceMaster,
            left_nodes: typing.Iterable[SpaceSpecifier],
            right_nodes: typing.Iterable[SpaceSpecifier],
            left_fixed_position: None | int | typing.Callable[[], int],
            right_fixed_position: None | int | typing.Callable[[], int],
    ):
        super().__init__()

        self.master = master
        self.master.add_specifier(self)

        self.left_fixed_position = left_fixed_position
        self.right_fixed_position = right_fixed_position

        self.horizontal_fixed_position = self._has_horizontal_fixed_position()

        self.left_nodes: list[SpaceSpecifier] = []
        self.right_nodes: list[SpaceSpecifier] = []
        for node in left_nodes:
            self.add_left_node(node)
        for node in right_nodes:
            self.add_right_node(node)

    def add_left_node(self, node: SpaceSpecifier) -> None:
        self.left_nodes.append(node)
        node.add_right_node(self)

    def add_right_node(self, node: SpaceSpecifier) -> None:
        self.right_nodes.append(node)
        node.add_left_node(self)

    def _has_horizontal_fixed_position(self) -> bool:
        return self.left_fixed_position is not None or self.right_fixed_position is not None


class SpaceMaster:
    def __init__(self):
        self.specifiers: list[SpaceSpecifier] = []

    def add_specifier(self, specifier: SpaceSpecifier):
        self.specifiers.append(specifier)
