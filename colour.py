import random

# 0 blend is the first colour, 1 blend is second colour
def blendColours(col1, col2, blend):
    if blend > 1:
        blend = 1
    elif blend < 0:
        blend = 0
    # get difference
    r = (col1[0] - col2[0]) * blend
    g = (col1[1] - col2[1]) * blend
    b = (col1[2] - col2[2]) * blend
    
    if r < 0:
        r += 255
    if g < 0:
        g += 255
    if b < 0:
        b += 255
    
    return r, g, b

def randColour (inclusive=True):
    if inclusive:
        return random.randrange(0,255), random.randrange(0,255), random.randrange(0,255)
    else:
        return random.randint(0,255), random.randint(0,255), random.randint(0,255)