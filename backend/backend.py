import json
import threading
import time
from datetime import datetime
from requests import request

from config.config import Config
from providers.provider_controller import ProviderController
import logging

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
                logging.FileHandler('lurebuster.log'),
                logging.StreamHandler()
        ]
)

logger = logging.getLogger(__name__)


class Backend:
    provider_controller: ProviderController = None
    config: Config = None

    templates: dict = {}
    selected_template_name: str = ''
    selected_template: dict = {}
    stats = {}

    on_stats_update = None
    on_finish_run = None

    request_threads: list[threading.Thread] = []

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
        self.on_finish_run = callback

    def start_attack(self, test: bool = False, data: dict = None):
        """Starts sending requests to the target URL."""
        if data.get('data_region') != self.selected_template.get('config', {}).get('data_region'):
            locale = self.config.locale_from_region(data.get('data_region'))
            self.set_provider_controller(locale)

        self.request_threads = []

        if test:
            self.send_requests(0, data)
            return

        if not self.stats.get("start_time"):
            self.stats['start_time'] = time.time()

        for i in range(data.get('thread_count', 1)):
            thread = threading.Thread(target=self.send_requests, args=(i, data))
            thread.daemon = True
            thread.start()
            self.request_threads.append(thread)

        for thread in self.request_threads:
            thread.join()

        self.on_finish_run()

    def send_requests(self, thread_id: int, data: dict):
        url = data.get('url')
        method = data.get('method').lower()
        count = data.get('request_count', 1)
        delay = data.get('request_delay', 0)
        headers = self.selected_template.get('headers', {})
        form_fields = self.selected_template.get('form_fields', {})

        headers = self.replace_request_data_placeholders(headers)
        form_fields = self.replace_request_data_placeholders(form_fields)

        for _ in range(count):
            current_time = time.time() - self.stats.get("start_time")
            self.stats["request_times"].append(current_time)

            try:
                response = request(method, url, headers=headers, data=form_fields)
                if response.status_code in range(100, 200):
                    self.stats['info_requests'] += 1

                elif response.status_code in range(200, 300):
                    self.stats["successful_requests"] += 1

                elif response.status_code in range(300, 400):
                    self.stats["redirected_requests"] += 1

                elif response.status_code in range(400, 500):
                    self.stats["failed_requests"] += 1

                elif response.status_code in range(500, 600):
                    self.stats["server_error_requests"] += 1

                # Update requests_sent counter
                self.stats["requests_sent"] += 1

                # Call the callback if registered
                if self.on_stats_update:
                    self.on_stats_update()

            except Exception as e:
                logger.error(f"Thread {thread_id}: Error sending request: {str(e)}")
                self.stats["requests_sent"] += 1
                self.stats["failed_requests"] += 1

                # Call the callback if registered
                if self.on_stats_update:
                    self.on_stats_update()

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

    def replace_request_data_placeholders(self, data: dict) -> dict:
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.provider_controller.replace_placeholders(value, repeat=True)

            elif isinstance(value, dict):
                data[key] = self.replace_request_data_placeholders(value)

        return data

    def stop_threads(self):
        for thread in self.request_threads:
            if thread.is_alive():
                thread.join(1.0)

        if self.stats["end_time"] is None:
            self.stats["end_time"] = time.time()

    def add_to_history(self) -> dict:
        elapsed = self.stats["end_time"] - self.stats["start_time"]
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        success_rate = 0
        if self.stats["requests_sent"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["requests_sent"]) * 100

        date_str = datetime.fromtimestamp(self.stats["start_time"]).strftime("%Y-%m-%d %H:%M")
        return {
                'date_str'    : date_str,
                'success_rate': f"{success_rate:.1f}%",
                'time_str'    : time_str
        }

    def load_templates_file(self):
        """Load templates from persistent storage, and sets the first as loaded"""
        try:
            with open('templates.json', 'r') as f:
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
        new_name = template_data.get('name')
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
        with open('templates.json', 'w') as file:
            json.dump(self.templates, file, indent=2)

    def set_provider_controller(self, locale: str = 'en_US'):
        """Loads the provider cotroller, based on selected locale"""
        self.provider_controller = ProviderController(locale)

    def set_logging_level(self, log_level: str):
        """Sets the application log level"""
        if log_level not in self.config.log_levels:
            raise ValueError(f'Log level "{log_level}" not available.')

        self.logger.setLevel(self.config.log_levels[log_level])

    def load_defaults(self):
        self.stats = self.config.default_stats.copy()
        self.selected_template = self.config.default_template.copy()
        self.selected_template_name = self.selected_template.get('name')


if __name__ == '__main__':
    backend = Backend()
    pass

    # print(backend.provider_controller.replace_placeholders('The name of the user was {{PERSON_name}} {{
    # PERSON_name}}'))
