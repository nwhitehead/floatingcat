'''
Easily generate combinations for testing

'''

def simple_iterator(lst):
    '''Simple iterator for a list'''
    for x in lst: yield x

def combinations_aux(args):
    '''Helper generator for combinations from list of lists'''
    if len(args) == 1:
        for x in args[0]:
            yield (x, )
    else:
        for x in args[0]:
            for y in combinations_aux(args[1:]):
                yield (x, ) + y

def combinations(*args):
    '''Generate combination tuples of elements from each argument
    
    Normal use:
        for x, y, z in combinations([1, 2, 3], [4, 5], ['red', 'green']):
            print x, y, z

    This will iterate over all permutations of choices, where
        x in [1, 2, 3]
        y in [4, 5]
        z in ['red', 'green']
    '''
    if len(args) == 1:
        return simple_iterator(args[0])
    else:
        return combinations_aux(args)
