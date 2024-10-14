from .base import Page

class IndexPage(Page):
    def process(self, context: dict) -> dict:
        return context
    
    def next(self):
        return ''
