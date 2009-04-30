

def parity(seq):
    for i, item in enumerate(seq):
        if i % 2 == 1:
            yield 'even', item
        else:
            yield 'odd', item
