#!/usr/bin/env python3

from pages import page_index, start_page


if __name__ == '__main__':
    page = start_page
    context = {}

    while True:
        try:
            ctx = page.process(context)
            context.update(ctx)
            next_page = page.next()
            if not next_page:
                break
            
            page = page_index[next_page]()
            
        except Exception as e:
            print(e)
            break
