import logging
from faker.config import AVAILABLE_LOCALES


class Config:

    def __init__(self): ...

    @property
    def log_levels(self) -> dict[str, int]:
        return {
                "DEBUG"   : logging.DEBUG,
                "INFO"    : logging.INFO,
                "WARNING" : logging.WARNING,
                "ERROR"   : logging.ERROR,
                "CRITICAL": logging.CRITICAL
        }

    @property
    def password_complexities(self) -> dict[str, int]:
        """Faker.misc.password length parameter"""
        return {
                'Low'    : 6,
                'Medium' : 12,
                'High'   : 18,
                'Higher' : 24,
                'Extreme': 30,
                'Random' : -1  # -1 means random
        }

    @property
    def request_methods(self) -> list[str]:
        return ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']

    @property
    def default_template(self) -> dict:
        return {
                "name"        : "Example Template",
                "request_data": {
                        "method": "POST",
                        "url"   : "https://example.com/login",
                },
                "headers"     : {
                        "User-Agent"     : "{{user_agent}}",
                        "Content-Type"   : "application/x-www-form-urlencoded",
                        "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                           "image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5"
                },
                "form_fields" : {
                        "username"    : "{{INTERNET_user_name}}",
                        "password"    : "{{MISC_password}}",
                        "email"       : "{{INTERNET_free_email}}",
                        "address"     : "{{ADDRESS_address}}",
                        "phone_number": "{{PHONE_NUMBER_msisdn}}",
                },
                "config"      : {
                        "data_region"        : "BR",
                        "password_complexity": "Random",
                        "request_count"      : 1000,
                        "thread_count"       : 5,
                        "request_delay"      : 0.5
                }
        }

    @property
    def default_stats(self) -> dict:
        return {
                "requests_sent"      : 0,
                "successful_requests": 0,
                "failed_requests"    : 0,
                "start_time"         : None,
                "end_time"           : None
        }

    @property
    def data_regions(self) -> list[str]:
        locales = [locale.split('_').pop() for locale in AVAILABLE_LOCALES]
        return list(set(locales))

    @staticmethod
    def locale_from_region(region: str) -> str:
        locales = list(filter(lambda x: x.endswith(region), AVAILABLE_LOCALES))
        return locales.pop()


if __name__ == "__main__":
    config = Config()
    print(config.locale_from_region("FR "))
