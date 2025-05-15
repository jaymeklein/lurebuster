import json

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


class LureBusterBackend:
    provider_controller: ProviderController = None
    config: Config = None

    templates: dict = {}
    selected_template_name: str = ''
    selected_template: dict = {}

    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger()
        self.set_provider_controller()

    def start_attack(self, test: bool = False):
        """Starts sending requests to the target URL."""

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

        self.templates.pop(template_name)
        self.templates[template_name] = template_data

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


if __name__ == '__main__':
    backend = LureBusterBackend()
    pass
