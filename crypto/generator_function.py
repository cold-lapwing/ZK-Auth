def find_g(p):
    for g in range(2,p):
        values = set()
        for x in range(1,p):
            value = pow(g,x,p)
            values.add(value)
        if len(values) == p - 1:
            return g
