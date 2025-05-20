import re
from typing import Any, Callable

import faker
from faker.config import AVAILABLE_LOCALES
from providers.provider_service import ProviderService


class ProviderController:
    """Controller responsible for identifying and replacing placeholders on text"""

    providers_services = {}
    providers_services_names = []

    def __init__(self, locale: str = "en_US"):
        self._validate_locale(locale)
        self.faker = faker.Faker(locale=locale)
        self._generate_providers_services()

    def replace_placeholders(self, text: str, repeat: bool = False) -> str:
        placeholders = self._search_placeholders(text)
        placeholders_data = self._get_providers_from_placeholders(placeholders)

        if not placeholders_data:
            return text

        for data in placeholders_data:
            method, parameters = self._get_method_and_parameters_from_placeholder(
                data["placeholder"]
            )
            provider = data["provider"]

            if not method:
                raise ValueError(f"Method {method} not found")

            if repeat:
                text = self._replace_repeat_values(
                    provider, method, parameters, text, data["placeholder"]
                )
                continue

            text = self._replace_no_repeat_values(
                provider, method, parameters, text, data["placeholder"]
            )

        return text

    @staticmethod
    def _validate_locale(locale: str):
        if locale not in AVAILABLE_LOCALES:
            raise ValueError(f'Locale "{locale}" not available.')

    def _generate_providers_services(self):
        """Gets all the available providers for the specified locale, defaults to en_US"""

        all_providers = self.faker.get_providers()
        for provider in all_providers:
            provider_service = ProviderService(provider)
            self.providers_services[provider_service.name.upper()] = provider_service

        self.providers_services_names = list(self.providers_services.keys())

    def _replace_repeat_values(
        self,
        pservice: ProviderService,
        method: str,
        parameters: dict,
        text: str,
        placeholder: str,
    ) -> str:
        """
        Replaces each placeholder occurrence with the same generated value.

        Example:
            Input: 'His name was {{PERSON_name}}, and her name was {{PERSON_name}}'
            Output: 'His name was Lucy Cechtelar, and her name was Lucy Cechtelar'

        Each occurrence gets the same replacement value.
        """
        args = parameters.get("args", [])
        kwargs = parameters.get("kwargs", {})
        pattern = re.escape(placeholder)

        subs = str(pservice.call(method, *args, **kwargs))
        return re.sub(pattern, subs, text)

    def _replace_no_repeat_values(
        self,
        pservice: ProviderService,
        method: str,
        parameters: dict,
        text: str,
        placeholder: str,
    ) -> str:
        """
        Replaces each placeholder occurrence with a new generated value.

        Example:
            Input: 'His name was {{PERSON_name}}, and her name was {{PERSON_name}}'
            Output: 'His name was Lucy Cechtelar, and her name was Adaline Reichel'

        Each occurrence gets a unique replacement value.
        """
        args = parameters.get("args", [])
        kwargs = parameters.get("kwargs", {})
        pattern = re.escape(placeholder)

        def replacement(match):
            return str(pservice.call(method, *args, **kwargs))

        return re.sub(pattern, replacement, text)

    @staticmethod
    def _search_placeholders(text: str) -> list[str]:
        """Searches for all placeholders in the text, using regex, and returns them"""
        return re.findall(r"{{.*?}}", text)

    def _get_providers_from_placeholders(self, placeholders: list[str]) -> list[dict]:
        """Based on the list of existing placeholders, returns a list of valid placeholders"""
        placeholders_and_providers = []

        for placeholder in placeholders:
            clean = self._clear_placeholder(placeholder)
            provider = self._get_provider_from_placeholder(clean)

            if not provider:
                raise ValueError(f"No provider found for placeholder {clean}")

            placeholders_and_providers.append(
                {"placeholder": placeholder, "provider": provider}
            )

        return placeholders_and_providers

    def _get_provider_from_placeholder(self, placeholder: str) -> dict | None:
        """
        Based on the given placeholder, returns the data for it

        Placeholder data includes the provider name, method and parameters
        """

        provider_name = self._provider_name_from_placeholder(placeholder)
        if provider_name is None or provider_name not in self.providers_services_names:
            return None

        return self.providers_services[provider_name]

    @staticmethod
    def _provider_name_from_placeholder(placeholder: str) -> str | None:
        """Based on a clean placeholder, returns the name of the provider, if it exists"""
        provider_name = re.match(r"^([A-Z]+(?:_[A-Z]+)*)", placeholder)

        if not provider_name:
            return None

        groups = provider_name.groups()
        return groups[0]

    def _get_method_and_parameters_from_placeholder(
        self, placeholder: str
    ) -> tuple[Callable, dict] | None:
        clean = self._clear_placeholder(placeholder)
        method_and_parameters = re.match(
            r"[A-Z_0-9]+_([a-z_0-9]+)_*(?:\((.*)\))*", clean
        )

        if not method_and_parameters.groups():
            return None, None

        method = method_and_parameters.groups()[0]
        method = method.replace("_", " ").strip().replace(" ", "_")

        parameters = method_and_parameters.groups()[1]
        if not parameters:
            parameters = ""

        args_and_kwargs = self._get_parameters_from_placeholder(parameters)

        return method, args_and_kwargs

    def _get_parameters_from_placeholder(self, placeholder: str) -> tuple | dict | None:
        """Based on the given placeholder, returns its method parameters"""
        args = []
        kwargs = {}

        placeholder = placeholder.replace(" ", "")
        if not placeholder:
            return {"args": args, "kwargs": kwargs}

        parts = [p.strip() for p in placeholder.split(",")]
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                kwargs[key.strip()] = self._try_convert_number(value.strip())
                continue

            args.append(self._try_convert_number(part.strip()))

        return {"args": args, "kwargs": kwargs}

    @staticmethod
    def _try_convert_number(value: str) -> Any:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    @staticmethod
    def _clear_placeholder(placeholder: str) -> str:
        return placeholder.replace("{{", "").replace("}}", "")


if __name__ == "__main__":
    providers_controller = ProviderController()
    res = providers_controller.replace_placeholders(
        "The name of the user was {{PERSON_name}} {{PERSON_name}}", True
    )
    res = providers_controller.replace_placeholders(
        "The name of the user was {{PERSON_name}} {{PERSON_name}}"
    )
    pass
