def format_number(num):
    if num>= 1_000_000_000:
        return (num // 1_000_000_000, 'B')
    elif num >= 1_000_000:
        return (num // 1_000_000, 'M') 
    elif num >= 100_000:
        return (num // 1_000, 'K') 
    else:
        return (num, '')
    
def format_number_v2(num):
    if num>= 1_000_000_000:
        return f'{num // 1_000_000_000}B'
    elif num >= 1_000_000:
        return f'{num // 1_000_000}M'
    elif num >= 100_000:
        return f'{num // 1_000}K'
    else:
        return f'{num}'