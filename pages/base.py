

class Page:
    '''this interface is implemented by every page
    :process: this method is called to process the page.
        it should take only one parameter, context which contains all
        the current state of the application needed to process the page.
        it should return the current state of the application as context.
        
    :next: this method is called after processing a page to return the url or
        identifier for the next page
    
    NOTE: the seperation of page should make it possible that given the right context,
        the page will always process successfully.
        this will also help in unit testing the application page by page.
    '''
    
    def __init__(self) -> None:
        self.url = ''
        self.session = None
    
    def process(self, context: dict) -> dict:
        raise NotImplementedError
    
    def next(self) -> str:
        raise NotImplementedError
