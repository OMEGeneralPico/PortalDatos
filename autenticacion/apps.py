from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    name = 'authentication'

    def ready(self):
        import authentication.signals

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        import core.signals