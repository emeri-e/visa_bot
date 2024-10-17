import inspect

class ValidationError(Exception):
    pass

class Field:
    def __init__(self, name: str, required=True, validators=[], **kwargs):
        self.name = name
        self.required = required
        self.validators = validators

    def validate(self, value):
        for validator_fn in self.validators:
            value = validator_fn(value)
        return value
    

class CharField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, value):
        value = super().validate(value)
        if not value and self.required:
            raise ValidationError('this field is required')
        return value
    
class SelectField(Field):
    def __init__(self, choices: list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(choices, list):
            raise ValidationError('choices must be a list instance')
        self.choices = choices
        self.value = None

    def validate(self, value):
        value = super().validate(value)
        if value in self.choices:
            self.value = value
            return self.value
        return ValidationError(f'value must be one of {self.choices}. {value} provided')
    

class BaseForm:
    _valid = False

    def __init__(self, value: dict):
        self.value = value
        self._validated = {}
        self.validate()

    def validate(self):
        fields = inspect.getmembers(self, lambda f: isinstance(f, Field))
        for field_name, field in fields:
            if field_name in self.value.keys():
                value = self.value[field_name]
                self._validated[field.name] = field.validate(value)
            elif field.required:
                raise ValueError(f'{field_name} is required but no value was provided')
        self._valid = True
    
    @property
    def validated_data(self):
        if not self.is_valid:
            raise ValidationError('form has not been validated')
        return self._validated
    
    @property
    def is_valid(self):
        return self._valid
