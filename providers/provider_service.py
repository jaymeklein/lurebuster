import inspect
import random
from typing import Callable

import faker
from faker.providers import BaseProvider


class ProviderService:
    """Provider Service class used to dynamically manage Faker providers"""
    _parent_methods = {}

    def __init__(self, provider: BaseProvider):
        self._provider = provider
        self._parent_dir = dir(BaseProvider)
        self._available_methods = {}
        self.placeholders = {}

        self._get_provider_methods_info(provider)
        self._get_provider_name()
        self._generate_placeholders()

    @property
    def methods(self) -> dict:
        """Gets the available methods for the current provider"""
        return self._available_methods

    @property
    def get_parent_methods(self) -> dict:
        """Gets the parent methods for the current provider (usually equal across providers)"""
        return self._parent_methods

    def call(self, method: str, *args, **kwargs) -> Callable:
        """
        Calls the given method, passing its args and kwargs

        Example: call('chrome', 20, 21)

        Or kwargs: call('chrome', version_from=20, version_to=21)

        Check 'ProviderService.methods()' for available methods and arguments
        """

        return self._get_callable(method)(*args, **kwargs)

    def _get_provider_name(self):
        full = self._provider.__provider__
        self.name = full.split('.').pop()

    def _get_callable(self, method: str) -> Callable:
        """Gets the callable from the list of non-inherited methods"""
        method_exists = method in list(self._available_methods)

        if not method_exists:
            raise ValueError(f"Method {method} not available")

        return getattr(self._provider, method)

    def _get_provider_methods_info(self, provider):
        """Returns a dictionary of method names with their parameter info for a Faker provider"""

        for name, method in inspect.getmembers(provider, callable):
            if name.startswith('_'):
                continue

            sig = inspect.signature(method)
            if name in self._parent_dir:
                self._parent_methods[name] = self._get_method_params(sig)
                continue

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

    @staticmethod
    def _get_param_type(param):
        param_type = param.annotation
        if param_type is inspect.Parameter.empty:
            return "Any"

        return param_type.__name__

    def _generate_placeholders(self):
        """
        Generates a list of method placeholders that can be used by the user, interpolating data in the payloads

        The first therm before "_" is the name of the provider.

        eg: https://faker.readthedocs.io/en/stable/providers.html

        Example 1: 'The name of the user was {{PERSON_name}}'

        Example 2: 'Her first name is {{PERSON_first_name_female}}, and her last name is {{PERSON_last_name_female}}'

        Example 3 : '{{USER_AGENT_chrome_(1, 10, 14, 18)}}'

        Example 4:
        """
        for method, parameters in self.methods.items():
            parameters = ', '.join(list(parameters.keys()))
            if parameters:
                parameters = f"_({parameters})"

            placeholder = "{{" + f"{self.name.upper()}_{method}" + parameters + "}}"
            self.placeholders[method] = placeholder

    def _get_placeholders_from_string(self, string: str) -> list[str]:
        ...


if __name__ == '__main__':
    faker = faker.Faker()

    # Using any provider from Faker
    random_provider = random.choice(faker.get_providers())

    # Initialize the service
    provider_service = ProviderService(random_provider)

    # Get the provider methods
    methods = list(provider_service.methods.keys())
    random_method = random.choice(methods)

    # Calls any method
    print(f"Calling {random_method}")
    print(provider_service.call(random_method))
