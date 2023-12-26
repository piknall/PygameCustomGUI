from __future__ import annotations

import abc
import typing


class Dimensions:
    def __init__(self,
                 position: tuple[int, int] = None,
                 size: tuple[int, int] = None,
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

    def get_position(self) -> tuple[int, int]:
        return self._position

    def get_size(self) -> tuple[int, int]:
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
            master: GuiMaster,
            left_nodes: typing.Iterable[SpaceSpecifier] | None,
            right_nodes: typing.Iterable[SpaceSpecifier] | None,
            min_width: int = 0,
            max_width: int | None = None,
            priority: tuple[int, int] | None = None,
            grow_rate: int | float | None = None,
            left_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
            right_fixed_position: None | PositionValueSpecifier | int | typing.Callable[[], int] | float | str = None,
    ):
        super().__init__()

        self.master = master
        self.master.add_specifier(self)

        if isinstance(left_fixed_position, PositionValueSpecifier) or left_fixed_position is None:
            self.left_fixed_position = left_fixed_position
        else:
            self.left_fixed_position = PositionValueSpecifier(left_fixed_position, master)

        if isinstance(right_fixed_position, PositionValueSpecifier) or right_fixed_position is None:
            self.right_fixed_position = right_fixed_position
        else:
            self.right_fixed_position = PositionValueSpecifier(right_fixed_position, master, horizontal=True)

        self.horizontal_fixed_position = self._has_horizontal_fixed_position()

        self.left_nodes: list[SpaceSpecifier] = []
        self.right_nodes: list[SpaceSpecifier] = []
        if left_nodes is not None:
            for node in left_nodes:
                self.add_left_node(node)
        if right_nodes is not None:
            for node in right_nodes:
                self.add_right_node(node)

        self.min_width = min_width
        self.max_width = max_width if max_width is not None else float("inf")
        self.sizable = self.min_width < self.max_width

        self.priority = priority
        if self.sizable and self.priority is None:
            raise ValueError("a priority has to be set for sizable spaces")
        self.grow_rate = None
        self.set_grow_rate(grow_rate)
        if self.sizable and self.grow_rate is None:
            raise ValueError("a grow_rate has to be set for sizable spaces")

    def add_left_node(self, node: SpaceSpecifier) -> None:
        if node in self.left_nodes:
            return None
        self.left_nodes.append(node)
        node.add_right_node(self)

    def add_right_node(self, node: SpaceSpecifier) -> None:
        if node in self.left_nodes:
            return None
        self.right_nodes.append(node)
        node.add_left_node(self)

    def _has_horizontal_fixed_position(self) -> bool:
        return self.left_fixed_position is not None or self.right_fixed_position is not None

    def evaluate_horizontal_fixed_position(self) -> None:
        if self.left_fixed_position is not None:
            self.x = self.left_fixed_position.evaluate()
        elif self.right_fixed_position is not None:
            self.right = self.right_fixed_position.evaluate()
        else:
            raise TypeError("the position of a not horizontally fixed specifier is set by the master")

    def set_grow_rate(self, rate: float | int):
        if type(rate) is float:
            def grow_rate_generator():
                current_offset = 0
                while True:
                    needed_step = rate + current_offset
                    grow_step = round(needed_step)
                    current_offset = needed_step - grow_step
                    yield grow_step

            self.grow_rate = grow_rate_generator()

        else:
            self.grow_rate = rate

    def get_horizontal_grow_step(self) -> int:
        if type(self.grow_rate) is int:
            return self.grow_rate

        return next(self.grow_rate)

    def grow_one_horizontal_step(self):
        grow_step = self.get_horizontal_grow_step()

        if self.max_width is not None and self.max_width - self.width < grow_step:
            grow_step = self.max_width - self.width
            if grow_step == 0:
                return False

        self.shift_right(grow_step)
        occupiable_space = self.shift_left(grow_step)

        self.width += occupiable_space

        if occupiable_space < grow_step:
            return False
        else:
            return True

    @staticmethod
    def get_space_between(element1: SpaceSpecifier, element2: SpaceSpecifier) -> int:
        if element1.right <= element2.x:
            return element2.x - element1.right
        elif element2.right <= element1.x:
            return element1.x - element2.right
        else:
            raise ValueError()

    def shift_left(self, steps: int):
        # if self.horizontal_fixed_position:
        #     return 0

        if self.left_fixed_position is None:
            space_to_general_limitation = self.x
        else:
            space_to_general_limitation = self.x - self.left_fixed_position.evaluate()
        left_space_to_gain = min((steps, space_to_general_limitation))

        for node in self.left_nodes:
            space_between = self.get_space_between(self, node)
            if space_between >= left_space_to_gain:
                continue

            element_shift = node.shift_left(left_space_to_gain - space_between)
            total_space_gained = space_between + element_shift

            if total_space_gained < left_space_to_gain:
                left_space_to_gain = total_space_gained

        self.x -= left_space_to_gain
        return left_space_to_gain

    def shift_right(self, steps: int) -> int:
        # if self.horizontal_fixed_position:
        #     return 0

        if self.right_fixed_position is None:
            space_to_general_limitation = self.master.width - self.right
        else:
            space_to_general_limitation = self.right_fixed_position.evaluate() - self.right
        right_space_to_gain = min((steps, space_to_general_limitation))

        for node in self.right_nodes:
            space_between = self.get_space_between(self, node)
            if space_between >= right_space_to_gain:
                continue

            element_shift = node.shift_right(right_space_to_gain - space_between)
            total_space_gained = space_between + element_shift

            if total_space_gained < right_space_to_gain:
                right_space_to_gain = total_space_gained

        self.x += right_space_to_gain
        return right_space_to_gain

    def __str__(self):
        return (f"\n{self.__class__.__name__} object at {hex(id(self))}:\n"
                f"{self._position=}, "
                f"{self._size=}, "
                f"{self.master=}, "
                f"{self.priority=}, "
                f"{self.grow_rate=}, "
                f"{self.sizable=}, "
                f"{self.horizontal_fixed_position=}, "
                f"\n{self.left_nodes=}, "
                f"\n{self.right_nodes=}, "
                f"\n{self.left_fixed_position=}, {self.right_fixed_position=}\n")


class SpaceMaster(Dimensions):
    def __init__(self,
                 position: tuple[int, int],
                 size: tuple[int, int]):
        super().__init__(position, size)

        self.specifiers: list[SpaceSpecifier] = []

    def add_specifier(self, specifier: SpaceSpecifier):
        self.specifiers.append(specifier)

    @abc.abstractmethod
    def set_size(self) -> None:
        pass


class GuiMaster(SpaceMaster):
    def __init__(self,
                 position: tuple[int, int],
                 size: tuple[int, int]):
        super().__init__(position,  size)

    def _initialize_specifiers_horizontally(self) -> bool:
        # set to minimal size:
        for specifier in self.specifiers:
            specifier.width = specifier.min_width

        # set up position:
        unpositioned_specifiers = self.specifiers.copy()

        def position_specifier_vertical(specifier_to_set_position: SpaceSpecifier) -> None:
            if specifier_to_set_position.horizontal_fixed_position:
                specifier_to_set_position.evaluate_horizontal_fixed_position()
                unpositioned_specifiers.remove(specifier_to_set_position)
                return None

            most_left_position = 0

            for node in specifier_to_set_position.left_nodes:
                if node in unpositioned_specifiers:
                    position_specifier_vertical(node)

                if node.right > most_left_position:
                    most_left_position = node.right

            specifier_to_set_position.x = most_left_position
            unpositioned_specifiers.remove(specifier_to_set_position)

        while unpositioned_specifiers:
            position_specifier_vertical(unpositioned_specifiers[0])

        for specifier in self.specifiers:
            for right_node in specifier.right_nodes:
                if specifier.right > right_node.x:
                    return False
        return True

    def _set_space_of_specifiers(self) -> None:
        resizable_specifiers = [element for element in self.specifiers if element.sizable]
        small_number = 0.5 ** 16
        resizable_specifiers.sort(key=lambda element: element.priority[0] + small_number * element.priority[1])

        priority_groups = [[]]
        current_priority_group = resizable_specifiers[0].priority[0]

        for element in resizable_specifiers:
            primary_priority = element.priority[0]
            if current_priority_group != primary_priority:
                priority_groups.append([])
            priority_groups[-1].append(element)

        for priority_group in priority_groups:
            elements_with_space = priority_group.copy()

            while elements_with_space:
                for element in elements_with_space.copy():
                    can_grow = element.grow_one_horizontal_step()

                    if not can_grow:
                        elements_with_space.remove(element)

    def arrange_specifiers(self) -> bool:
        if not self._initialize_specifiers_horizontally():
            return False
        self._set_space_of_specifiers()
        return True

    def set_size(self) -> None:
        pass



if __name__ == "__main__":
    test_master = GuiMaster((0, 0), (1000, 1000))
    element_1 = SpaceSpecifier(test_master,
                               None, None,
                               100, max_width=150, priority=(0, 0), grow_rate=1, left_fixed_position=10)
    element_2 = SpaceSpecifier(test_master,
                               None, None,
                               0, priority=(0, 1), grow_rate=2, left_fixed_position=0)
    element_3 = SpaceSpecifier(test_master,
                               (element_1, element_2), None,
                               max_width=100, priority=(0, 2), grow_rate=3, right_fixed_position=None)
    element_4 = SpaceSpecifier(test_master,
                               (element_3,), None,
                               50, priority=(0, 3), grow_rate=3.5, right_fixed_position="95%")

    for _ in range(10):
        print(element_2.get_horizontal_grow_step())

    test_master.arrange_specifiers()
    print(element_1)
    print(element_2)
    print(element_3)
    print(element_4)

    for i in test_master.specifiers:
        print(i.x, i.width)

    import pygame
    pygame.init()
    pygame.display.init()
    window = pygame.display.set_mode(test_master.get_size(), flags=pygame.RESIZABLE)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.WINDOWRESIZED:
                test_master._size = (event.x, event.y)
                test_master.arrange_specifiers()
            # print(event)

        window.fill((255, 255, 255))
        for count, i in enumerate(test_master.specifiers):
            pygame.draw.rect(window, (255 - count * 50, count * 50, 0), [i.x, count * 50, i.width, 50])

        pygame.display.update()
        clock.tick(60)
