import json
import logging
import threading
import time
from datetime import datetime
from time import perf_counter_ns
from typing import Callable

from requests import ReadTimeout, request

from config.config import Config
from providers.provider_controller import ProviderController

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("lurebuster.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class Backend:
    provider_controller: ProviderController
    config: Config

    templates: dict = {}
    selected_template_name: str = ""
    selected_template: dict = {}
    stats = {}

    on_stats_update: Callable
    on_finish_run: Callable
    register_log: Callable
    stop = False

    request_threads: dict = {}

    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger()
        self.set_provider_controller()
        self.load_templates_file()
        self.load_defaults()

    def register_stats_callback(self, callback):
        """Register a callback function to be called when stats are updated"""
        self.on_stats_update = callback

    def register_finish_run_callback(self, callback):
        """Register a callback function to be called when the attack is finished"""
        self.on_finish_run = callback

    def register_activity_log_callback(self, callback):
        """Register a callback function to be called when generating activity logs"""
        self.register_log = callback

    def start_attack(self, test: bool = False, data: dict = None):
        """Starts sending requests to the target URL."""
        if data.get("data_region") != self.selected_template.get("config", {}).get(
                "data_region"
        ):
            locale = self.config.locale_from_region(data["data_region"])
            self.set_provider_controller(locale)

        self.request_threads = {}

        if test:
            self.loop_requests(0, data, test)
            self.stop = False
            return

        if not self.stats.get("start_time"):
            self.stats["start_time"] = time.time()

        threads = min(data['thread_count'], data['request_count'])
        for i in range(threads):
            thread = threading.Thread(target=self.loop_requests, args=(i, data))
            thread.daemon = True
            thread.start()
            self.request_threads[i] = thread

        for thread in self.request_threads.values():
            thread.join()

        self.stop = False
        self.on_finish_run()
        self.register_log("Attack stopped")

    def loop_requests(self, thread_id: int, data: dict, test: bool = False):
        url = data["url"]
        method = data["method"].lower()
        count = data.get("request_count", 1)
        delay = data.get("request_delay", 0)
        original_headers = self.selected_template.get("headers")
        original_payload = self.selected_template.get("form_fields")

        for _ in range(count):
            headers = self.replace_request_data_placeholders(original_headers.copy())
            payload = self.replace_request_data_placeholders(original_payload.copy())

            if "start_time" not in self.stats or not self.stats["start_time"]:
                self.stats["start_time"] = time.time()

            current_time = time.time() - self.stats["start_time"]
            self.stats["request_times"].append(current_time)
            start = time.perf_counter()
            sent, recv, code = self.send_request(method, url, headers, payload, thread_id)
            elapsed = time.perf_counter() - start
            self.stats['response_times'].append(elapsed)
            self.register_log(f"thread:{thread_id} status:{code} sent:{sent} received:{recv} in {format(elapsed, '.3f')}ms")

            if test or self.stop:  
                return

            if len(self.stats["request_times"]) < 1:
                continue

            recent_times = self.stats["request_times"][-10:]
            if len(recent_times) < 1:
                continue

            time_diff = recent_times[-1] - recent_times[0]
            if time_diff > 0:
                rate = len(recent_times) / time_diff
                self.stats["request_rates"].append((current_time, rate))

            time.sleep(delay)

    def send_request(self, method: str, url: str, headers: dict, payload: dict, thread: int) -> tuple:
        bytes_sent = 0
        bytes_received = 0
        status_code = None

        try:
            response = request(method, url, headers=headers, data=json.dumps(payload), timeout=10)
            bytes_sent, bytes_received = self.get_request_size(response)
            status_code = response.status_code
            if response.status_code in range(100, 200):
                self.stats["info_requests"] += 1

            elif response.status_code in range(200, 300):
                self.stats["successful_requests"] += 1

            elif response.status_code in range(300, 400):
                self.stats["redirected_requests"] += 1

            elif response.status_code in range(400, 500):
                self.stats["failed_requests"] += 1

            elif response.status_code in range(500, 600):
                self.stats["server_error_requests"] += 1

            self.stats["requests_sent"] += 1

        except ReadTimeout:
            self.stats['timed_out_requests'] += 1

        except Exception as e:
            logger.error(f"Thread {thread}: Error sending request: {str(e)}")
            self.stats["requests_sent"] += 1
            self.stats["failed_requests"] += 1

        if self.on_stats_update:
            self.on_stats_update()

        return bytes_sent, bytes_received, status_code

    def replace_request_data_placeholders(self, data: dict | str) -> dict | str:
        """Replaces placeholders in the request data with generated values."""
        if not data:
            return None

        if isinstance(data, str):
            return self.replace_request_data_placeholders(data)

        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.provider_controller.replace_placeholders(
                        value, repeat=True
                )

            elif isinstance(value, dict):
                data[key] = self.replace_request_data_placeholders(value)

        return data

    def stop_threads(self):
        """Stops sending requests to the target URL."""
        self.stop = True
        for thread in self.request_threads.values():
            if thread.is_alive():
                thread.join(1.0)

        if self.stats["end_time"] is None:
            self.stats["end_time"] = time.time()

    def calculate_success_rate(self) -> float:
        success_rate = 0
        if self.stats["requests_sent"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["requests_sent"]) * 100
        return success_rate

    def elapsed_time_str(self, start: float, end: float) -> str:
        elapsed = start - end
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_metrics(self) -> dict:
        success_rate = self.calculate_success_rate()

        date_str = datetime.fromtimestamp(self.stats["start_time"]).strftime(
                "%Y-%m-%d %H:%M"
        )

        elapsed_time = self.elapsed_time_str(self.stats["end_time"], self.stats["start_time"])
        return {
                "date_str"           : date_str,
                "elapsed_time"       : elapsed_time,
                "sent_requests"      : self.stats['requests_sent'],
                "successful_requests": self.stats['successful_requests'],
                "success_rate"       : f"{success_rate:.2f}%",
                "failed_requests"    : self.stats['failed_requests'],
        }

    def load_templates_file(self):
        """Load templates from persistent storage, and sets the first as loaded"""
        try:
            with open("templates.json", "r") as f:
                self.templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.templates.update(self.config.default_template)

        if self.selected_template or not self.templates:
            return

        self.selected_template_name = list(self.templates.keys())[0]
        self.selected_template = self.templates[self.selected_template_name]

    def load_template(self, template_name: str):
        """Loads the template configuration file to the backend"""
        self.selected_template_name = template_name
        self.selected_template = self.templates[template_name]

    def save_template(self, template_name: str, template_data: dict):
        new_name = template_data.get("name")
        if not new_name:
            raise ValueError("Template name is required")

        # if template_name not in self.templates
        self.templates.pop(template_name)
        self.templates[new_name] = template_data

        if self.selected_template_name == template_name:
            self.selected_template_name = new_name
            self.selected_template = template_data

    def delete_template(self, template_name: str):
        self.templates.pop(template_name)
        self.save_templates()

    def save_templates(self):
        """Save templates to persistent storage"""
        with open("templates.json", "w") as file:
            json.dump(self.templates, file, indent=2)

    def set_provider_controller(self, locale: str = "en_US"):
        """Loads the provider cotroller, based on selected locale"""
        self.provider_controller = ProviderController(locale)

    def set_logging_level(self, log_level: str):
        """Sets the application log level"""
        if log_level not in self.config.log_levels:
            raise ValueError(f'Log level "{log_level}" not available.')

        self.logger.setLevel(self.config.log_levels[log_level])

    def load_defaults(self):
        self.stats = self.config.default_stats.copy()
        
        if self.templates:
            self.selected_template_name = list(self.templates.keys())[0]
            self.selected_template = self.templates[self.selected_template_name]
            return
        
        self.selected_template = self.config.default_template.copy()
        self.selected_template_name = self.selected_template["name"]

    def get_request_size(self, response):
        method_len = len(response.request.method)
        url_len = len(response.request.url)
        headers_len = len('\r\n'.join(f'{k}{v}' for k, v in response.request.headers.items()))
        body_len = len(response.request.body) if response.request.body else 0
        return method_len + url_len + headers_len + body_len, len(response.text)


if __name__ == "__main__":
    backend = Backend()
    pass

    # print(backend.provider_controller.replace_placeholders('The name of the user was {{PERSON_name}} {{
    # PERSON_name}}'))
