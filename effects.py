import pygame
from constants import *
from yugo_tools import get_image, cserp, clamp, getcwd
from os.path import join
from numpy import cos, sin
from math import atan2, sqrt, radians, pi
from random import randint as rand, random


channels: list[pygame.mixer.Channel] = []
sounds = {}


def play_sound_path(path: str, vol=0.2):
    if not sounds.__contains__(path):
        sounds[path] = pygame.mixer.Sound(join(getcwd(), path))
    play_sound(sounds[path], vol)


def play_sound(sound: pygame.mixer.Sound, vol=0.2) -> bool:
    """Play a sound
    Returns true if the sound was played
    Returns false if all channels were busy"""
    if len(channels) == 0:
        pygame.mixer.set_num_channels(20)
        for _ in range(9):
            chan = pygame.mixer.Channel(_+1)
            chan.set_volume(0.2)
            channels.append(chan)
    for channel in channels:
        if not channel.get_busy():
            channel.set_volume(vol)
            channel.play(sound)
            return True
    return False


def within_radius(pos1, pos2, radius: float) -> bool:
    def pyth_theorem(p1, p2) -> float:
        dx, dy = p2[0]-p1[0], p2[1]-p1[1]
        return sqrt(pow(dx, 2) + pow(dy, 2))
    if pyth_theorem(pos1, pos2) < radius:
        return True
    return False


class CurrencyParticle:
    def __init__(self, pos: tuple[int, int], currency: int):
        self.x = pos[0]+rand(-20, 20)
        self.y = pos[1]+rand(-20, 20)
        self.gx = 30
        self.gy = pygame.display.get_surface().get_height()-133
        self.angle = 0
        self.velo = 0
        self.speed = rand(120, 200)*0.01
        if not (currency in (DAIRY_DOLLAR, MILK_COUNTER, HAY_COUNTER)):
            raise SyntaxError(f"wrong int, got {currency} instead")
        self.currency = {DAIRY_DOLLAR: "money.png", MILK_COUNTER: "milk.png", HAY_COUNTER: "hay.png"}[currency]
        if self.currency == "milk.png":
            self.gx += 55
        if self.currency == "hay.png":
            self.gx += 110

    def draw(self, surface: pygame.Surface, framerate: int):
        deltatime = 75/framerate
        self.velo += self.speed * deltatime
        self.angle = atan2(self.gy-self.y, self.gx-self.x)
        self.x += cos(self.angle) * self.velo * deltatime * 0.05
        self.y += sin(self.angle) * self.velo * deltatime * 0.05

        # finally, blit the surface and return if the within
        surface.blit(get_image(join("images", self.currency)), (self.x, self.y))
        if within_radius((self.x, self.y), (self.gx, self.gy), 30):
            self.x = self.gx
            self.y = self.gy
            return True
        return False


class CircleParticle:
    def __init__(self, pos: tuple[float, float], color=(94, 252, 141), age=10):
        self.x = pos[0]
        self.y = pos[1]
        self.dx = (random()*2-1)*6
        self.dy = (random()*2-1)*6
        self.color = pygame.Color(color)
        self.age = age

    def draw(self, surface: pygame.Surface, framerate: int):
        deltatime = 75/framerate
        self.age -= 0.2 * deltatime
        self.x += self.dx * deltatime
        self.y += self.dy * deltatime
        self.dx *= 0.97 ** deltatime
        self.dy *= 0.97 ** deltatime
        pygame.draw.circle(surface, self.color.lerp((0, 0, 0), rand(0, 10)*0.02), (self.x, self.y), self.age)
        return self.age < 0


def cserped_pos(pos1, pos2, amount):
    """Clamped"""
    return cserp(amount, pos1[0], pos2[0]), cserp(amount, pos1[1], pos2[1])


class FakeCard:
    def __init__(self, image: str, spos: tuple[int, int], gpos: tuple[int, int],
                 srot=0, grot=0, anim_time: float = 0.3, real_card=None, endsize=None):
        """SPOS = start position
        GPOS = goal position
        anim variable is cserped
        image file is in .\\images\\cards
        for rotational class variables, 0-180 is on the front and 180-360 is on the back"""
        self.sx, self.sy = spos
        self.image = image
        self.gx, self.gy = gpos
        self.srot = srot
        self.grot = grot
        self.anim = 0
        self.anim_time = anim_time
        self.real_card = real_card
        self.endsize = endsize
        self.was_revealed = False

    def draw(self, surface: pygame.Surface, framerate):
        self.anim += (1/self.anim_time)/framerate
        self.anim = clamp(self.anim, 0, 1)
        pos = cserped_pos((self.sx, self.sy), (self.gx, self.gy), clamp(self.anim, 0, 1))
        rot = radians(cserp(self.anim, self.srot, self.grot)/pi)
        if cos(rot*pi) >= 0:
            image = get_image(join("images", "backside.png"), (cos(rot*pi)*0.5, 0.5))
        else:
            image = get_image(join("images", "cards", self.image), (-cos(rot*pi)*0.5, 0.5))
        if self.endsize is None:
            surface.blit(image, image.get_rect(center=(125+pos[0], 162+pos[1])))
        else:
            self.endsize: tuple[int, int]
            scale = cserped_pos((250, 325), self.endsize, self.anim)
            surface.blit(pygame.transform.scale(image, (int(scale[0]), int(scale[1]))), image.get_rect(center=(125+pos[0], 162+pos[1])))
        pass

    def reveal(self, time=None):
        """Turns the card from backside to frontside"""
        if self.anim in (0, 1):
            self.grot = 180
            self.srot = 360
            self.sx = self.gx
            self.sy = self.gy
            if time is not None:
                self.anim_time = time
            self.anim = 0
        self.was_revealed = True

    def get_rect(self):
        """Does not take into account the current rotation of the card"""
        pos = cserped_pos((self.sx, self.sy), (self.gx, self.gy), clamp(self.anim, 0, 1))
        return pygame.Rect(pos[0], pos[1], 250, 325)
