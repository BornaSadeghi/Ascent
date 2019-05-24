from pygame import *
import spritesheet, math, random, geometry, colour
from gui import Image, Text

mixer.quit()  # somehow, this reduces audio lag
mixer.init(44100, -16, 2, 2048)
init()

'''
states
0: menu
1: help
2: game
3: death screen
'''
STATE = 0

SIZE = 1000, 700
screen = display.set_mode(SIZE)
clock = time.Clock()

WHITE = 255, 255, 255
BLACK = 0, 0, 0
GREY = 150, 150, 150
GREEN = 0, 255, 0
RED = 255, 0, 0
DARKRED = 150, 0, 0
YELLOW = 200, 200, 0
ORANGE = 255, 200, 0
LIGHTBLUE = 140, 210, 255

spriteFileName = "sprites\\"

highScoreFile = "highscore.dat"

titleImage = image.load(spriteFileName + "title.png")
helpScreenImage = image.load(spriteFileName + "help.png")
deathScreenImage = image.load(spriteFileName + "death.png")
gameIcon = image.load(spriteFileName + "icon.png")   
cellSize = 16, 16
# import from spritesheet to list of sprites
sprites = spritesheet.sheetToSpriteArray(spriteFileName + "gamesheet.png", cellSize)

# change caption and icon of window
display.set_caption("Ascent")
display.set_icon(gameIcon)

soundFile = "sounds\\"
music = mixer.music.load(soundFile + "theme.mp3")

pistolShotSound = mixer.Sound(soundFile + "pistol_shot.wav")
pistolReloadSound = mixer.Sound(soundFile + "pistol_reload.wav")
machineGunShotSound = mixer.Sound(soundFile + "machine_shot.wav")
machineGunReloadSound = mixer.Sound(soundFile + "machine_reload.wav")
shotgunShotSound = mixer.Sound(soundFile + "shotgun_shot.wav")
shotgunReloadSound = mixer.Sound(soundFile + "shotgun_reload.wav")
rocketShotSound = mixer.Sound(soundFile + "rocket_shot.wav")
rocketReloadSound = mixer.Sound(soundFile + "rocket_reload.wav")
bulletHitSound = mixer.Sound(soundFile + "bullet_hit.wav")
rocketHitSound = mixer.Sound(soundFile + "rocket_hit.wav")
gunEmptySound = mixer.Sound(soundFile + "gun_empty.wav")
healSound = mixer.Sound(soundFile + "heal.wav")
deathSound = mixer.Sound(soundFile + "death.wav")
spellSound = mixer.Sound(soundFile + "spell_shot.wav")
clickSound = mixer.Sound(soundFile + "click.wav")

TERMINAL_VEL = -15  # max pixels per frame

enemies = []
platforms = []
items = []
projectiles = []
particleEffects = []
bgObjects = []


class Player:

    def __init__(self):
        self.health = 100
        self.rect = Rect(0, 0, 80, 80)
        self.hitbox = Rect(20, 0, 40, 80)
        
        self.velX, self.velY = 0, 0
        self.dir = 0
        
        self.weapon = None
        self.jumping = False
        self.grounded = False
        self.speed = 10
        self.jump = 13
        self.gravityMod = 1
        
        self.sprites = [transform.scale(sprites[i], (self.rect[2], self.rect[3])) for i in range (4)]
        
        self.frame = 0  # current frame of animation
        self.nextFrame = 4  # frames until animation updates

    def update(self):
        self.rect[0] += self.velX * self.speed
        self.rect[1] -= self.velY
        self.velY -= gravity * self.gravityMod
        
        if self.velY < TERMINAL_VEL:  # stops from falling too fast
            self.velY = TERMINAL_VEL
        
        self.hitbox[0] = self.rect[0] + 20
        self.hitbox[1] = self.rect[1]

        # rotate and flip weapon
        if self.weapon != None:
            self.weapon.rect.center = self.rect.centerx - cam.x, self.rect.centery - cam.y 
            weapCenter = self.weapon.rect.center
            self.weapon.framesSinceShot += 1
            
            if mouseY - weapCenter[1] != 0:
                self.weapon.rot = math.degrees(math.atan((mouseX - weapCenter[0]) / (mouseY - weapCenter[1])))
                
            if mouseY < weapCenter[1]:
                self.weapon.rot += 180
            if mouseX < weapCenter[0]:
                self.weapon.flip = True
            else:
                self.weapon.flip = False
        # animate based on movement
        self.nextFrame -= abs(self.velX * self.speed) / 10
        if self.velX != 0 and self.nextFrame <= 0:
            self.frame += 1
            self.nextFrame = 4
            if self.frame > len(self.sprites) - 1:
                self.frame = 0
            
    def draw(self):
        img = self.sprites[self.frame]
        if mouse.get_pos()[0] < self.rect.centerx - cam.x:
            img = transform.flip(img, True, False)
    
        screen.blit(img, (self.rect[0] - cam.x, self.rect[1] - cam.y))
        if self.weapon != None:
            self.weapon.draw()

        
class Weapon:

    def __init__(self, type=0):
        self.rect = Rect(0, 0, 80, 80)
        
        self.type = type
        
        # accuracy is out of 20
        # fireRate is shots per second
        if self.type == 0:  # pistol
            self.fireRate = 8
            self.damage = 20
            self.accuracy = 16
            self.maxAmmo = 12
            self.maxStoredAmmo = 24
            self.automatic = False
            self.shotSound = pistolShotSound
            self.reloadSound = pistolReloadSound
            
        elif self.type == 1:  # machine gun
            self.fireRate = 8
            self.damage = 30
            self.accuracy = 16
            self.maxAmmo = 30
            self.maxStoredAmmo = 90
            self.automatic = True
            self.shotSound = machineGunShotSound
            self.reloadSound = machineGunReloadSound
            
        elif self.type == 2:  # shotgun
            self.fireRate = 1
            self.damage = 15
            self.accuracy = 6
            self.maxAmmo = 8
            self.maxStoredAmmo = 24
            self.automatic = False
            self.shotSound = shotgunShotSound
            self.reloadSound = shotgunReloadSound
            
        elif self.type == 3:  # rocket launcher
            self.fireRate = 0.5
            self.damage = 100
            self.accuracy = 8
            self.maxAmmo = 1
            self.maxStoredAmmo = 6
            self.automatic = False
            self.shotSound = rocketShotSound
            self.reloadSound = rocketReloadSound
        
        self.ammo = self.maxAmmo
        self.storedAmmo = self.maxStoredAmmo  # stored ammo for reloading
        
        self.framesSinceShot = 60 / self.fireRate
        
        self.sprite = transform.scale(sprites[self.type + 4], (self.rect[2], self.rect[3]))
        
        self.flip = False
        self.rot = 0

    def shoot(self):
        if self.framesSinceShot > 60 / self.fireRate and self.ammo > 0:
            self.framesSinceShot = 0
            self.ammo -= 1
            self.shotSound.play()
            
            if self.type == 2:  # shotgun
                numShots = 8
            else:
                numShots = 1
            
            # yellow particles
            pos = self.rect.centerx + cam.x, self.rect.centery + cam.y
            particleEffects.append(ParticleEffect(1, pos, YELLOW, 8, 4, 0.1))
            
            for i in range (numShots):
                # position where shot ends (far off screen)
                x, y = normalize(mouseX - self.rect.centerx, mouseY - self.rect.centery)
                x, y = self.rect.centerx + (x + random.uniform(-1, 1) / self.accuracy) * 1000, self.rect.centery + (y + random.uniform(-1, 1) / self.accuracy) * 1000
                
                if self.type != 3:  # bullets
                    draw.line(screen, (255, 150, 0), self.rect.center, (x, y), 5)
                    for e in enemies:
                        shot = self.rect.centerx - cam.x, self.rect.centery - cam.y
                        enemyRect = e.rect[0] - cam.x, e.rect[1] - cam.y, e.rect[2], e.rect[3]
                        if geometry.lineCollidesRect((self.rect.center, (x, y)), enemyRect):
                            e.health -= self.damage
                            bulletHitSound.play()
                            particleEffects.append(ParticleEffect(self.damage, e.rect.center, DARKRED, 10, 10, 0.2))
                            # knockback from gunshot
                            e.velX += x / 1000
                            e.velY -= y / 1000
                    for p in projectiles:  # destroy spells by shooting them
                        rect = p.rect[0] - cam.x, p.rect[1] - cam.y, p.rect[2], p.rect[3]
                        if geometry.lineCollidesRect((self.rect.center, (x, y)), rect) and p.type == 1:
                            projectiles.remove(p)
                            particleEffects.append(ParticleEffect(50, p.rect.center, GREEN, 8, 8, 0.2))
                else:  # rockets
                    p = Projectile(0, (-(self.rect.centerx - x) / 500, -(self.rect.centery - y) / 500))
                    p.rect[0], p.rect[1] = self.rect[0] + cam.x, self.rect[1] + cam.y
                    p.rot = self.rot
                
                    projectiles.append(p)
                    
        elif self.ammo == 0:
            if self.storedAmmo > 0:  # reload
                if self.storedAmmo < self.maxAmmo:
                    self.ammo += self.storedAmmo
                    self.storedAmmo = 0
                else:
                    self.ammo = self.maxAmmo
                    self.storedAmmo -= self.maxAmmo
                self.reloadSound.play()
            else:  # out of ammo
                gunEmptySound.play()
    
    def draw(self):
        img = self.sprite
        if self.flip:
            img = transform.flip(img, False, True)
        img = transform.rotate(img, self.rot - 90)

        # prevent sprite from shifting when rotated
        center = self.rect.center
        rect = img.get_rect(center=(center))
        
        screen.blit(img, (rect[0], rect[1]))


player = Player()
player.weapon = Weapon()


class Enemy:

    def __init__(self):
        self.rect = Rect(0, 0, 80, 80)
        self.hitbox = self.rect
        
        self.health = 100
        self.speed = 3
        self.velX, self.velY = 0, 0
        self.xDir, self.yDir = 0, 0
        
        self.knockback = 1
        self.grounded = False
        self.jump = 15
        self.damage = 20
        
        self.type = random.randrange(0, 3)
        if self.type == 2:
            self.attackSpeed = 0.34
        else:
            self.attackSpeed = 1  # attacks per second
        
        # different sprite groups
        if self.type == 0:
            self.sprites = [transform.scale(sprites[i], (self.rect[2], self.rect[3])) for i in range (8, 10, 1)]
        elif self.type == 1:
            self.sprites = [transform.scale(sprites[i], (self.rect[2], self.rect[3])) for i in range (10, 12, 1)]
        elif self.type == 2:
            self.sprites = [transform.scale(sprites[i], (self.rect[2], self.rect[3])) for i in range (12, 14, 1)]
            
        self.frame = 0
        self.nextFrame = 4  # counter for animation speed
        self.nextAttack = self.attackSpeed  # counter for attack speed

    def update(self):
        # check if dead
        if self.health <= 0:
            enemies.remove(self)
        
        # follow player and move
        self.rect[0] += self.velX * self.speed
        
        # x direction
        if player.rect[0] - self.rect[0] > 0:
            self.xDir = 1
        elif player.rect[0] - self.rect[0] < 0:
            self.xDir = -1
        else:
            self.xDir = 0
        
        # y direction
        if player.rect[1] - self.rect[1] > 0:
            self.yDir = -1
        elif player.rect[1] - self.rect[1] < 0:
            if self.type == 1:
                if player.rect[1] + player.rect[3] - self.rect[1] < 0:  # check differently for ground enemies
                    self.yDir = 1
            else:
                self.yDir = 1
        else:
            self.yDir = 0
            
        if self.type == 1:  # non-flying enemies
            self.velY -= gravity
            
            if self.grounded and self.yDir == 1:
                self.velY = self.jump
                self.grounded = False
            
        else:  # flying enemies
            self.velY = lerp (self.velY, self.yDir, 20)
            self.rect[1] -= self.velY * self.speed
        
        self.velX = lerp(self.velX, self.xDir, 20)
        
        if self.velY < TERMINAL_VEL:  # terminal velocity
            self.velY = TERMINAL_VEL
            
        if self.type == 1:
            self.rect[1] -= self.velY
        
        #attack player by contact
        if geometry.rectCollision(player.hitbox, self.hitbox) and self.nextAttack > 60 / self.attackSpeed:
            self.nextAttack = 0
            bulletHitSound.play()
            player.health -= self.damage
            player.velX += self.velX * self.knockback
            player.velY += self.velY * self.knockback
            
            particleEffects.append(ParticleEffect(100, player.rect.center, DARKRED, 10, 10, 0.2))
            
        # attack player by "spell" (cybercriminal only)
        if self.type == 2 and self.nextAttack > 60 / self.attackSpeed:
            self.nextAttack = 0
            spellSound.play()
            p = Projectile(1, (self.velX, -self.velY))
            projectiles.append(p)
            p.rect.center = self.rect.center
        self.nextAttack += 1
        
        # animate
        self.nextFrame -= abs(self.velX * self.speed) / 10
        if self.velX != 0 and self.nextFrame <= 0:
            self.frame += 1
            self.nextFrame = 4
            if self.frame > len(self.sprites) - 1:
                self.frame = 0

    def draw(self):
        img = self.sprites[self.frame]
        if self.velX < 0:  # if moving left, flip image over
            img = transform.flip(img, True, False)
        rect = self.hitbox[0] - cam.x, self.hitbox[1] - cam.y, self.hitbox[2], self.hitbox[3] 
        
        screen.blit(img, (self.rect[0] - cam.x, self.rect[1] - cam.y))


class Platform:

    def __init__(self):
        self.rect = Rect (0, 0, 80, 80)
        self.sprite = transform.scale(random.choice((sprites[14], sprites[15])), (self.rect[2], self.rect[3]))
                   
    def collision(self):
        
        playerRect = player.hitbox[0] - cam.x, player.hitbox[1] - cam.y, player.hitbox[2], player.hitbox[3]
        rect = self.rect[0] - cam.x, self.rect[1] - cam.y, self.rect[2], self.rect[3]

        if playerRect[1] + playerRect[3] <= rect[1] and playerRect[1] + playerRect[3] > rect[1] + player.velY:  # if player above platform
            if playerRect[0] >= rect[0] - playerRect[2] and playerRect[0] <= rect[0] + rect[2]:  # if player in platform's x-axis
                player.velY = 0
                player.grounded = True
            else:  # prevent double jump
                player.grounded = False
                
        # check if enemy on platform
        for e in enemies:
            if e.type == 1:  # enemy type must not be flying
                enemyRect = e.hitbox[0] - cam.x, e.hitbox[1] - cam.y, e.hitbox[2], e.hitbox[3]
                
                if enemyRect[1] + enemyRect[3] <= rect[1] and enemyRect[1] + enemyRect[3] > rect[1] + e.velY:  # if enemy above platform
                    if enemyRect[0] >= rect[0] - enemyRect[2] and enemyRect[0] <= rect[0] + rect[2]:
                        e.velY = 0
                        e.grounded = True
                        e.rect[1] -= 1  # stop from falling through
                    else:
                        e.grounded = False
                
    def draw(self):
        screen.blit(self.sprite, (self.rect[0] - cam.x, self.rect[1] - cam.y))


class Item:  # medkits, ammunition, weapons

    def __init__(self):
        self.rect = Rect(0, 0, 80, 80)
        self.type = random.randrange(0, 3)  # 0: medkit, 1: ammo, 2: weapon
        
        if self.type == 2:
            self.weaponType = random.randrange(0, 4)
            self.sprite = transform.scale(sprites[4 + self.weaponType], (self.rect[2], self.rect[3]))
        else:
            self.sprite = transform.scale(sprites[16 + self.type], (self.rect[2], self.rect[3]))
        self.particleEffect = ParticleEffect(2, self.rect.center, YELLOW, 10, 2, -1, 0.01)

    def collect (self):
        global mouseHold
        if geometry.rectCollision(player.hitbox, self.rect):
            if self.type == 0:  # medkit
                player.health = 100
                healSound.play()
            elif self.type == 1:  # ammo
                player.weapon.ammo = player.weapon.maxAmmo
                player.weapon.storedAmmo = player.weapon.maxStoredAmmo
                player.weapon.reloadSound.play()
            else:  # weapon
                mouseHold = False  # prevent automatic weapon firing
                player.weapon = Weapon(self.weaponType)
                player.weapon.reloadSound.play()
            
            items.remove(self)
            particleEffects.remove(self.particleEffect)
        else:
            self.particleEffect.update()

    def draw(self):
        screen.blit(self.sprite, (self.rect[0] - cam.x, self.rect[1] - cam.y))



class Projectile:
    # type 0: missile, type 1: spell
    def __init__(self, type=0, vel=(0, 0)):
        self.rect = Rect(0, 0, 80, 80)
        self.type = type
        
        if type == 0:
            self.damage = 150
            self.range = 300  # damage radius in pixels
            self.speed = 10
            self.sprites = [transform.scale(sprites[18], (self.rect[2], self.rect[3]))]
        elif type == 1:
            self.sprites = [transform.scale(sprites[19 + i], (self.rect[2], self.rect[3])) for i in range (2)]
            self.damage = 10
            self.speed = 6
        
        self.rot = 0
        
        self.frame = 0  # current frame of animation
        self.frameCount = 0
        self.nextFrame = 4  # frames until animation updates
        self.curSprite = self.sprites[0]
        self.velX, self.velY = vel

    def update(self):
        self.rect[0] += self.velX * self.speed
        self.rect[1] += self.velY * self.speed
        
        if self.type == 0:  # missile
            for enemy in enemies:
                if geometry.rectCollision(self.rect, enemy.hitbox):  # if missile hits enemy, do damage to enemies within radius
                    particleEffects.append(ParticleEffect(100, enemy.rect.center, ORANGE, 20, 20, 0.2))
                    rocketHitSound.play()
                    for e in enemies:
                        if dist(self.rect.center, e.hitbox.center) < self.range:
                            e.health -= self.damage
                            particleEffects.append(ParticleEffect(self.damage, e.rect.center, DARKRED, 10, 10, 0.2))
                    projectiles.remove(self)
                    return
        elif self.type == 1:  # spell
            if geometry.rectCollision(self.rect, player.hitbox):
                player.health -= self.damage
                bulletHitSound.play()
                particleEffects.append(ParticleEffect(self.damage, player.rect.center, DARKRED, 10, 10, 0.2))
                player.velX += self.velX
                player.velY += self.velY
                projectiles.remove(self)
                return
        
        # animate
        self.frameCount += 1
        if self.frameCount >= self.nextFrame:
            self.frameCount = 0
            self.frame += 1
            
        if self.frame >= len(self.sprites):
            self.frame = 0
        self.curSprite = self.sprites[self.frame]

    def draw(self):
        if self.type == 0:
            img = transform.rotate(self.curSprite, self.rot - 90)
        else:
            img = self.curSprite
        
        center = self.rect.center
        rect = img.get_rect(center=(center))
        
        screen.blit(img, (rect[0] - cam.x, rect[1] - cam.y))
        

# particles are just rectangles that use physics
class Particle:  # every particle from a particle effect

    def __init__(self, pos, colour=RED, particleSize=4, velRange=10, gravityMod=0.5):
        self.rect = Rect(pos[0], pos[1], particleSize, particleSize)
        self.velX, self.velY = random.randrange(-velRange, velRange), random.randrange(-velRange, velRange)
        
        self.gravityMod = gravityMod
        self.colour = colour

    def update(self):
        self.velY -= gravity * self.gravityMod
        
        self.rect[0] += self.velX
        self.rect[1] -= self.velY

    def draw(self):
        rect = self.rect[0] - cam.x, self.rect[1] - cam.y, self.rect[2], self.rect[3]
        draw.rect(screen, self.colour, rect)

        
class ParticleEffect:

    def __init__(self, particleRate, pos, particleColour=RED, particleSize=10, velRange=8, duration=-1, gravityMod=0.5):
        self.pos = pos
        self.particleSize = particleSize
        self.colour = particleColour
        
        self.velRange = velRange
        self.spawnRate = particleRate
        self.gravityMod = gravityMod
        self.particles = []
        particleEffects.append(self)
        
        self.duration = duration
        # frames since particle effect started
        self.lifetimeFrames = 0
        # frames since last particle appeared
        self.framesSinceGen = 60 / self.spawnRate

    def update (self):
        if self.duration == -1:  # if the effect is infinite
            if self.framesSinceGen >= 60 / self.spawnRate:
                self.framesSinceGen = 0
                self.particles.append(Particle((self.pos[0], self.pos[1]), self.colour, self.particleSize, self.velRange, self.gravityMod))
        else:
            if self.lifetimeFrames >= 60 * self.duration:
                if len(self.particles) == 0:
                    particleEffects.remove(self)
                    return
            elif self.framesSinceGen >= 60 / self.spawnRate:
                self.framesSinceGen = 0
                self.particles.append(Particle((self.pos[0], self.pos[1]), self.colour, self.particleSize, self.velRange))
        
        for p in self.particles:
            if not cull(p.rect, screenRect):
                self.particles.remove(p)
            else:
                p.update()
        
        self.lifetimeFrames += 1
        self.framesSinceGen += 1

    def draw(self):
        for p in self.particles:
            p.draw()


class BackgroundObject:  # clouds and stars

    def __init__(self):
        self.rect = Rect(0, 0, 240, 240)
        self.sprite = transform.scale(sprites[27], (self.rect[2], self.rect[3]))
        
        # intensity of parallax effect (some clouds move slower)
        self.parallax = random.uniform(2, 5)

    def draw(self):
        screen.blit(self.sprite, (self.rect[0] - cam.x / self.parallax, self.rect[1] - cam.y / self.parallax))


class Camera:

    def __init__(self):
        self.x, self.y = 0, 0


cam = Camera()


# heads-up display
class HUD:

    def __init__(self):
        self.healthRect = Rect(0, 0, 160, 160)
        self.healthAngle = math.radians(player.health * 3.6)
        self.healthColour = GREEN
        
        self.weaponRect = Rect(self.healthRect[2] // 2 - 40, self.healthRect[3] // 2 - 40, 80, 80)
        self.ammoRect = Rect(self.weaponRect[0] - 30, self.healthRect[1] + 10, 140, 140)
        self.ammoStoredRect = Rect(self.ammoRect[0] + 10, self.ammoRect[1] + 10, 120, 120)
        self.weaponSprite = transform.scale(player.weapon.sprite, (80, 80))
        
        self.ammoAngle = math.radians(player.weapon.ammo * (360 / player.weapon.ammo))
        self.ammoColour = GREY
        
        self.ammoStoredAngle = math.radians(player.weapon.storedAmmo * (360 / player.weapon.maxStoredAmmo))
        self.ammoStoredColour = RED
        
    def update(self):
        self.healthColour = colour.blendColours(GREEN, RED, player.health / 100)
        self.weaponSprite = transform.scale(player.weapon.sprite, (80, 80))
        self.healthAngle = lerp(self.healthAngle, math.radians(player.health * 3.6), 4)
        if player.weapon.ammo != 0:
            self.ammoAngle = lerp(self.ammoAngle, math.radians(player.weapon.ammo * (360 / player.weapon.maxAmmo)), 4)
        else:
            self.ammoAngle = 0
            
        if player.weapon.storedAmmo != 0:
            self.ammoStoredAngle = lerp(self.ammoStoredAngle, math.radians(player.weapon.storedAmmo * (360 / player.weapon.maxStoredAmmo)), 4)
        else:
            self.ammoStoredAngle = 0
            
    def draw(self):
        draw.circle(screen, BLACK, (self.healthRect.centerx, self.healthRect.centery), self.healthRect[2] // 2)
        draw.arc(screen, self.healthColour, self.healthRect, -self.healthAngle, 0, 10)
        draw.arc(screen, self.ammoColour, self.ammoRect, -self.ammoAngle, 0, 10)
        draw.arc(screen, self.ammoStoredColour, self.ammoStoredRect, -self.ammoStoredAngle, 0, 10)
        screen.blit (self.weaponSprite, self.weaponRect)


hud = HUD()


def dist (p1, p2):
    diffX = p2[0] - p1[0]
    diffY = p2[1] - p1[1]
    return math.sqrt(diffX ** 2 + diffY ** 2)


# normalize a 2D vector
def normalize(x, y):
    magnitude = dist((0, 0), (x, y))
    if magnitude != 0:
        return x / magnitude, y / magnitude
    else:
        return 0, 0


def cull (rect, areaRect):  # returns true if an object at the position should be drawn/collided
    return areaRect[0]-rect[2] <= rect[0] <= areaRect[0]+areaRect[2] and areaRect[1]-rect[3] <= rect[1] <= areaRect[1]+areaRect[3]

# linear interpolation between two values (smoothing)
def lerp (num1, num2, smooth=4):
    num1 += (num2 - num1) / smooth
    if abs(num1) < 0.05:
        num1 = 0
    return num1


def genPlatforms():  # if not enough platforms, generate more outside of screen
    while len(platforms) < numPlatforms:
        p = Platform()
        
        rectLeft = rangeRect[0] - p.rect[2], rangeRect[1] - p.rect[3], SIZE[0], rangeRect[3]
        rectRight = screenRect[0] + SIZE[0], rangeRect[1], SIZE[0], rangeRect[3]
        rectTop = screenRect[0] - p.rect[2], rangeRect[1] - p.rect[3], SIZE[0], SIZE[1]
        rectBottom = screenRect[0], screenRect[1] + SIZE[1], SIZE[0], SIZE[1]
        
        side = random.choice((rectLeft, rectRight, rectTop, rectBottom))  # what side the platform chooses to be on around the screen
        p.rect[0], p.rect[1] = random.randrange(side[0], side[0] + side[2]), random.randrange(side[1], side[1] + side[3])
        platforms.append(p)

        
numBackgroundObjects = 40


def genBackgroundObjects(): # same for background objects
    global altitude
    
    rangeR = int(rangeRect[0] - cam.x), int(rangeRect[1] - cam.y), rangeRect[2], rangeRect[3]
    screenR = int(screenRect[0] - cam.x), int(screenRect[1] - cam.y), screenRect[2], screenRect[3]
    while len(bgObjects) < numBackgroundObjects:
        b = BackgroundObject()
        
        rectLeft = rangeR[0] - b.rect[2], rangeR[1] - b.rect[3], SIZE[0], rangeR[3]
        rectRight = screenR[0] + SIZE[0], rangeR[1], SIZE[0], rangeR[3]
        rectTop = screenR[0] - b.rect[2], rangeR[1] - b.rect[3], SIZE[0], SIZE[1]
        rectBottom = screenR[0], screenR[1] + SIZE[1], SIZE[0], SIZE[1]
        
        side = random.choice((rectLeft, rectRight, rectTop, rectBottom))  # what side the object chooses to be on around the screen
        b.rect[0], b.rect[1] = random.randrange(side[0], side[0] + side[2]) * b.parallax, random.randrange(side[1], side[1] + side[3]) * b.parallax
        
        if altitude > 100:  # replace clouds with stars at a certain point
            b.sprite = transform.scale(sprites[28], (b.rect[2], b.rect[3]))
        
        bgObjects.append(b)
                
        
def genEnemy():
    global enemyFrameCount
    if enemyFrameCount >= 60 / enemySpawnRate:
        e = Enemy()
        enemyFrameCount = 0
        
        rectLeft = rangeRect[0] - e.rect[2], rangeRect[1] - e.rect[3], SIZE[0], rangeRect[3]
        rectRight = screenRect[0] + SIZE[0], rangeRect[1], SIZE[0], rangeRect[3]
        rectTop = screenRect[0] - e.rect[2], rangeRect[1] - e.rect[3], SIZE[0], SIZE[1]
        rectBottom = screenRect[0], screenRect[1] + SIZE[1], SIZE[0], SIZE[1]
            
        side = random.choice((rectLeft, rectRight, rectTop, rectBottom))  # what side the enemy chooses to be on around the screen
        e.rect[0], e.rect[1] = random.randrange(side[0], side[0] + side[2]), random.randrange(side[1], side[1] + side[3])
        enemies.append(e)

        
def genItem():
    global itemFrameCount
    if itemFrameCount >= 60 / itemSpawnRate:
        i = Item()
        itemFrameCount = 0
        
        rectLeft = rangeRect[0] - i.rect[2], rangeRect[1] - i.rect[3], SIZE[0], rangeRect[3]
        rectRight = screenRect[0] + SIZE[0], rangeRect[1], SIZE[0], rangeRect[3]
        rectTop = screenRect[0] - i.rect[2], rangeRect[1] - i.rect[3], SIZE[0], SIZE[1]
        rectBottom = screenRect[0], screenRect[1] + SIZE[1], SIZE[0], SIZE[1]
            
        side = random.choice((rectLeft, rectRight, rectTop, rectBottom))  # what side the enemy chooses to be on around the screen
        i.rect[0], i.rect[1] = random.randrange(side[0], side[0] + side[2]), random.randrange(side[1], side[1] + side[3])
        
        i.particleEffect.pos = i.rect.center
        
        items.append(i)


def getHighScore():
    highScore = int(open(highScoreFile, "r").read())
    return highScore


def setHighScore (score):
    file = open(highScoreFile, "w")
    file.write(str(score))
    file.close()


def resetGame():
    global player, maxAltitude
    player.weapon = Weapon()
    player.health = 100
    player.rect[0], player.rect[1] = 0, 0
    player.velX, player.velY = 0, 0
    player.dir = 0
    player.jumping = False
    cam.x, cam.y = 0, 0
    maxAltitude = 0
    
    enemies.clear()
    items.clear()
    platforms.clear()
    projectiles.clear()
    particleEffects.clear()

    
altitude = -player.rect[1] // 100
gravity = 0.98 - altitude / 1000
minGravity = 0.1
maxGravity = 1.1
minItemSpawnRate = 0.2
maxItemSpawnRate = 4
# for spawning enemies after a certain number of frames
enemyFrameCount = 0
itemFrameCount = 0

maxAltitude = 0

# GUI items

# title screen and help screen
titleRect = SIZE[0] // 2 - 200, 100, 400, 100
titleBanner = Image (titleRect, titleImage)

playButton = Image ((200, 200, 240, 240), sprites[21])
playHitRect = playButton.rect[0], playButton.rect[1] + 40, playButton.rect[2], playButton.rect[3] - 60

quitButton = Image ((SIZE[0] - 200 - 240, 200, 240, 240), sprites[23])
quitHitRect = quitButton.rect[0], quitButton.rect[1] + 40, quitButton.rect[2], quitButton.rect[3] - 60

helpImage = Image ((0, 0, SIZE[0], SIZE[1]), helpScreenImage)
okButton = Image ((550, SIZE[1] - 240, 240, 240), sprites[25])
okHitRect = okButton.rect[0], okButton.rect[1] + 40, okButton.rect[2], okButton.rect[3] - 60

numTitleClouds = 20
titleClouds = [BackgroundObject() for i in range (numTitleClouds)]
for c in titleClouds:
    c.rect[0] = random.randrange(-c.rect[2], SIZE[0])

menuButtons = [playButton, quitButton]

# high score
highScoreText = Text((0, SIZE[1] - 35, 10, 10), "Best height: " + str(getHighScore()) + "m", BLACK, "lucida console", 32)
creditsText = Text((0, 0, 10, 10), "Music, art, and code by Borna Sadeghi", BLACK, "lucida console", 16)

# hud (altitude meter)
altitudeMeter = Text((0, SIZE[1] - 35, 10, 10), "Altitude: " + str(altitude) + "m", GREY, "lucida console", 32)
maxAltitudeText = Text((0, SIZE[1] - 70, 10, 10), "Highest: " + str(maxAltitude) + "m", GREY, "lucida console", 32)
warningText = Text((300, SIZE[1] - 35, 10, 10), "Do not descend any further...", RED, "lucida console", 32)
impendingDeathText = Text((300, SIZE[1] - 35, 10, 10), "That's it. Now you must die.", RED, "lucida console", 32)

# death screen
deathBackground = Image((300, 200, 400, 300), deathScreenImage)
yourHeightText = Text((340, 330, 10, 10), "Your height: " + str(maxAltitude) + "m", BLACK, "lucida console", 32)
deathOkButton = Image ((440, 370, 120, 120), sprites[25])
deathOkHitRect = deathOkButton.rect[0], deathOkButton.rect[1] + 20, deathOkButton.rect[2], deathOkButton.rect[3] - 30

mixer.music.play(-1)

mouseX, mouseY = 0, 0
mouseHold = False
run = True
while run:
    mouseX, mouseY = mouse.get_pos()
    if STATE == 0:  # menu
        mixer.music.unpause()
        screen.fill(LIGHTBLUE)
                
        for c in titleClouds:
            c.rect[1] += c.parallax
            c.draw()
            if c.rect[1] > SIZE[1]:
                c.rect[0] = random.randrange(-c.rect[2], SIZE[0])
                c.rect[1] = -c.rect[3]
        
        titleBanner.draw()
        highScoreText.draw()
        creditsText.draw()
        
        if geometry.inRect((mouseX, mouseY), playHitRect):
            playButton.changeSprite(sprites[22])
        else:
            playButton.changeSprite(sprites[21])
        if geometry.inRect((mouseX, mouseY), quitHitRect):
            quitButton.changeSprite(sprites[24])
        else:
            quitButton.changeSprite(sprites[23])
        
        for b in menuButtons:
            b.draw()
        
        for e in event.get():
            if e.type == MOUSEBUTTONDOWN:
                if geometry.inRect((mouseX, mouseY), playButton.rect):
                    STATE = 1
                elif geometry.inRect((mouseX, mouseY), quitButton.rect):
                    run = False
            if e.type == QUIT:
                run = False
                
    elif STATE == 1:  # help menu
        screen.fill(WHITE)
        
        helpImage.draw()
        okButton.draw()
        
        if geometry.inRect((mouseX, mouseY), okHitRect):
            okButton.changeSprite(sprites[26])
        else:
            okButton.changeSprite(sprites[25])
        
        for e in event.get():
            if e.type == MOUSEBUTTONDOWN:
                if geometry.inRect((mouseX, mouseY), okHitRect):
                    STATE = 2
            if e.type == QUIT:
                run = False
                
    elif STATE == 2:  # game
        mixer.music.pause()
        screen.fill(colour.blendColours(LIGHTBLUE, BLACK, gravity))
        
        if player.health <= 0:
            STATE = 3
            deathSound.play()
        
        altitude = -player.rect[1] // 100
        
        gravity = 0.98 - altitude / 500
        if gravity < minGravity:
            gravity = minGravity
        elif gravity > maxGravity:
            gravity = maxGravity
            
        itemSpawnRate = 2 - (altitude) / 1000
        if itemSpawnRate < minItemSpawnRate:
            itemSpawnRate = minItemSpawnRate
        elif itemSpawnRate > maxItemSpawnRate:
            itemSpawnRate = maxItemSpawnRate
        numPlatforms = 200 * gravity
        # update camera pos with damping
        cam.x = lerp (cam.x, player.rect.centerx - SIZE[0] // 2, 20)
        cam.y = lerp (cam.y, player.rect.centery - SIZE[1] // 2, 20)
        
        rangeRect = int(cam.x - SIZE[0]), int(cam.y - SIZE[1]), SIZE[0] * 3, SIZE[1] * 3  # range of object generation
        screenRect = int(cam.x), int(cam.y), SIZE[0], SIZE[1]
    
        # two seperate loops to stop sprites from flickering
        for b in bgObjects:
            rect = b.rect[0] - cam.x / b.parallax, b.rect[1] - cam.y / b.parallax, b.rect[2], b.rect[3]
            rangeR = rangeRect[0] - cam.x, rangeRect[1] - cam.y, rangeRect[2], rangeRect[3]
            
            if not cull (rect, rangeR):
                bgObjects.remove(b)
                
        for b in bgObjects:
            rect = b.rect[0] - cam.x / b.parallax, b.rect[1] - cam.y / b.parallax, b.rect[2], b.rect[3]
            screenR = screenRect[0] - cam.x, screenRect[1] - cam.y, screenRect[2], screenRect[3]
            if cull (rect, screenR):
                b.draw()
        
        for p in platforms:
            if not cull (p.rect, rangeRect):
                platforms.remove(p)
        for p in platforms:
            if cull(p.rect, screenRect):
                p.collision()
                p.draw()
        
        genPlatforms()
        genBackgroundObjects()
        
        player.velX = lerp (player.velX, player.dir, 8)
        player.update()
        player.draw()
        
        if player.weapon.automatic and mouseHold:  # only for automatic weapons
            player.weapon.shoot()
        if player.jumping and player.grounded:
            player.gravityMod = 0.5
            player.grounded = False
            player.velY = player.jump
        
        for e in enemies:
            if not cull(e.rect, rangeRect):
                enemies.remove(e)
        for e in enemies:
            e.update()
            if cull(e.rect, screenRect):  # cull out off-screen enemies
                e.draw()
    
        for i in items:
            if not cull (i.rect, rangeRect):
                particleEffects.remove(i.particleEffect)
                items.remove(i)
        for i in items:
            if cull(i.rect, screenRect):  # cull out off-screen items
                i.collect()
                i.draw()
        
        for p in projectiles:
            if not cull (p.rect, rangeRect):
                projectiles.remove(p)
        for p in projectiles:
            p.update()
            if cull(p.rect, screenRect):
                p.draw()
        
        for p in particleEffects:
            p.update()
            p.draw()
        
        if altitude > -50:
            enemySpawnRate = 0.3 + altitude / 300  # per second
            if altitude > maxAltitude:
                maxAltitude = altitude
            elif altitude < -25:
                warningText.draw()
        else:  # punish the player for going downwards
            enemySpawnRate = 50

        if enemySpawnRate == 50:
            impendingDeathText.draw()
        
        if enemySpawnRate > 0:
            genEnemy()
        if itemSpawnRate > 0:
            genItem()
        enemyFrameCount += 1
        itemFrameCount += 1
        
        for e in event.get():
            if e.type == KEYDOWN:
                if e.key == K_a:
                    player.dir -= 1
                elif e.key == K_d:
                    player.dir += 1
                elif e.key == K_s:  # falling through obstacles
                    player.rect[1] += 2
                    player.grounded = False
                    
                elif e.key == K_w:
                    player.jumping = True
                    
            elif e.type == KEYUP:
                if e.key == K_a:
                    player.dir += 1
                elif e.key == K_d:
                    player.dir -= 1
                elif e.key == K_w:
                    player.jumping = False
                    player.gravityMod = 1
                    
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 1:
                    if player.weapon.automatic:
                        mouseHold = True
                    else:
                        player.weapon.shoot()
            elif e.type == MOUSEBUTTONUP:
                if e.button == 1:
                    if player.weapon.automatic:
                        mouseHold = False
            if e.type == QUIT:
                run = False
        
        hud.update()
        hud.draw()
        
        altitudeMeter.update("Altitude: " + str(altitude) + "m")
        altitudeMeter.textColour = colour.blendColours(BLACK, WHITE, gravity)
        altitudeMeter.draw()
        
        maxAltitudeText.update("Highest: " + str(maxAltitude) + "m")
        maxAltitudeText.textColour = altitudeMeter.textColour
        maxAltitudeText.draw()
    
    elif STATE == 3:  # death
        deathBackground.draw()
        
        yourHeightText.update("Your height: " + str(maxAltitude) + "m")
        yourHeightText.draw()
        
        if maxAltitude > getHighScore():
            setHighScore(maxAltitude)
            highScoreText.update("Best height: " + str(getHighScore()) + "m")
        
        deathOkButton.draw()
        
        if geometry.inRect((mouseX, mouseY), deathOkHitRect):
            deathOkButton.sprite = sprites[26]
        else:
            deathOkButton.sprite = sprites[25]
        
        for e in event.get():
            if e.type == MOUSEBUTTONDOWN:
                if e.button == 1:
                    if geometry.inRect((mouseX, mouseY), deathOkHitRect):
                        mixer.music.rewind()
                        resetGame() 
                        STATE = 0
            if e.type == QUIT:
                run = False
    display.update()
    clock.tick(60)
