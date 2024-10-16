

class ValidationError(Exception):
    pass

class Field:
    def __init__(self, *args, **kwargs):
        pass

    def validate(self):
        raise NotImplementedError
    
class SelectField(Field):
    def __init__(self, choices: list, value, *args, required=True, **kwargs):
        self.choices = choices
        self.value = value

    def validate(self):
        if self.value in self.choices:
            return self.value
        return ValidationError(f'value must be one of {self.choices}. {self.value} provided')