import inspect
import random
from typing import Callable

import faker
from faker.providers import BaseProvider


class ProviderService:
    """Provider Service class used to dynamically manage Faker providers"""
    _available_methods = {}
    _parent_methods = dir(BaseProvider)

    def __init__(self, provider: BaseProvider):
        self._provider = provider
        self._get_provider_methods_info(provider)

    def methods(self) -> dict:
        """Gets the available methods for the current provider"""
        return self._available_methods

    def call(self, method: str, *args, **kwargs) -> Callable:
        """
        Calls the given method, passing its args and kwargs

        Example: call('chrome', 20, 21)

        Or kwargs: call('chrome', version_from=20, version_to=21)

        Check 'ProviderService.methods()' for available methods and arguments
        """

        return self._get_callable(method)(*args, **kwargs)

    def _get_callable(self, method: str) -> Callable:
        """Gets the callable from the list of non-inherited methods"""
        method_exists = method in list(self._available_methods)

        if not method_exists:
            raise ValueError(f"Method {method} not available")

        return getattr(self._provider, method)

    def _get_provider_methods_info(self, provider):
        """Returns a dictionary of method names with their parameter info for a Faker provider"""

        for name, method in inspect.getmembers(provider, callable):
            if name.startswith('_') or name in self._parent_methods:
                continue

            sig = inspect.signature(method)
            self._available_methods[name] = self._get_method_params(sig)

    def _get_method_params(self, signature):
        """Get method parameters for a Faker provider"""

        params_info = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue



            default = param.default if param.default is not inspect.Parameter.empty else None
            param_type = self._get_param_type(param)

            params_info[param_name] = {
                    'type'   : param_type,
                    'default': default,
                    'kind'   : str(param.kind)
            }

        return params_info

    def _get_param_type(self, param):
        param_type = param.annotation
        if param_type is inspect.Parameter.empty:
            return "Any"

        return param_type.__name__


if __name__ == '__main__':
    faker = faker.Faker()

    # Using any provider from Faker
    random_provider = random.choice(faker.get_providers())

    # Initialize the service
    provider_service = ProviderService(random_provider)

    # Get the provider methods
    methods = list(provider_service.methods().keys())
    random_method = random.choice(methods)

    # Calls any method
    print(f"Calling {random_method}")
    print(provider_service.call(random_method))