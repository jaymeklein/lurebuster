import faker

class LureBusterBackend:

    def __init__(self):
        self.faker = faker.Faker()
        self.faker_providers = []

    def get_faker_providers(self) -> list:
        for provider in self.faker.providers:


if __name__ == '__main__':
    LureBusterBackend().get_faker_providers()