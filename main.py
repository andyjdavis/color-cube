import os, pygame
from pygame.locals import *

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

import math
import random

def pos_to_top_left(pos, size):
    return (pos[0] - (size[0]/2), pos[1] - (size[1]/2))

def pos_to_rect(pos, size):
    (x, y) = pos_to_top_left(pos, size)
    return pygame.Rect(x, y, size[0], size[1])

def color_average(c1, c2):
    return ( (c1[0]+c2[0])/2, (c1[1]+c2[1])/2, (c1[2]+c2[2])/2,)

class Globals:
    
    def __init__(self):
        self.width = 800
        self.height = 600

        self.level = 1
        self.time = 0
        
        self.block_size = (40,40)
        self.block_jump = -7
        self.block_move = 3
        self.gravity = 0.2
        
        self.player_border_width = 4
        self.player_start_color = (0, 0, 0)
        
        self.platform_thickness = 5
        self.platform_color = (127,127,127)

        #self.text_antialias = 1
        #self.text_color = (255, 255, 255)
        #self.text_bg_color = (0, 0, 0)
        
        self.state_splash = False
        self.state_playing = True
        self.state_between_levels = False

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, vel, color, size, player=False):
        pygame.sprite.Sprite.__init__(self)
        
        self.pos_previous = [pos[0],pos[1]]
        self.pos = [pos[0],pos[1]]
        self.vel = [vel[0],vel[1]]
        self.color = color
        self.size  = size
        self.player = player
        self.sitting_on = False
        
        self.image = pygame.Surface(size).convert()
        #platforms dont call update() so fill their image here
        self.image.fill(self.color)
        
        self.rect = pos_to_rect(self.pos, self.size)
    
    def over(self, platform):
        was_above = (self.pos_previous[1] + self.size[1]/2) <= (platform.pos[1] - platform.size[1]/2)
        is_above = (self.pos[1] + self.size[1]/2) <= (platform.pos[1] - platform.size[1]/2)
        return was_above or is_above
    
    def __revert_pos(self, stop, i):
        self.pos = list(self.pos_previous)
        if (stop):
            self.vel[i] = 0
        else:
            self.vel[i] = -self.vel[0]
    
    def update(self):
        # record the old position before we start changing stuff
        self.pos_previous = list(self.pos)
        
        if not self.sitting_on:
            self.vel[1] += g.gravity
        
        self.pos[0] = int( math.floor( self.pos[0] + self.vel[0] ) )
        self.pos[1] = int( math.floor( self.pos[1] + self.vel[1] ) )
        
        # check if the player has moved off a platform
        if (self.player and self.sitting_on):
            offleft = (self.pos[0] + self.size[0]/2) < (self.sitting_on.pos[0] - self.sitting_on.size[0]/2)
            offright = (self.pos[0] - self.size[0]/2) > (self.sitting_on.pos[0] + self.sitting_on.size[0]/2)
            over = (self.pos[1] + self.size[1]/2) - (self.sitting_on.pos[1] - self.sitting_on.size[1]/2)
            
            if offleft or offright or over != 0:
                self.sitting_on = False
        
        # stop sprites leaving the screen
        if (self.pos[0] - self.size[0]/2) < 0:
            self.__revert_pos(self.player, 0)
        elif (self.pos[0] + self.size[0]/2) > g.width:
            self.__revert_pos(self.player, 0)
        elif (self.pos[1] - self.size[1]/2) < 0:
            self.__revert_pos(True, 1)
        elif (self.pos[1] + self.size[1]/2) > g.height:
            self.__revert_pos(True, 1)
        else:
            # stop nonplayer blocks running off the end of platforms
            if not self.player and self.sitting_on:
                if (self.pos[0] + self.size[0]/2 > self.sitting_on.pos[0] + self.sitting_on.size[0]/2
                or self.pos[0] - self.size[0]/2 < self.sitting_on.pos[0] - self.sitting_on.size[0]/2):
                    self.vel[0] *= -1
            
        self.rect = pos_to_rect(self.pos, self.size)
        if (self.player):
            self.image.fill((255,255,255))
            r_pos = (g.player_border_width, g.player_border_width)
            r_size = (g.block_size[0] - 2*g.player_border_width, g.block_size[1] - 2*g.player_border_width)
            r = Rect(r_pos, r_size)
            pygame.draw.rect(self.image, self.color, r)
        else:
            self.image.fill(self.color)

g = Globals()

pygame.init()
screen = pygame.display.set_mode((g.width, g.height))
pygame.display.set_caption('Blocks')
pygame.mouse.set_visible(0)

player_block = None
exit = None

block_group = pygame.sprite.RenderPlain()
platform_group = pygame.sprite.RenderPlain()
barrier_group = pygame.sprite.RenderPlain()

def group_collide(group, s, dokill=False):
    return pygame.sprite.spritecollide(s, group, dokill)

def group_group_collide(group1, group2, dokill=False):
    return pygame.sprite.groupcollide(group1, group2, dokill, dokill)

def key_down(k):
    #if not g.playing:
        #return

    if k == K_LEFT and player_block:
        player_block.vel[0] -= g.block_move
    elif k == K_RIGHT and player_block:
        player_block.vel[0] += g.block_move
    elif k == K_SPACE and player_block and player_block.vel[1] == 0:
        player_block.vel[1] = g.block_jump
        player_block.sitting = False

def key_up(k):
    #if not g.playing:
        #return

    if k == K_LEFT and player_block:
        player_block.vel[0] += g.block_move
        if (player_block.vel[0] > 0):
            player_block.vel[0] = 0
    elif k == K_RIGHT and player_block:
        player_block.vel[0] -= g.block_move
        if (player_block.vel[0] < 0):
            player_block.vel[0] = 0

def setup_level(level):
    global player_block, exit
    
    block_group.empty()
    platform_group.empty()
    barrier_group.empty()
    
    # some defaults levels can override
    exit_color = (255, 255, 255)
    exit_size = (50, 75)
    exit_pos = (g.width - exit_size[0]/2 - 10, g.height - exit_size[1]/2)
    
    barrier_color = (0, 0, 255)
    
    player_color = g.player_start_color
    player_pos = (g.width/7, 25)
    
    zero_vel = (0,0)
    spacing = 3 * g.block_size[1] # platform spacing
    
    level = 2
    if level == 1:
        barrier_color = (0, 0, 255)
        
        pos = (20, g.height - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 2:
        barrier_color = (0, 0, 255)
        
        pos = (20, g.height - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width - 40, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (20, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 3:
        pos = (g.width - 30, g.height - 2 * spacing - g.block_size[1]/2)
        vel = (-1,0)
        block = Sprite(pos, vel, (0,0,255), g.block_size)
        block_group.add(block)
        
        pos = (g.width/2, g.height - g.block_size[1]/2)
        vel = (-2,0)
        block = Sprite(pos, vel, (255,255,0), g.block_size)
        block_group.add(block)
        
        # purple barrier
        barrier_color = (127, 0, 127)
    elif level == 4:
        pos = (g.width/8, g.height - 3 * spacing - g.block_size[1]/2)
        vel = (2,0)
        block = Sprite(pos, vel, (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width - 30, g.height - 2 * spacing - g.block_size[1]/2)
        vel = (-1,0)
        block = Sprite(pos, vel, (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/2, g.height - g.block_size[1]/2)
        vel = (-2,0)
        block = Sprite(pos, vel, (0,0,255), g.block_size)
        block_group.add(block)
        
        # purple barrier
        barrier_color = (127, 0, 127)
        
    player_block = Sprite(player_pos, zero_vel, player_color, g.block_size, True)
    
    exit = Sprite(exit_pos, zero_vel, exit_color, exit_size)
    
    last_y = None
    barrier_width = 3 * (g.width/7)
    for platform_y in range(spacing, g.height, spacing):
        pos = (barrier_width/2, platform_y)
        platform = Sprite(pos, zero_vel, g.platform_color, (barrier_width , g.platform_thickness))
        platform_group.add(platform)
        
        pos = (g.width - barrier_width/2, platform_y)
        platform = Sprite(pos, zero_vel, g.platform_color, (barrier_width , g.platform_thickness))
        platform_group.add(platform)
        
        last_y = platform_y

    # the barrier to the exit
    barrier_size = (5, spacing)
    barrier_pos = (g.width - 2* exit_size[0], g.height - barrier_size[1]/2)
    barrier = Sprite(barrier_pos, zero_vel, barrier_color, barrier_size)
    barrier_group.add(barrier)
    
    # a platform along the bottom of the screen
    pos = (g.width/2, g.height - g.platform_thickness/2)
    platform = Sprite(pos, zero_vel, g.platform_color, (g.width, g.platform_thickness))
    platform_group.add(platform)

def main():
    clock = pygame.time.Clock()
    
    bg = pygame.Surface(screen.get_size()).convert()
    bg.fill((0,0,0))
    
    setup_level(g.level)

    while 1:
        clock.tick(60)
        g.time += 1
        
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
                else:
                    key_down(event.key)
            elif event.type == KEYUP:
                key_up(event.key)

        if g.state_playing:
            #platforms, barriers and exits dont move so dont have to call update()
            block_group.update()
            
            # Any any blocks on a platform?
            hits = group_group_collide(block_group, platform_group)
            if ( len(hits) > 0):
                for block in hits:
                    platform = hits[block][0]
                    if block.sitting_on != platform:
                        block.vel[1] = 0
                        if block.pos[1] < platform.pos[1]:
                            block.sitting_on = platform
                            block.pos[1] = platform.pos[1] - platform.size[1]/2 - block.size[1]/2
                
            # have any blocks hit a barrier?
            hits = group_group_collide(block_group, barrier_group)
            if ( len(hits) > 0):
                for block in hits:
                    barrier = hits[block][0]
                    if block.color != barrier.color:
                        # block cannot pass through
                        block.vel[0] *= -1
                        block.pos[0] = barrier.pos[0] - barrier.size[0]/2 - block.size[0]/2
            
            if player_block:
                player_block.update()
                
                # did the player touch a block?
                hits = group_collide(block_group, player_block, True)
                for block in hits:
                    #block.vel[0] *= -1
                    if player_block.color == g.player_start_color:
                        player_block.color = block.color
                    else:
                        player_block.color = color_average(player_block.color, block.color)
                
                
                # did the player touch a platform?
                hits = group_collide(platform_group, player_block)
                if ( len(hits) > 0):
                    for platform in hits:
                        if player_block.over(platform):
                            player_block.vel[1] = 0
                            player_block.sitting_on = platform
                            player_block.pos[1] = platform.pos[1] - platform.size[1]/2 - player_block.size[1]/2
                
                # did the player touch a barrier?
                hits = group_collide(barrier_group, player_block)
                if ( len(hits) > 0):
                    for barrier in hits:
                        if player_block.color != barrier.color:
                            # player cannot pass through
                            player_block.vel[0] = 0
                            player_block.pos[0] = barrier.pos[0] - barrier.size[0]/2 - player_block.size[0]/2
                
                # has the player reached the exit?
                if player_block.rect.colliderect(exit.rect):
                    # player has reached the exit
                    g.level += 1
                    setup_level(g.level)
            
        screen.blit(bg, (0, 0))
        
        if exit:
            draw_pos = pos_to_top_left(exit.pos, exit.size)
            screen.blit(exit.image, draw_pos)
        block_group.draw(screen)
        barrier_group.draw(screen)
        platform_group.draw(screen)
        
        if player_block:
            draw_pos = pos_to_top_left(player_block.pos, player_block.size)
            screen.blit(player_block.image, draw_pos)
        
        pygame.display.flip()

if __name__ == '__main__': main()

