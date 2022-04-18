import inspect
from typing import Any

from fastapi.params import Depends


def resolve_dependency(container: Any):
    if isinstance(container, (Depends,)):
        container = container.dependency()
        if inspect.isgenerator(container):
            return next(container)
        for name, parameter in inspect.signature(container.__init__).parameters.items():
            if parameter.default and isinstance(parameter.default, (Depends,)):
                container.__dict__[name] = resolve_dependency(parameter.default)
        return container
    elif inspect.isclass(container) or callable(container):
        return resolve_dependency(container())
    elif inspect.isgenerator(container):
        return next(container)