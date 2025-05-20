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
                "CRITICAL": logging.CRITICAL,
        }

    @property
    def password_complexities(self) -> dict[str, int]:
        """Faker.misc.password length parameter"""
        return {
                "Low"    : 6,
                "Medium" : 12,
                "High"   : 18,
                "Higher" : 24,
                "Extreme": 30,
                "Random" : -1,  # -1 means random
        }

    @property
    def request_methods(self) -> list[str]:
        return ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

    @property
    def default_template(self) -> dict:
        return {
                "name"       : "Example Template",
                "request"    : {
                        "method": "POST",
                        "url"   : "https://example.com/login",
                },
                "headers"    : {
                        "User-Agent"     : "{{USER_AGENT_user_agent}}",
                        "Content-Type"   : "application/x-www-form-urlencoded",
                        "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                           "image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "origin"         : "https://example.com/login",
                        "referer"        : "https://example.com/login",
                        "cookie"         : "X_CACHE_KEY=3f4f228e5ad64883485655e591ff825c; "
                                           "PHPSESSID=711rqh2poh7ge3porfftrobheu"
                },
                "form_fields": {
                        "firstname"     : "{{PERSON_first_name}}",
                        "lastname"      : "{{PERSON_last_name}}",
                        "street"        : "{{ADDRESS_street_name}}",
                        "city"          : "{{ADDRESS_city}}",
                        "state"         : "{{ADDRESS_state}}",
                        "zipcode"       : "{{ADDRESS_postcode}}",
                        "mobile"        : "{{MISC_password}}",
                        "ccnumb"        : "{{CREDIT_CARD_credit_card_number}}",
                        "mmonth"        : "{{CREDIT_CARD_credit_card_expire}}",
                        "email"         : "{{INTERNET_free_email}}",
                        "cvvz"          : "{{CREDIT_CARD_credit_card_security_code}}",
                        "btnBillingInfo": "1",
                },
                "config"     : {
                        "data_region"        : "BR",
                        "password_complexity": "Random",
                        "request_count"      : 1000,
                        "thread_count"       : 5,
                        "request_delay"      : 0.5,
                },
        }

    @property
    def default_stats(self) -> dict:
        return {
                "requests_sent"        : 0,
                "successful_requests"  : 0,
                "failed_requests"      : 0,
                "server_error_requests": 0,
                "info_requests"        : 0,
                "redirected_requests"  : 0,
                "timed_out_requests"   : 0,
                "start_time"           : None,
                "end_time"             : None,
                "request_rates"        : [],
                "request_times"        : [],
                "response_times"       : []
        }

    @property
    def data_regions(self) -> list[str]:
        locales = [locale.split("_").pop() for locale in AVAILABLE_LOCALES]
        return list(set(locales))

    @staticmethod
    def locale_from_region(region: str) -> str:
        locales = list(filter(lambda x: x.endswith(region), AVAILABLE_LOCALES))
        return locales.pop()
