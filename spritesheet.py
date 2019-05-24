from pygame import Surface, image, SRCALPHA

images = []

class Spritesheet: # takes in a spritesheet
    def __init__(self, fileName, cellSize):
        self.spritesheet = image.load(fileName).convert_alpha()
        
        self.imageSize = self.spritesheet.get_rect()
        self.cellSize = cellSize

    # crops the image and returns it
    def cropImage(self, x, y, w, h):
        image = Surface((w, h), SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, w, h))
        return image
    
    # splits spritesheet into list of sprites
    def getImageList(self):
        for y in range (0,self.imageSize[3], self.cellSize[0]):
            for x in range (0,self.imageSize[2], self.cellSize[1]):
                images.append(self.cropImage(x,y,self.cellSize[0], self.cellSize[1]))
        return images

def sheetToSpriteArray(fileName, cellSize):
    return Spritesheet(fileName, cellSize).getImageList()