# This is a game called "Color Cube".
#
# Color Cube is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Color Cube is distributed in the hope that it will be useful and maybe even fun,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Color Cube.  If not, see <http://www.gnu.org/licenses/>.
#
# copyright  2013 onwards Andrew Davis
# license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later

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

def color_combine(c1, c2):
    return (c1[0]+c2[0], c1[1]+c2[1], c1[2]+c2[2])

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

        self.text_antialias = 1
        self.text_color = (200, 200, 200)
        self.text_bg_color = (0, 0, 0)
        
        self.state_splash = True
        self.state_playing = False
        self.state_over = False
        
        self.splash_surface = None
        self.end_surface = None
        self.splash_size = (400, 300)

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, vel, color, size, player=False, text=None):
        pygame.sprite.Sprite.__init__(self)
        
        self.pos_previous = [pos[0],pos[1]]
        self.pos = [pos[0],pos[1]]
        self.vel = [vel[0],vel[1]]
        self.color = color
        self.size  = size
        self.player = player
        self.text = text

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
            # Fill with white then draw a smaller rectangle of the player's current color.
            # This is to give the appearance of having a border.
            self.image.fill((255,255,255))
            r_pos = (g.player_border_width, g.player_border_width)
            r_size = (g.block_size[0] - 2*g.player_border_width, g.block_size[1] - 2*g.player_border_width)
            r = Rect(r_pos, r_size)
            pygame.draw.rect(self.image, self.color, r)
        else:
            self.image.fill(self.color)
        
        if (self.text):
            font = pygame.font.SysFont("arial",24)
            t = font.render(self.text, g.text_antialias, (255, 0, 0), self.color)
            self.image.blit(t, (5, 10))

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
    if g.state_splash:
        if k == K_SPACE:
            setup_level(g.level)
            g.state_splash = False
            g.state_playing = True
            return
    elif g.state_over:
        if k == K_SPACE:
            g.level = 1
            setup_level(g.level)
            g.state_over = False
            g.state_playing = True

    if k == K_LEFT and player_block:
        player_block.vel[0] -= g.block_move
    elif k == K_RIGHT and player_block:
        player_block.vel[0] += g.block_move
    elif k == K_SPACE and player_block and player_block.vel[1] == 0:
        player_block.vel[1] = g.block_jump
        player_block.sitting = False
    elif k == K_r:
        setup_level(g.level)

def key_up(k):
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

    exit_color = (255, 255, 255)
    exit_size = (50, 75)
    exit_pos = (g.width - exit_size[0]/2 - 10, g.height - exit_size[1]/2)
    
    barrier_color = (0, 0, 255)
    
    player_color = g.player_start_color
    player_pos = (g.width - (exit_size[0]*3), g.height - 40)
    
    zero_vel = (0,0)
    spacing = 3 * g.block_size[1] # platform spacing

    if level == 1:
        # simple level. just a blue cube and a blue barrier
        barrier_color = (0, 0, 255)
        
        pos = (20, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 2:
        # blue barrier again but now there are cubes you must avoid
        barrier_color = (0, 0, 255)
        
        pos = (20, g.height - 1 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width - 40, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/6, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 3:
        # magenta barrier + red and blue cubes to introduce combining
        barrier_color = (255, 0, 255)
        
        pos = (g.width - 70, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/3, g.height - 1 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (-g.block_move,0), (0, 0, 255), g.block_size)
        block_group.add(block)
    elif level == 4:
        # yellow barrier
        barrier_color = (255, 255, 0)
        
        pos = (g.width - 30, g.height - 1 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (-g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/8, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/3, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 5:
        # magenta barrier + red and blue plus a green cube to avoid
        barrier_color = (255, 0, 255)
        
        pos = (g.width/8, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (-g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width - 90, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/3, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 6:
        # cyan barrier
        barrier_color = (0, 255, 255)
        
        pos = (g.width/8, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width - 100, g.height - 4 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/3, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    elif level == 7:
        # white barrier
        barrier_color = (255, 255, 255)
        
        pos = (g.width/8, g.height - 3 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (255,0,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width - 30, g.height - 2 * spacing - g.block_size[1]/2)
        block = Sprite(pos, (g.block_move,0), (0,255,0), g.block_size)
        block_group.add(block)
        
        pos = (g.width/2, g.height - g.block_size[1]/2)
        block = Sprite(pos, (-g.block_move,0), (0,0,255), g.block_size)
        block_group.add(block)
    else:
        g.state_playing = False
        g.state_over = True
        return

    player_block = Sprite(player_pos, zero_vel, player_color, g.block_size, True)
    
    exit = Sprite(exit_pos, zero_vel, exit_color, exit_size, False, "exit")
    
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

def draw_splash(screen):

    if not g.splash_surface:
        g.splash_surface = pygame.Surface(g.splash_size).convert()

        font = pygame.font.SysFont("arial",24)
        
        text = font.render("Color Cube", g.text_antialias, g.text_color, g.text_bg_color)
        g.splash_surface.blit(text, (10, 20))
        
        font = pygame.font.SysFont("arial", 18)
        
        text = font.render("You are a poor colorless cube looking to escape.", g.text_antialias, g.text_color, g.text_bg_color)
        g.splash_surface.blit(text, (10, 80))
        
        text = font.render("Use the left and right arrows to move.", g.text_antialias, g.text_color, g.text_bg_color)
        g.splash_surface.blit(text, (10, 150))
        
        text = font.render("Space to jump.", g.text_antialias, g.text_color, g.text_bg_color)
        g.splash_surface.blit(text, (10, 180))
        
        text = font.render("r to restart a level.", g.text_antialias, g.text_color, g.text_bg_color)
        g.splash_surface.blit(text, (10, 210))
        
        text = font.render("Press space to begin.", g.text_antialias, g.text_color, g.text_bg_color)
        g.splash_surface.blit(text, (10, 270))
    
    splash_dest_rect = pygame.Rect((g.width/2) - (g.splash_size[0]/2), (g.height/2) - (g.splash_size[1]/2), g.splash_size[0], g.splash_size[1])
    screen.blit(g.splash_surface, splash_dest_rect)

def draw_end_game_screen(screen):

    if not g.end_surface:
        g.end_surface = pygame.Surface(g.splash_size).convert()
        
        font = pygame.font.SysFont("arial",24)
        
        text = font.render("Congratulations! You are truly a human color wheel.", g.text_antialias, g.text_color, g.text_bg_color)
        g.end_surface.blit(text, (10, 20))
        
        text = font.render("Press space to play again", g.text_antialias, g.text_color, g.text_bg_color)
        g.end_surface.blit(text, (10, 80))

    dest_rect = pygame.Rect((g.width/2) - (g.splash_size[0]/2), (g.height/2) - (g.splash_size[1]/2), g.splash_size[0], g.splash_size[1])
    screen.blit(g.end_surface, dest_rect)

def main():
    clock = pygame.time.Clock()
    
    bg = pygame.Surface(screen.get_size()).convert()
    bg.fill((0,0,0))

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

        if g.state_splash:
            draw_splash(screen)
        elif g.state_playing:
            # Updating exit just to get "exit" drawn. There must be a better way.
            exit.update()
            
            #platforms and barriers dont move so dont have to call update()
            block_group.update()
            
            # Are any blocks on a platform?
            hits = group_group_collide(block_group, platform_group)
            if ( len(hits) > 0):
                for block in hits:
                    platform = hits[block][0]
                    if block.sitting_on != platform:
                        block.vel[1] = 0
                        if block.pos[1] < platform.pos[1]:
                            block.sitting_on = platform
                            block.pos[1] = platform.pos[1] - platform.size[1]/2 - block.size[1]/2
            
            # Have any blocks hit a barrier?
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
                
                # Did the player touch a block?
                hits = group_collide(block_group, player_block, True)
                for block in hits:
                    if player_block.color == g.player_start_color:
                        player_block.color = block.color
                    else:
                        player_block.color = color_combine(player_block.color, block.color)
                
                
                # Did the player touch a platform?
                hits = group_collide(platform_group, player_block)
                if ( len(hits) > 0):
                    for platform in hits:
                        if player_block.over(platform):
                            player_block.vel[1] = 0
                            player_block.sitting_on = platform
                            player_block.pos[1] = platform.pos[1] - platform.size[1]/2 - player_block.size[1]/2
                
                # Did the player touch a barrier?
                hits = group_collide(barrier_group, player_block)
                if ( len(hits) > 0):
                    for barrier in hits:
                        if player_block.color != barrier.color:
                            # player cannot pass through
                            player_block.vel[0] = 0
                            player_block.pos[0] = barrier.pos[0] - barrier.size[0]/2 - player_block.size[0]/2
                
                # Has the player reached the exit?
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
        elif g.state_over:
            draw_end_game_screen(screen)

        pygame.display.flip()

if __name__ == '__main__': main()

