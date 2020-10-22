#  Simplest form of an evolution simulator
"""

    TO DO LIST:
    X Make an empty pygame window
    X Make a dot that can move randomly
    X Make a food dot that can be consumed
    X Implement Energy
    
    X Give the dots sight
    X Give the dots speed
    X Balance sight and speed with energy
    X Sort out them running off the edge lol  # When hit wall, randomise 10,80 degrees in the direction they are already going away from the wall
    X DUPLICATION
    X Create wondering traits, targetting traits, breeding traits
        X Wandering jitter, wandering turns, wandering patience, wandering speed, sight, breeding energy, passing energy
    - Clickability  (see traits, generation)
        - Generation, Age, Children
    - Legs and eyes!
    - Sprint speed? (when target)
    - Remove bounce? Rely on turning?
    - Let the dots rest?

"""

import pygame
import math
import random

# Constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0,0,180)
GREEN = (0, 180, 0)
RED = (180, 0, 0)
YELLOW = (0,240,240)
GREY = (230,230,230)
PI = math.pi

# Classes

class Creature(pygame.sprite.Sprite):
    def __init__(self, x, y, size, sightDist, speed, startEnergy, breedEnergy, passingEnergy, wanderJit, wanderTurn, wanderPatience, generation, family, environment):
        self.yspeed = 0
        self.xspeed = 0
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([size,size])
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.ellipse(self.image,DarkenCol(BLUE),[0,0,size,size],0)
        pygame.draw.ellipse(self.image,BLUE,[1,1,size-1,size-1],0)

        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = x
        self.radius = size/2

        self.environment = environment
        self.x = x
        self.y = y
        # Angle represents bearing of the creature (From N)
        self.angle = 270
        self.energy = startEnergy
        self.energyTimer = 0
        self.energyUsage = ((speed/10) * (speed/20) + 2 * (sightDist/10)) / 20
        
        self.sightDistance = sightDist
        self.target = None
        self.targetAngle = 0
        self.targetDir = [0,0]
        # Speed given in pixels/second
        self.speed = speed

        self.age = 0
        self.ageCounter = 0
        self.generation = generation
        self.family = family
        self.childCount = 0

        self.breedEnergy = breedEnergy
        self.passingEnergy = passingEnergy

        # Make sure wandering variables CANNOT be less than 1 (randrange will break)
        if wanderJit < 1:
            self.wanderJit = 1
        else:
            self.wanderJit = wanderJit

        if wanderTurn < 1:
            self.wanderTurn = 1
        else:
            self.wanderTurn = wanderTurn

        if wanderPatience < 1:
            self.wanderPatience = 1
        else:
            self.wanderPatience = wanderPatience
            
        #Create sight hitbox
        self.sightBox = SightBox(self,self.sightDistance)
        self.environment.SightBox_List.add(self.sightBox)
    def update(self):
        # Collision with food detection
        food_collision_list = pygame.sprite.spritecollide(self, self.environment.Food_list, False)
        for food in food_collision_list:
            if pygame.sprite.collide_circle(self, food):
                food.eaten = True
                food.kill()
                self.energy += 10

        if self.rect.top <= 0:
            self.CalculateBounce(1)
            self.target = None
        elif self.rect.right >= 1280:
            self.CalculateBounce(2)
            self.target = None
        elif self.rect.bottom >= 720:
            self.CalculateBounce(3)
            self.target = None
        elif self.rect.left <= 0:
            self.CalculateBounce(4)
            self.target = None
        else:
            if self.target:
                if self.target.eaten:
                    self.target = None
            else:
                # Sight
                food_seen_list = pygame.sprite.spritecollide(self.sightBox, self.environment.Food_list, False)
                for food in food_seen_list:
                    if pygame.sprite.collide_circle(self.sightBox, food):
                        self.target = food
                        self.targetDir[0] = self.x+self.radius - food.x
                        self.targetDir[1] = (self.y+self.radius - food.y)
                        
                        self.targetAngle = math.degrees(math.atan2(self.targetDir[1],self.targetDir[0]))
                        # Adjust for what quadrant
                        self.targetAngle = (self.targetAngle-90) % 360
                        
                        self.angle = self.targetAngle % 360

                if not self.target:
                    # Randomise direction
                    if random.randint(0,10) == 0:
                        self.angle += random.randrange(-1*self.wanderJit,self.wanderJit)
                    if random.randint(0,self.wanderPatience) == 0:
                        self.angle += random.randrange(-1*self.wanderTurn,self.wanderTurn)
                    self.angle = self.angle % 360

        
        # Current Speed = 0.66 pixels/tick or 40 p/s
        self.x += (self.speed/60)*math.sin(math.radians(self.angle))
        self.y -= (self.speed/60)*math.cos(math.radians(self.angle))

        

        self.rect.y = self.y
        self.rect.x = self.x

        self.energyTimer += self.energyUsage
        if self.energyTimer > 60:
            self.energyTimer -= 60
            self.energy -= 1
        self.ageCounter += 1
        if self.ageCounter > 60:
            self.ageCounter = 1
            self.age += 1

        # DUPLICATE
        if self.energy >= self.breedEnergy:
            NewCreature = Creature(self.x,self.y,25,
                                   self.sightDistance+random.randint(-3,3),
                                   self.speed+random.randint(-3,3),
                                   self.passingEnergy,
                                   self.breedEnergy+random.randint(-3,3),
                                   self.passingEnergy+random.randint(-3,3),
                                   self.wanderJit+random.randint(-2,2),
                                   self.wanderTurn+random.randint(-4,4),
                                   self.wanderPatience+random.randint(-10,10),
                                   self.generation+1, self.family,
                                   self.environment)
            self.environment.Creature_list.add(NewCreature)
            NewPart = DupeAnim(self.x,self.y)
            self.environment.Decor_List.add(NewPart)
            self.energy -= self.passingEnergy
            self.childCount += 1
        elif self.energy <= 0:
            self.sightBox.kill()
            self.kill()
            

        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.ellipse(self.image,DarkenCol(BLUE),[0,0,self.radius*2,self.radius*2],0)
        pygame.draw.ellipse(self.image,BLUE,[1,1,self.radius*2-1,self.radius*2-1],0)
        font = pygame.font.SysFont('comicsansms',11,True,False)
        text = font.render(str(self.energy),False,WHITE)
        self.image.blit(text, [(self.radius)-(text.get_width()/2) , (self.radius) - (text.get_height()/2)])

    def CalculateBounce(self,side):
        # Sides around 1,2,3,4 as N,E,S,W
        if side == 1:
            if self.angle <= 180:
                self.angle = random.randint(100,170)
            else:
                self.angle = random.randint(190,260)
        elif side == 2:
            if self.angle >= 90:
                self.angle = random.randint(190,260)
            else:
                self.angle = random.randint(280,350)
        elif side == 3:
            if self.angle >= 180:
                self.angle = random.randint(280,350)
            else:
                self.angle = random.randint(10,80)
        elif side == 4:
            if self.angle >= 270:
                self.angle = random.randint(10,80)
            else:
                self.angle = random.randint(100,170)
            
        

        

class SightBox(pygame.sprite.Sprite):
    def __init__(self,creature,radius):
        pygame.sprite.Sprite.__init__(self)

        self.owner = creature
        self.radius = self.owner.sightDistance
        
        self.image = pygame.Surface([self.radius*2,self.radius*2])
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        
        self.rect = self.image.get_rect()
        self.rect.center = creature.rect.center
        pygame.draw.circle(self.image, RED, (self.radius,self.radius), self.radius,1)
        
    def update(self):
        self.rect.center = self.owner.rect.center
    
class Food(pygame.sprite.Sprite):
    def __init__(self,x,y,environment):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([5,5])
        self.image.fill(GREEN)
        self.eaten= False

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.x = x+2
        self.y = y+2
        self.environment = environment
        
class Environment(object):
    def __init__(self,creatures,foods,foodSpawnRate):
        

        self.Food_list = pygame.sprite.Group()
        self.Creature_list = pygame.sprite.Group()
        self.SightBox_List = pygame.sprite.Group()
        self.Decor_List = pygame.sprite.Group()
        self.foodSpawnCount = 0
        self.foodSpawnRate = foodSpawnRate

        for i in range(foods):
            NewFood = Food(random.randint(100,1180),random.randint(80,640),self)
            self.Food_list.add(NewFood)

        for i in range(creatures):
            # The default testing stats were Creature(x,y,25,40,40,80,110,50,15,160,300,self)       size, sightDist, speed, startEnergy, breedEnergy, passingEnergy, wanderJit, wanderTurn, wanderPatience
            NewCreature = Creature(random.randint(300,880),random.randint(230,490),
                                   25,
                                   random.randint(30,65),       # Sight Distance
                                   random.randint(15,80),       # Speed (pix/s)
                                   80,
                                   random.randint(90,140),      # Breeding Energy Limit
                                   random.randint(30,65),       # Passing Energy on breeding
                                   random.randint(5,45),        # Jitter angle
                                   random.randint(100,250),     # Turning angle
                                   random.randint(150,450),     # Wander Patience
                                   1, chr(65+i), self)
            self.Creature_list.add(NewCreature)
    def update(self):
        self.Creature_list.update()
        self.SightBox_List.update()
        self.Decor_List.update()

        self.foodSpawnCount += 1
        if self.foodSpawnCount > self.foodSpawnRate:
            NewFood = Food(random.randint(100,1180),random.randint(80,640),self)
            self.Food_list.add(NewFood)
            self.foodSpawnCount = 1
    def draw(self,screen):
        self.Creature_list.draw(screen)
        self.Food_list.draw(screen)
        self.Decor_List.draw(screen)

class DupeAnim(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)

        self.counter = 1
        self.image = pygame.Surface([60,60])
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)

        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
    def update(self):
        self.counter += 1
        if self.counter >= 60:
            self.kill()
        
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.circle(self.image, BLACK, self.rect.center, self.counter)
        

def DarkenCol(colour):
    r = math.floor(colour[0]*0.6)
    g = math.floor(colour[1]*0.6)
    b = math.floor(colour[2]*0.6)
    return (r,g,b)

def GetClicked(pos,environment):
    clicked = None
    for i in environment.Creature_list:
        if i.rect.collidepoint(pos):
            clicked = i
            break
    return clicked

def main():
    pygame.init()

    size = (1480, 720)
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("EvoSim")

    done = False

    clock = pygame.time.Clock()

    environment = Environment(6,30,40)
    clickedSprite = None
        
    
    # -------- Main Program Loop -----------
    while not done:
        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()

                clickedSprite = GetClicked(pos,environment)
                
                environment.Decor_List.empty()
                if clickedSprite != None:
                    environment.Decor_List.add(clickedSprite.sightBox)
                    print(clickedSprite.family,clickedSprite.generation)
        
        # --- Game logic


        environment.update()
        
        screen.fill(WHITE)
        # --- Drawing
        environment.draw(screen)
        pygame.draw.rect(screen, DarkenCol(GREY), (1280,0,1,710),1)
        pygame.draw.rect(screen, GREY, (1281,0,200,710))
        if clickedSprite != None:
            font = pygame.font.Font('freesansbold.ttf',24)
            text = font.render("Name: " + clickedSprite.family + "-" + str(clickedSprite.generation),False,BLACK)
            screen.blit(text, [1295,30])

            text = font.render("Age: " + str(clickedSprite.age)+"s",False,BLACK)
            screen.blit(text, [1295,60])

            text = font.render("Energy: " + str(clickedSprite.energy),False,BLACK)
            screen.blit(text, [1295,90])

            text = font.render("Sight: " + str(clickedSprite.sightDistance),False,BLACK)
            screen.blit(text, [1295,150])

            text = font.render("Speed: " + str(clickedSprite.speed),False,BLACK)
            screen.blit(text, [1295,180])

            text = font.render("Jitter: " + str(clickedSprite.wanderJit),False,BLACK)
            screen.blit(text, [1295,240])

            text = font.render("Turn: " + str(clickedSprite.wanderTurn),False,BLACK)
            screen.blit(text, [1295,270])

            text = font.render("Patience: " + str(clickedSprite.wanderPatience),False,BLACK)
            screen.blit(text, [1295,300])

            text = font.render("Breed lvl: " + str(clickedSprite.breedEnergy),False,BLACK)
            screen.blit(text, [1295,360])

            text = font.render("Breed pass: " + str(clickedSprite.passingEnergy),False,BLACK)
            screen.blit(text, [1295,390])

            text = font.render("Children: " + str(clickedSprite.childCount),False,BLACK)
            screen.blit(text, [1295,450])

            text = font.render("Children: " + str(clickedSprite.childCount),False,BLACK)
            screen.blit(text, [1295,450])



        pygame.display.flip()
     

        # This program will run at 60 loops per second
        clock.tick(60)
    
    for i in environment.Creature_list:
        print(i.sightDistance,i.speed,i.breedEnergy,i.passingEnergy,i.wanderJit,i.wanderTurn,i.wanderPatience)
        
    pygame.quit()


if __name__ == "__main__":
    main()
