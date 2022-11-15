from __future__ import annotations

from abc import ABCMeta, abstractmethod, ABC
from typing import Generic, TypeVar, Callable, overload, Optional

T = TypeVar('T')
R = TypeVar('R')
U = TypeVar('U')


def require_non_none(obj):
    if obj is None:
        raise AttributeError()
    return obj


class Predicate(Generic[T]):
    predicate_function: Callable[[T], bool]

    def __init__(self, predicate_function: Callable[[T], bool] = None):
        self.predicate_function = predicate_function

    def test(self, t: T) -> bool:
        require_non_none(self.predicate_function)
        return self.predicate_function(t)

    def and_(self, other: Predicate[T]) -> Predicate[T]:
        require_non_none(other)
        return Predicate[T](lambda t: self.test(t) and other.test(t))

    def negate(self) -> Predicate[T]:
        return Predicate[T](lambda t: not self.test(t))

    def or_(self, other: Predicate[T]) -> Predicate[T]:
        require_non_none(other)
        return Predicate[T](lambda t: self.test(t) or other.test(t))

    def is_equal(self, target_ref) -> Predicate[T]:
        return Predicate[T](lambda obj: obj is None if not target_ref else lambda obj: target_ref == obj)

    def not_(self, target: Predicate[T]) -> Predicate[T]:
        require_non_none(target)
        return target.negate()


class Function(Generic[T, R]):
    function: Callable[[T], R]

    def __init__(self, function: Callable[[T], R]):
        self.function = function

    @overload
    def apply(self, t: T) -> R:
        ...

    def apply(self, t: T, u=None) -> R:
        require_non_none(self.function)
        return self.function(t)

    def compose(self, before: Function[T, R]) -> Function[T, R]:
        require_non_none(before)
        return Function[T, R](lambda v: self.apply(before.apply(v)))

    def and_then(self, after: Function[T, R]) -> Function[T, R]:
        require_non_none(after)
        return Function[T, R](lambda t: after.apply(self.apply(t)))

    def identity(self) -> Function[T, T]:
        return Function[T, T](lambda t: t)


class BiFunction(Function[T, R], Generic[T, U, R]):
    bi_function: Callable[[T, U], R]

    def __init__(self, bi_function: Callable[[T, U], R] = None):
        self.bi_function = bi_function

    def apply(self, t: T, u: Optional[U] = None) -> R:
        require_non_none(self.bi_function)
        return self.bi_function(t, u)

    def and_then(self, after: BiFunction[T, U, R]) -> BiFunction[T, U, R]:
        require_non_none(after)
        return BiFunction[T, U, R](lambda t, u: after.apply(self.apply(t, u)))


if __name__ == '__main__':
    print("start")
    assert Predicate[str](lambda _: False).test("abc") is False
    assert BiFunction[int, int, int](lambda a, b: a + b).apply(3, 3) == 6
    print("Done")
