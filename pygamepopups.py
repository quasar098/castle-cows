import pygame
from numpy import clip as clamp, cos, pi
# noinspection PyUnresolvedReferences
from yugo_tools import expand_rect, Text, Switch, MultipleChoice, _move_pos

text_storage: dict[str, pygame.Surface] = {}
sub_text_storage: dict[str, pygame.Surface] = {}
texts_shown = []  # texts at the end are at the bottom
POPUP_WIDTH, POPUP_HEIGHT = 240, 92
POPUP_PADDING = 4


def cserp(min_, max_, amount):
    """Like lerp but with cosine instead of linear"""
    return (cos((clamp(amount, 0, 1)*-1+1)*pi)/2+0.5)*(max_-min_)+min_


def no_action():
    pass


def add_debug_popup(message: str, font: pygame.font.Font = None, time_shown: int = 3, sub_text: str = None,
                    sub_font: pygame.font.Font = None, action=no_action, action_args=None) -> None:
    if font is None:
        font = pygame.font.SysFont("Arial", 20)
    if sub_font is None and sub_text is not None:
        sub_font = pygame.font.SysFont("Arial", 14)
    if not text_storage.__contains__(message):
        text_storage[message] = font.render(message, True, (255, 255, 255))
    if sub_font is not None and sub_text is not None:
        if not sub_text_storage.__contains__(message):
            sub_text_storage[sub_text] = sub_font.render(sub_text, True, (251, 251, 251))
    surf = pygame.Surface((POPUP_WIDTH, POPUP_HEIGHT))
    surf.fill((19, 31, 44))
    surf.blit(text_storage[message], text_storage[message].get_rect(topright=(POPUP_WIDTH-5, 5)))
    if sub_text_storage.__contains__(sub_text):
        surf.blit(sub_text_storage[sub_text], sub_text_storage[sub_text].get_rect(topright=(POPUP_WIDTH-5, 10+font.get_height())))
    if len(texts_shown) < 6:
        texts_shown.append({"surf": surf, "age": time_shown, "action": action, "action_args": action_args,
                            "in_anim": 3/8, "total_time": time_shown, "out_anim": 1, "hover_anim": 0})


def update_popups(screen: pygame.Surface, framerate: int = 60):
    remove_target = None
    for count, message in enumerate(texts_shown):
        screen_width, screen_height = screen.get_width(), screen.get_height()
        message_x = screen_width-(POPUP_WIDTH+POPUP_PADDING) + \
            cserp(1, 0, message["out_anim"])*POPUP_WIDTH
        message_y = screen_height-((len(texts_shown)-1)-count+1)*(POPUP_HEIGHT+POPUP_PADDING) + \
            sum([cserp(0, message["total_time"], text.get("in_anim")) for text in texts_shown])*POPUP_HEIGHT
        surf: pygame.Surface = message["surf"].copy()
        pygame.draw.polygon(surf, (70, 117, 153), ((0, 0), (50+cserp(0, 15, message["hover_anim"]), 0),
                                                   (30+cserp(0, 15, message["hover_anim"]), POPUP_HEIGHT), (0, POPUP_HEIGHT)))
        pygame.draw.polygon(surf, (158, 216, 219), ((0, 0), (40+cserp(0, 10, message["hover_anim"]), 0),
                                                    (20+cserp(0, 10, message["hover_anim"]), POPUP_HEIGHT), (0, POPUP_HEIGHT)))
        screen.blit(surf, (message_x, message_y))
        pygame.draw.rect(screen, (233, 255, 249), (message_x, message_y+POPUP_HEIGHT-10, cserp(POPUP_WIDTH, 0,
                                                                                               message['age'] /
                                                                                               message["total_time"]), 10))
        if message["in_anim"] == 0 and message["out_anim"] == 1:
            if message["surf"].get_rect(topleft=(message_x, message_y)).collidepoint(pygame.mouse.get_pos()):
                message["hover_anim"] += 5/framerate
            else:
                message["hover_anim"] -= 5/framerate
        message["hover_anim"] = clamp(message["hover_anim"], 0, 1)
        message["in_anim"] = clamp(message["in_anim"]-(int(message["in_anim"] > 0)/framerate)*(1-message["hover_anim"]), 0, 99)
        message["out_anim"] = clamp(message["out_anim"]-(int(message["age"] <= 3/8)/framerate*8/3) *
                                    (1-message["hover_anim"]), 0, 99)
        message["age"] -= 1/framerate*(1-message["hover_anim"])
        if message["age"] <= 0:
            remove_target = message
    if remove_target is not None:
        texts_shown.remove(remove_target)


def handle_popup_events(event: pygame.event.Event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            for count, message in enumerate(texts_shown):
                screen_width, screen_height = pygame.display.get_surface().get_width(), \
                                              pygame.display.get_surface().get_height()
                message_x = screen_width-(POPUP_WIDTH+POPUP_PADDING) + \
                    cserp(1, 0, message["out_anim"])*POPUP_WIDTH
                message_y = screen_height-((len(texts_shown)-1)-count+1)*(POPUP_HEIGHT+POPUP_PADDING) + \
                    sum([cserp(0, message["total_time"], text.get("in_anim")) for text in texts_shown])*POPUP_HEIGHT
                if pygame.Rect(message_x, message_y, POPUP_WIDTH, POPUP_HEIGHT).collidepoint(pygame.mouse.get_pos()):
                    # a popup was clicked
                    if message["action_args"] is not None:
                        message["action"](*(message["action_args"]))
                    else:
                        message["action"]()
                    return True
    return False


class RightClickOption:
    def __init__(self, text, func):
        self.func: callable = func
        self.text: str = text


class RightClickAbility:
    def __init__(self, text: str, ability, payable: bool):
        self.ability = ability
        self.text = text
        self.can_pay_for_it = payable


class RightClickMenu:  # there should only be one of these
    def __init__(self):
        self.x = 0
        self.y = 0
        self.options: list[RightClickOption, RightClickAbility] = []
        self.text_cache: dict[str, pygame.Surface] = {}
        self.font: pygame.font.Font = pygame.font.SysFont("Arial", 20)
        self.shown = False

    def show(self, options: list[RightClickOption, RightClickAbility] = ()):
        if len(options) == 0:
            return
        self.shown = True
        self.options = options
        self.x, self.y = pygame.mouse.get_pos()

    def fetch_text(self, text: str):
        if not self.text_cache.__contains__(text):
            self.text_cache[text] = self.font.render(text, True, (0, 0, 0))
        return self.text_cache[text]

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 200,
                           self.font.get_height()*len(self.options))  # could 100% be optimized to not use list comp
        # every time this is called

    def handle_events(self, event: pygame.event.Event):
        will_return = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # lmb pressed
                if self.shown:
                    if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                        better_y = pygame.mouse.get_pos()[1]-self.y
                        better_y /= self.font.get_height()
                        better_y = int(better_y)
                        right_click_thing = self.options[better_y]
                        if isinstance(right_click_thing, RightClickAbility):
                            will_return = right_click_thing.ability
                        elif isinstance(right_click_thing, RightClickOption):
                            right_click_thing.func()
            self.shown = False
        return will_return

    def draw(self, surface: pygame.Surface):
        if self.shown:
            pygame.draw.rect(surface, (0, 0, 0), self.get_rect().inflate(2, 2))
            pygame.draw.rect(surface, (255, 255, 255), self.get_rect())
            for count, option in enumerate(self.options):
                if isinstance(option, RightClickAbility):
                    if not option.can_pay_for_it:
                        pygame.draw.rect(surface, (249, 57, 67), (self.x, self.y+count*self.font.get_height(), 200, self.font.get_height()))
                if pygame.Rect((self.x, self.y+count*self.font.get_height(), 200, self.font.get_height()))\
                        .collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surface, (189, 189, 189), (self.x, self.y+count*self.font.get_height(), 200, self.font.get_height()))
                    if isinstance(option, RightClickAbility):
                        if not option.can_pay_for_it:
                            pygame.draw.rect(surface, (148, 39, 45), (self.x, self.y+count*self.font.get_height(), 200, self.font.get_height()))
                surface.blit(self.fetch_text(option.text), (self.x, self.y+count*self.font.get_height()))


# noinspection PyTypeChecker
pause_menu = None


def get_pause_menu():
    return pause_menu


class PauseMenu:
    def __init__(self):
        self.center = pygame.display.get_surface().get_rect().center
        self.width = 600
        self.height = 500
        self.shown = False
        self.pause_font = pygame.font.SysFont("Helvetica", 25)

        # actual stuff
        segment = pygame.Rect(self.get_rect().left+10, self.get_rect().top+40, self.get_rect().width-20, 40)
        word = pygame.Rect(segment.x, segment.y, segment.w/2, segment.h)
        setting = pygame.Rect(segment.x+segment.w/2, segment.y, segment.w/2, segment.h)
        self.pause_menu_text = Text(self.get_rect().midtop, self.pause_font, "Pause menu", "midtop")

        # hover card opacity
        self.hover_opacity_text = Text(word, self.pause_font, "Card Hover Visibility", "midleft", wrap_rect=True)
        self.hover_opacity = MultipleChoice(setting, self.pause_font, ["Opaque", "Translucent", "Invisible"])
        self.hover_opacity.selected_option = "Translucent"  # default option is translucent

        # connection interval
        self.connection_interval_text = Text(word.move(0, 50), self.pause_font, "Connection speed: ", "midleft", wrap_rect=True)
        self.connection_interval = MultipleChoice(setting.move(0, 50), self.pause_font, ["20 per second", "10 per second", "5 per second"])
        self.connection_interval.selected_option = "20 per second"

        # land scraping accuracy
        self.land_scrape_accuracy_text = Text(word.move(0, 100), self.pause_font, "Land overlaping accuracy: ", "midleft", wrap_rect=True)
        self.land_scrape_accuracy = MultipleChoice(setting.move(0, 100), self.pause_font, [2, 3, 10])
        self.land_scrape_accuracy.selected_option = 3

        # set pause menu to self
        global pause_menu
        pause_menu = self

    def draw(self, surface: pygame.Surface):
        if self.shown:
            pygame.draw.rect(surface, (0, 0, 0), expand_rect(self.get_rect(), 2), border_radius=23)
            pygame.draw.rect(surface, (255, 255, 255), self.get_rect(), border_radius=23)
            self.pause_menu_text.draw(surface)
            self.hover_opacity_text.draw(surface)
            self.hover_opacity.draw(surface)
            self.connection_interval_text.draw(surface)
            self.connection_interval.draw(surface)
            self.land_scrape_accuracy_text.draw(surface)
            self.land_scrape_accuracy.draw(surface)

            # draw dropdown
            self.hover_opacity.draw_select(surface)
            self.connection_interval.draw_select(surface)
            self.land_scrape_accuracy.draw_select(surface)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.center[0]-self.width/2, self.center[1]-self.height/2, self.width, self.height)

    def handle_events(self, event: pygame.event.Event) -> bool:
        """Returns true if you clicked on the box"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.shown = not self.shown
                self.connection_interval.selecting_option = False
                self.hover_opacity.selecting_option = False
                self.land_scrape_accuracy.selecting_option = False
                return True
        if self.shown:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.get_rect().collidepoint(pygame.mouse.get_pos()):  # clicked inside the pause menu rectangle

                        if self.hover_opacity.handle_events(event):
                            return True
                        if self.connection_interval.handle_events(event):
                            return True
                        if self.land_scrape_accuracy.handle_events(event):
                            return True

                        return True
                    else:
                        self.shown = False
        return False


pause_menu: PauseMenu
