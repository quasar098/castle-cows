from pygame import draw, Rect, Surface, font, event as pyevent, constants as pygame, mouse
from numpy import clip as clamp
from typing import Union
from yugo_tools import cserp
# noinspection PyUnresolvedReferences
from pygamepopups import add_debug_popup


cows_popups = []
COWS_POPUP_FONT: Union[font.Font, None] = None


def add_popup(info: str):
    global COWS_POPUP_FONT
    if COWS_POPUP_FONT is None:
        COWS_POPUP_FONT = font.SysFont("Arial", 25)
    if len(cows_popups) < 10:  # 10 popups max
        cows_popups.append(CowsPopup(info))


class CowsPopup:
    def __init__(self, message: str, duration: int = 5):
        self.message = COWS_POPUP_FONT.render(message, True, (0, 0, 0))
        self.anim = 0
        self.duration = duration
        self.rect = Rect((0, 0, 1, 1))


cows_popups: list[CowsPopup]


def handle_cows_popups(event: pyevent.Event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            for popup in cows_popups.__reversed__():
                if popup.rect.collidepoint(mouse.get_pos()):
                    if popup.anim < popup.duration:
                        popup.anim = popup.duration
                        break


def draw_cows_popups(screen: Surface, framerate: int):
    for count, popup in enumerate(cows_popups):
        count = 0
        p_width, p_height, inflation = 400, 100, 12
        width, height = screen.get_size()
        count -= 1 - cserp(clamp(popup.anim*2, 0, 1)) + cserp(clamp(popup.anim, popup.duration, popup.duration+1)-popup.duration)*(p_height+10)/p_height
        popup.anim += 1/framerate
        popup_rect = Rect((width/2-p_width/2, 10+count*(p_height+10), p_width, p_height))
        popup.rect = popup_rect
        draw.rect(screen, (0, 0, 0), popup_rect.inflate(inflation, inflation), border_radius=int(20+inflation/2))
        draw.rect(screen, (255, 255, 255), popup_rect, border_radius=20)
        screen.blit(popup.message, popup.message.get_rect(center=popup_rect.center))
        if popup.anim > popup.duration+1:
            cows_popups.remove(popup)
