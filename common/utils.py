from unidecode import unidecode
from drf_spectacular.openapi import AutoSchema


def slugify(value):
    return unidecode(value).lower().replace(' ', '-')


class ModuleTagAutoSchema(AutoSchema):
    def get_tags(self):
        module_path = self.view.__module__
        parts = module_path.split('.')

        if len(parts) >= 2:
            module_name = parts[-2]
            return [module_name.capitalize()]

        return super().get_tags()
