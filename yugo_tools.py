import pygame
from typing import Any, Union, Callable
from numpy import clip as clamp, pi, cos
from os import getcwd
from os.path import join
from time import perf_counter as perftime

# yugo tools version 1

YUGO_FRAMERATE = 60
looping = False
images_storage: dict[str, pygame.Surface] = {}
texts_storage: dict[str, pygame.Surface] = {}
last_time = 0


def debug_time(name):
    global last_time
    new = perftime()
    diff = new-last_time
    print(diff, name)  # do not delete!
    last_time = new
    return diff


def fetch_text(text: str, font: pygame.font.Font):
    if not texts_storage.__contains__(text):
        texts_storage[text] = font.render(text, True, (0, 0, 0))
    return texts_storage[text]


def round_to(to_what: Union[int, float], amount: [int, float]) -> Union[float, int]:
    """Round a number to the nearest number of the other number
    Important: the number you're rounding to is first"""
    return round(amount*(1/to_what))*to_what


def set_yugo_framerate(amount: int) -> int:
    """Set the framerate of the yugo library items
    Returns the integer passed in"""
    global YUGO_FRAMERATE
    YUGO_FRAMERATE = amount
    return YUGO_FRAMERATE


def get_image(path: str, scale: Union[tuple[int, int], tuple[float, float]] = (1, 1), rot: float = 0):
    """Much faster implementation to fetch images because of my fetch text method
    Basically, whenever a texture is needed, it is fetched once before being stored in a dictionary for later use
    The path is relative to the current working directory, meaning C:/Users/susy.png wont be found even if there.
    For example: a path of images/logo.png would actually start from the current working dir"""
    global images_storage
    path_thing = f"{path}|{scale}|{rot}"
    if not images_storage.__contains__(path_thing):
        try:
            images_storage[path_thing] = pygame.image.load(join(getcwd(), path)).convert_alpha()
        except FileNotFoundError:
            images_storage[path_thing] = pygame.Surface((250, 325), pygame.SRCALPHA).convert_alpha()
            images_storage[path_thing].fill((0, 0, 0))
            images_storage[path_thing].fill((255, 0, 255), (0, 0, 125, 162))
            images_storage[path_thing].fill((255, 0, 255), (125, 162, 125, 163))
        image = images_storage[path_thing]
        if rot != 0:
            images_storage[path_thing] = pygame.transform.rotozoom(image, int(rot), scale[0]).convert_alpha()
        else:
            images_storage[path_thing] = pygame.transform.scale(image, (int(images_storage[path_thing].get_width()*scale[0]),
                                                                int(images_storage[path_thing].get_height()*scale[1]))).convert_alpha()
    return images_storage[path_thing]


def expand_rect(rect: pygame.Rect, num: int) -> pygame.Rect:
    """Expands the boundaries of a rectangle in a certain amount in each direction
    I.E: Rect(10, 10, 20, 20) expanded 3 would be Rect(7, 7, 23, 23)"""
    return rect.inflate(num, num)


def butter_round(num: float):
    return int(num) if num >= 0 else int(num-1)


def cserp(amount: float, n1=0, n2=1) -> float:
    """Like linear interpolation but instead it follows the curved path of a cosine function
    It is clamped between 0 and 1"""
    return clamp(-0.5*cos(pi*amount)+0.5, 0, 1)*(n2-n1)+n1


def _move_pos(pos: Union[list[int, int], tuple[int, int], tuple[float, float], list[float, float]],
              shift: Union[list[int, int], tuple[int, int], tuple[float, float], list[float, float]]):
    return pos[0]+shift[0], pos[1]+shift[1]


class Text:
    def __init__(self, rect: Union[pygame.Rect, tuple[int, int, int, int], tuple[float, float]],
                 font: pygame.font.Font, text: Any, alignment: str = "center",
                 color: Union[tuple[int, int, int], pygame.Color] = (0, 0, 0), wrap_rect=None):
        """Its a text object.
        Use alignment to determine where the text will be in the rectangle.
        The alignment uses the pygame rect kwargs for alignment."""
        if len(rect) == 2:
            rect = rect[0], rect[1], 1, 1
        self.rect = pygame.Rect(rect)
        self.text_surface = font.render(str(text), True, color)
        if wrap_rect:
            self.rect.w = self.text_surface.get_rect().w
            self.rect.h = self.text_surface.get_rect().h
        self.color = pygame.Color(color)
        self.text = str(text)
        self.font = font
        self.alignment = alignment

    # noinspection PyUnusedLocal
    def draw(self, surface: pygame.Surface) -> None:
        exec(f"surface.blit(self.text_surface, " +
             f"self.text_surface.get_rect({self.alignment}=self.rect.{self.alignment}))")

    def change(self, font: pygame.font.Font = None, text: Any = None,
               color: Union[tuple[int, int, int], pygame.Color] = None) -> None:
        if color is None:
            color = self.color
        if text is None:
            text = self.text
        if font is None:
            font = self.font
        self.color = pygame.Color(color)
        self.font = font
        self.text = str(text)
        self.text_surface = font.render(str(text), True, color)


class Button(Text):
    def __init__(self, rect: Union[pygame.Rect, tuple[float, float, float, float]],
                 font: pygame.font.Font, action: Union[Callable, None] = None, *action_args, text: Any = "",
                 color: Union[tuple[int, int, int], pygame.Color] = (255, 255, 255),
                 secondary_color: Union[tuple[int, int, int], pygame.Color] = (0, 0, 0),
                 pressed_color: Union[tuple[int, int, int], pygame.Color, None] = None):
        super().__init__(rect, font, text)
        self.color = pygame.Color(color)
        self.pressed_color = pygame.Color(pressed_color) if pressed_color is not None else None
        self.secondary_color = pygame.Color(secondary_color)
        self.action = action
        self.action_args = action_args
        self.pressed = False
        """Text with a button that is clickable to trigger a function
        The text alignment is always centered"""

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.secondary_color, expand_rect(self.rect, 4), border_radius=2)
        inside_color = self.color.lerp((0, 0, 0), int(self.pressed)*0.1)
        if self.pressed_color is not None:
            inside_color = self.pressed_color if self.pressed else self.color
        pygame.draw.rect(surface, inside_color,
                         self.rect.move(int(self.pressed), int(self.pressed)), border_radius=2)
        surface.blit(self.text_surface,
                     self.text_surface.get_rect(center=self.rect.center).move(int(self.pressed), int(self.pressed)))

    def change(self, font: pygame.font.Font = None, action: Union[Callable, None] = "NoParam",
               text: Any = None, color: Union[tuple[int, int, int], pygame.Color] = None,
               secondary_color: Union[tuple[int, int, int], pygame.Color] = None) -> None:
        if color is None:
            color = self.color
        if text is None:
            text = self.text
        if font is None:
            font = self.font
        if secondary_color is None:
            secondary_color = self.secondary_color
        if action == "NoParam":
            action = self.action
        self.action = action
        self.color = pygame.Color(color)
        self.secondary_color = pygame.Color(secondary_color)
        self.font = font
        self.text = str(text)
        self.text_surface = font.render(str(text), True, color)

    def handle_events(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(pygame.mouse.get_pos()):
                    self.pressed = True
                    if len(self.action_args) == 0:
                        self.action()
                    else:
                        self.action(*self.action_args)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.pressed = False
        if event.type == pygame.WINDOWLEAVE:
            self.pressed = False


class Switch(Text):
    def __init__(self, rect: Union[pygame.Rect, tuple[int, int, int, int], tuple[float, float]], font: pygame.font.Font,
                 text: Any, color: Union[tuple[int, int, int], pygame.Color] = (255, 255, 255), state: bool = False):
        """A switch which can be either on or off
        It also has text to the right of the switch
        You can get/change the state of the button using Switch.state
        The top left of the switch is positioned at the top left of the rectangle"""
        super().__init__(rect, font, text)
        self.color = pygame.Color(color)
        self.anim = int(state)  # anim is cos interpolated later
        self.state = state

    def change(self, rect: Union[pygame.Rect, tuple[int, int, int, int], tuple[float, float], None] = None,
               font: pygame.font.Font = None, text: Any = None,
               color: Union[tuple[int, int, int], pygame.Color] = None,
               state: Union[bool, None] = None) -> None:
        if color is None:
            color = self.color
        if rect is None:
            rect = self.rect
        if text is None:
            text = self.text
        if font is None:
            font = self.font
        if state is None:
            state = self.state
        self.state = bool(state)
        self.rect = pygame.Rect(rect)
        self.color = pygame.Color(color)
        if (text is not None, font is not None).__contains__(True):
            # if both the font and text are undefined, then redraw the text surface
            self.text_surface = font.render(str(text), True, color)
        self.font = font
        self.text = str(text)

    def draw(self, surface: pygame.Surface) -> None:
        # basics
        anim_speed = 0.07
        on_color = pygame.Color(53, 206, 141)
        off_color = pygame.Color(198, 47, 34)
        rect = pygame.Rect(self.rect.x, self.rect.y, 90, 35)
        slider_width = 0.55  # percentage of width of ^

        self.anim += (int(self.state)*(anim_speed*2)-anim_speed)*(75/YUGO_FRAMERATE)
        self.anim = clamp(self.anim, 0, 1)
        pygame.draw.rect(surface, (0, 0, 0),
                         expand_rect(rect, 6), border_radius=6)  # border
        pygame.draw.rect(surface, self.color, rect, border_radius=4)  # inside rect
        margin = 3
        pygame.draw.rect(surface, pygame.Color(149, 150, 157).lerp(self.color, 0.7),
                         pygame.Rect(rect.x+margin, rect.y+margin, rect.w-margin*2, rect.h-margin*2), border_radius=3)
        # slider indent
        pygame.draw.rect(surface, off_color.lerp(on_color, cserp(self.anim)),
                         pygame.Rect(rect.x+margin, rect.y+margin, rect.w*slider_width-margin*2,
                                     rect.h-margin*2).
                         move((rect.w-(rect.w*slider_width)) * cserp(self.anim), 0), border_radius=3)  # slider
        text_pos = self.text_surface.get_rect(midleft=rect.midright)
        surface.blit(self.text_surface, text_pos.move(13, 0))
        pass

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if pygame.Rect(self.rect.x, self.rect.y, 90, 35).collidepoint(pygame.mouse.get_pos()):
                    self.state = not self.state


class MultipleChoice:
    def __init__(self, rect: Union[pygame.Rect, tuple[int, int, int, int], tuple[float, float]],
                 font: pygame.font.Font, options: list[Any],
                 color: Union[tuple[int, int, int], pygame.Color] = (255, 255, 255)):
        """An element made so the user can choose between multiple items
        Basically a drop down menu
        Text is aligned to the left of the box"""
        if not isinstance(rect, pygame.Rect):  # if it is a tuple or list
            if len(rect) == 2:
                rect = rect[0], rect[1], 250, 50
        self.rect = pygame.Rect(rect)
        self.color = pygame.Color(color)
        self.font = font
        if len(options) == 0:
            self.options: dict[str, pygame.Surface] = {"-": font.render("-", True, (0, 0, 0))}
        else:
            self.options: dict[str, pygame.Surface] = {}
        self.selecting_option = False
        for option in options:
            self.options[option] = font.render(str(option), True, (0, 0, 0))
        self.selected_option = "-"
        if len(options) > 0:
            self.selected_option = options[0]  # will select the first option by default

    def change(self, rect: Union[pygame.Rect, tuple[int, int, int, int], tuple[float, float], None] = None,
               font: Union[pygame.font.Font, None] = None, options: Union[list[str], None] = None,
               color: Union[tuple[int, int, int], pygame.Color] = (255, 255, 255),
               selected_option: str = None) -> None:
        if rect is None:
            rect = self.rect
        else:
            if not isinstance(rect, pygame.Rect):  # if it is a tuple or list
                if len(rect) == 2:
                    rect = rect[0], rect[1], 250, 50
        if font is None:
            font = self.font
        if options is None:
            options = list(self.options.keys())
        if color is None:
            color = self.color
        if selected_option is None:
            selected_option = self.selected_option
        self.color = pygame.Color(color)
        self.rect = pygame.Rect(rect)
        if (font is not None, options is not None).__contains__(True):
            # either the font or options have changed so all the text surfaces will get redrawn
            if len(self.options) == 0:
                self.options: dict[str, pygame.Surface] = {"-": font.render("-", True, (0, 0, 0))}
            else:
                self.options: dict[str, pygame.Surface] = {}
            for option in options:
                self.options[option] = font.render(str(option), True, (0, 0, 0))
        self.selected_option = selected_option
        self.font = font

    def draw(self, surface: pygame.Surface) -> None:
        secondary_color = pygame.Color(0, 0, 0)
        pygame.draw.rect(surface, secondary_color, expand_rect(self.rect, 6), border_radius=6)
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        surface.blit(self.options[self.selected_option],
                     self.options[self.selected_option].get_rect(midleft=(self.rect.left+9, self.rect.centery)))
        arrow_head = _move_pos(self.rect.midright, (-self.rect.h/2, 5))
        pygame.draw.line(surface, secondary_color, arrow_head, _move_pos(arrow_head, (-10, -10)), 4)
        pygame.draw.line(surface, secondary_color, arrow_head, _move_pos(arrow_head, (10, -10)), 4)

    def draw_select(self, surface: pygame.Surface) -> None:
        if self.selecting_option:
            options_rect = pygame.Rect(self.rect.x, self.rect.y,
                                       self.rect.w, (self.font.get_height()+4)*len(self.options)+8)
            pygame.draw.rect(surface, (0, 0, 0), expand_rect(options_rect, -4), border_radius=3)
            pygame.draw.rect(surface, self.color, expand_rect(options_rect, -8), border_radius=2)
            for count, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x+4, self.rect.y+(self.font.get_height()+4)*count+4,
                                          self.rect.w-8, self.options[option].get_rect().h+4)
                if option_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surface, pygame.Color(149, 150, 157).lerp(self.color, 0.7), option_rect)
                surface.blit(self.options[option], option_rect.topleft)

    def handle_events(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # lmb pressed down
                if not self.selecting_option:
                    if self.rect.collidepoint(pygame.mouse.get_pos()):
                        self.selecting_option = True
                else:  # register clicks on drop down menu
                    for count, option in enumerate(self.options):
                        option_rect = pygame.Rect(self.rect.x+4, self.rect.y+(self.font.get_height()+4)*count+4,
                                                  self.rect.w-8, self.options[option].get_rect().h+4)
                        if option_rect.collidepoint(pygame.mouse.get_pos()):
                            self.selected_option = option
                    self.selecting_option = False
                    return True
        if event.type == pygame.WINDOWLEAVE:
            self.selecting_option = False
        return False


class InputBox:
    def __init__(self, rect: Union[pygame.Rect, tuple[int, int, int, int]],
                 font: pygame.font.Font,
                 allowed_chars: Union[str, list[str]] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/()" +
                                                        "_=-1234567890#$%^&*!?,.<>;':'\"\\|[]{}`~ ",
                 color: Union[tuple[int, int, int], pygame.Color] = (255, 255, 255),
                 text_if_no_text: str = "Enter this"):
        self.text_if_no_text = text_if_no_text
        self.rect = pygame.Rect(rect)
        self.font = font
        self.caret = pygame.Surface((4, font.get_height()), pygame.SRCALPHA)
        self.caret.fill((0, 0, 0))
        self.allowed = allowed_chars
        self.color = pygame.Color(color)
        self.text_if_no_text_surf = font.render(text_if_no_text, True,
                                                pygame.Color((149, 150, 157)).lerp(self.color, 0.4))
        self.text = ""
        self.text_surf = pygame.Surface((1, 1))
        self.text_surf.fill(self.color)
        self.selected = False
        self.time_since_last_clicked = 0

    def redraw_surface(self) -> None:
        self.text_surf = self.font.render(self.text, True, (0, 0, 0))

    def change(self, rect: Union[pygame.Rect, tuple[int, int, int, int], None] = None,
               font: Union[pygame.font.Font, None] = None,
               allowed_chars: Union[str, list[str], None] = None,
               text: Union[str, None] = None,
               color: Union[tuple[int, int, int], pygame.Color, None] = None,
               text_if_no_text: Union[None, str] = None) -> None:
        if rect is None:
            rect = self.rect
        if allowed_chars is None:
            allowed_chars = self.allowed
        if color is None:
            color = self.color
        self.color = pygame.Color(color)
        if isinstance(allowed_chars, (list, tuple)):
            if isinstance(allowed_chars, tuple):
                allowed_chars = list(allowed_chars)
            self.allowed = "".join(allowed_chars)
        else:
            self.allowed = allowed_chars
        self.rect = pygame.Rect(rect)
        if (text is not None, font is not None).__contains__(True):
            self.text = text
            self.font = font
            self.redraw_surface()
        if text_if_no_text is not None:
            self.text_if_no_text_surf = font.render(text_if_no_text, True,
                                                    pygame.Color((149, 150, 157)).lerp(self.color, 0.4))
            self.text_if_no_text = text_if_no_text

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (0, 0, 0), expand_rect(self.rect, 6), border_radius=6)
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(surface, pygame.Color((149, 150, 157)).lerp(self.color, 0.6), self.rect, border_radius=4)
            pygame.draw.rect(surface, self.color, expand_rect(self.rect, -7), border_radius=4)
        if len(self.text) == 0 and not self.selected:
            surface.blit(self.text_if_no_text_surf,
                         self.text_if_no_text_surf.get_rect(midleft=_move_pos(self.rect.midleft, (10, 0))))
        else:
            surf_rect = self.text_surf.get_rect(midleft=_move_pos(self.rect.midleft, (10, 0)))
            surface.blit(pygame.transform.chop(self.text_surf,
                                               (0, 0, clamp(self.text_surf.get_width()-self.rect.w+20, 0, 190123), 0)),
                         surf_rect)
            if self.selected:
                self.caret.set_alpha((cos(self.time_since_last_clicked*6)+1)*126)
                surface.blit(self.caret, self.caret.get_rect(midleft=(clamp(surf_rect.right, self.rect.left, self.rect.w-15+self.rect.left),
                                                                      surf_rect.centery)))
        self.time_since_last_clicked += 1/YUGO_FRAMERATE

    def handle_events(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_IBEAM)
            else:
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(pygame.mouse.get_pos()):
                    self.selected = True
                    self.time_since_last_clicked = 0
                    return True
                else:
                    self.selected = False
        if event.type == pygame.TEXTINPUT:
            if self.selected:
                if event.text in self.allowed:
                    self.text += event.text
                    self.redraw_surface()
                self.time_since_last_clicked = 0
                return True
        if event.type == pygame.KEYDOWN:
            if self.selected:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    self.redraw_surface()
                self.time_since_last_clicked = 0
                return True
        if event.type == pygame.WINDOWLEAVE:
            self.selected = False
        return False
