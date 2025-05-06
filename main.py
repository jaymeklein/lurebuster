import time
from threading import Event

import webview
import requests
import random
import string
from faker import Faker
from concurrent.futures import ThreadPoolExecutor
import json

faker = Faker()

data_types = ['string', 'integer', 'json', 'email', 'name', 'address', 'phone', 'user-agent', 'postal-code']


def generate_random_data(data_type):
    match data_type:
        case 'string':
            return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        case 'integer':
            return random.randint(1, 1000000)
        case 'json':
            return json.dumps({random_string(4): random_string(8) for _ in range(3)})
        case 'email':
            return faker.email(domain=faker.domain_name(levels=random.randint(1, 3)))
        case 'name':
            return faker.name()
        case 'address':
            return faker.address()
        case 'postal-code':
            return faker.postal_code()
        case 'phone':
            return faker.phone_number()
        case 'user-agent':
            return faker.user_agent()
    return ''


def random_string(length):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


class Api:
    def __init__(self):
        self.window = None
        self.stopped = Event()
        self.metrics = {
                'start_time' : None,
                'total'      : 0,
                'success'    : 0,
                'errors'     : 0,
                'last_update': time.time()
        }

    def start_attack(self, data):
        try:
            self.stopped.clear()
            self.metrics = {
                    'start_time' : time.time(),
                    'total'      : 0,
                    'success'    : 0,
                    'errors'     : 0,
                    'last_update': time.time()
            }

            url = data['url']
            num_threads = data['numThreads']

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                while not self.stopped.is_set():
                    # Generate fresh parameters for each batch
                    url_params = self._process_params(data['urlParams'])
                    full_url = requests.Request('GET', url, params=url_params).prepare().url

                    futures = []
                    for _ in range(num_threads):
                        futures.append(executor.submit(self.send_request, full_url, data))

                    for future in futures:
                        future.result()

                    self._update_metrics()

        except Exception as e:
            self.window.evaluate_js(f"appendResult('Configuration error: {str(e).replace("'", "\\'")}')")

    def send_request(self, full_url, data):
        if self.stopped.is_set():
            return

        headers = self._process_params(data['headers'])
        post_params = self._process_params(data['postParams'])
        method = data['method'].upper()

        try:
            self.metrics['total'] += 1
            if method in ['POST', 'PUT', 'PATCH']:
                content_type = headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    response = requests.request(method, full_url, headers=headers, json=post_params)
                else:
                    response = requests.request(method, full_url, headers=headers, data=post_params)
            else:
                response = requests.request(method, full_url, headers=headers)

            if 200 <= response.status_code < 300:
                self.metrics['success'] += 1
                try:
                    response = json.loads(response.text)
                    print('Message:', response.get("data", {}).get('message', 'null'))
                    print('ID:', response.get("data", {}).get('ucfid'))
                except:
                    pass
            else:
                self.metrics['errors'] += 1

            # Only update metrics, don't send individual results
            self._update_metrics()

        except Exception as e:
            self.metrics['errors'] += 1
            self._update_metrics()

    def _process_params(self, params):
        result = {}
        for param in params:
            if not param['key']:
                continue

            if param['isJson']:
                try:
                    # Parse existing JSON or generate random JSON
                    if param['random']:
                        value = generate_random_data('json')
                    else:
                        value = json.loads(param['value'])
                    result[param['key']] = value
                except json.JSONDecodeError:
                    result[param['key']] = param['value']
            else:
                if param['random']:
                    value = generate_random_data(param['dataType'])
                else:
                    value = param['value']
                result[param['key']] = value
        return result

    def _update_metrics(self):
        now = time.time()
        if now - self.metrics['last_update'] > 1:
            self.metrics['last_update'] = now
            self.window.evaluate_js(f"updateMetrics({json.dumps(self.get_metrics())})")

    def get_metrics(self):
        duration = time.time() - self.metrics['start_time']
        return {
                'total'   : self.metrics['total'],
                'success' : self.metrics['success'],
                'errors'  : self.metrics['errors'],
                'rps'     : self.metrics['total'] / duration if duration > 0 else 0,
                'duration': duration
        }

    def stop_attack(self):
        self.metrics = {'total': 0, 'success': 0, 'errors': 0, 'rps': 0, 'duration': 0, 'last_update': 0}
        self.stopped.set()
        self._update_metrics()

    def add_row(self, section, key=None, value=None, is_random=False, data_type='string', is_json=False):
        row_id = f'row_{section}_{random.randint(1, 100000)}'
        checked = "checked" if is_random else ""
        json_checked = "checked" if is_json else ""
        selected = lambda dt: "selected" if dt == data_type else ""

        return f"""
        <div class="row" id="{row_id}">
            <input type="text" placeholder="Key" class="param-key" value="{key or ''}">
            <textarea placeholder="Value" class="param-value" rows="">{value or ''}</textarea>
            <label>
                <input type="checkbox" class="random-check" {checked}> Random
            </label>
            <select class="data-type" style="display: {'inline' if is_random else 'none'}">
            {'\n'.join([f'<option value="{option}" {selected(option)}>{option}</option>' for option in data_types])}
            </select>
            <label>
                <input type="checkbox" class="json-check" {json_checked}> Is JSON
            </label>
            <button onclick="removeRow('{row_id}')">Remove</button>
        </div>
        """

    def import_json(self, section, json_str):
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return "Error: JSON must be an object/dictionary"

            html = ""
            for key, value in data.items():
                is_json = isinstance(value, (dict, list))
                value_str = json.dumps(value, indent=2) if is_json else str(value)
                html += self.add_row(
                        section=section,
                        key=key,
                        value=value_str,
                        is_json=is_json,
                        data_type='json' if is_json else 'string'
                )
            return html
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON - {str(e)}"


def main():
    api = Api()
    window = webview.create_window(
            'LureBuster - Anti-Phishing Tool',
            'assets/index.html',
            js_api=api,
            width=900,
            height=700
    )
    api.window = window
    webview.start()


if __name__ == '__main__':
    main()
