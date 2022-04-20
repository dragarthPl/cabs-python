import inspect
from typing import Any, Dict

from fastapi.params import Depends


class DependencyResolver:
    dependency_cache: Dict[str, Any]

    def __init__(self):
        self.dependency_cache = {}

    def resolve_dependency(self, container: Any):
        container_key = str(container)
        if container_key in self.dependency_cache:
            return self.dependency_cache[container_key]
        if isinstance(container, (Depends,)):
            new_container = container.dependency()
            if inspect.isgenerator(new_container):
                new_generator = next(new_container)
                self.dependency_cache[container_key] = new_generator
                return new_generator
            for name, parameter in inspect.signature(new_container.__init__).parameters.items():
                if parameter.default and isinstance(parameter.default, (Depends,)):
                    new_container.__dict__[name] = self.resolve_dependency(parameter.default)
            self.dependency_cache[container_key] = new_container
            return new_container
        elif inspect.isclass(container) or callable(container):
            return self.resolve_dependency(container())
        elif inspect.isgenerator(container):
            new_generator = next(container)
            self.dependency_cache[container_key] = new_generator
            return next(new_generator)
