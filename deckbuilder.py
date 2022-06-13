from settingshandler import SettingsHandler
from cows import *
import pygame
from yugo_tools import Button, InputBox, MultipleChoice
from typing import Any


DEFAULT_LOOT_POOL = {
    Castle: 4,
}  # todo change later


class Deck:
    def __init__(self, name):
        self.name: str = name
        self.loot_pool: dict[Any, int] = DEFAULT_LOOT_POOL

    def valid_deck(self) -> bool:
        """Checks to see if the deck configuration is legal or not"""
        # more than four of the same card in a deck
        if True in [amount > 4 for amount in list(self.loot_pool.values())]:
            return False
        # four talismans total
        if bool(sum(list({card: v for card, v in self.loot_pool if card.type == TYPE_TALISMAN}.values())) == 4):
            return False
        # there must be eighty cards total
        if sum(list(self.loot_pool.values())) != 80:
            return False
        return True

    def add_card(self, card_class):
        if self.loot_pool.get(card_class) is None:
            self.loot_pool[card_class] = 1
            return True
        elif self.loot_pool[card_class] == 4:
            return False
        self.loot_pool[card_class] += 1

    def remove_card(self, card_class):
        if card_class in self.loot_pool:
            self.loot_pool[card_class] -= 1
            if not self.loot_pool.get(card_class):
                self.loot_pool.pop(card_class)


DEFAULT_DECK = Deck("Default Deck")


class CardSelector:
    def __init__(self, rect: pygame.Rect):
        self.scroll = 0
        self.dscroll = 0
        self.rect = rect
        self.prev_mouse_pos = (0, 0)
        self._possible_cards = Card.__subclasses__()
        self._possible_cards.sort(key=lambda _: _.image)
        self.scroll_speed = 8
        self.search_term = ""
        self.type_filter = None

    @property
    def possible_cards(self) -> list:
        # search
        filtered = list(filter(lambda _: self.search_term in _.get_name(_).lower(), self._possible_cards))
        # type
        if self.type_filter is not None:
            filtered = list(filter(lambda _: _.type == self.type_filter, self._possible_cards))
        # return it
        if not len(filtered):
            filtered = self._possible_cards
        return filtered

    @property
    def selected(self):
        return bool(self.rect.collidepoint(pygame.mouse.get_pos())*pygame.mouse.get_pressed(3)[0])

    def showcase_card(self, off=0):
        return self.possible_cards[clamp(int(divmod(self.scroll-off, len(self.possible_cards))[1]), 0, len(self.possible_cards)-1)]

    @property
    def rel_mouse(self):
        mloc = pygame.mouse.get_pos()
        return mloc[0]-self.prev_mouse_pos[0], mloc[1]-self.prev_mouse_pos[1]

    def draw(self, screen: pygame.Surface, font):
        if self.selected:
            self.dscroll = self.scroll_speed*self.rel_mouse[0]/self.rect.w
        self.scroll += self.dscroll
        if self.dscroll.__abs__() > 30:
            self.dscroll = self.dscroll/self.dscroll.__abs__()*20
            add_popup("Stop scrolling so fast!")
        self.dscroll *= 0.8

        ratio = self.rect.w/500/3
        lefter_showcase = get_image(join("images", "cards", self.showcase_card(-2).image), (ratio, ratio))
        screen.blit(lefter_showcase, lefter_showcase.get_rect(
            midtop=self.rect.move(divmod(self.scroll, 1)[1]*self.rect.w/3-ratio*1250, 10).midtop)
                    )
        righter_showcase = get_image(join("images", "cards", self.showcase_card(2).image), (ratio, ratio))
        screen.blit(righter_showcase, righter_showcase.get_rect(
            midtop=self.rect.move(divmod(self.scroll, 1)[1]*self.rect.w/3+ratio*750, 10).midtop)
                    )
        left_showcase = get_image(join("images", "cards", self.showcase_card(-1).image), (ratio, ratio))
        screen.blit(left_showcase, left_showcase.get_rect(
            midtop=self.rect.move(divmod(self.scroll, 1)[1]*self.rect.w/3-ratio*750, 10).midtop)
                    )
        right_showcase = get_image(join("images", "cards", self.showcase_card(1).image), (ratio, ratio))
        screen.blit(right_showcase, right_showcase.get_rect(
            midtop=self.rect.move(divmod(self.scroll, 1)[1]*self.rect.w/3+ratio*250, 10).midtop)
                    )
        middle_showcase = get_image(join("images", "cards", self.showcase_card(0).image), (ratio*1.1, ratio*1.1))
        screen.blit(middle_showcase, middle_showcase.get_rect(
            midtop=self.rect.move(divmod(self.scroll, 1)[1]*self.rect.w/3-ratio*250, 10-23).midtop)
                    )
        arrow = self.rect.centerx, self.rect.bottom-50
        pygame.draw.polygon(screen, (0, 0, 0), (arrow, (arrow[0]-20, arrow[1]+40), (arrow[0]+20, arrow[1]+40)))

        # set prev pos
        self.prev_mouse_pos = pygame.mouse.get_pos()
        if get_debug():
            draw_border_of_rect(screen, self.rect, (255, 0, 0))
            screen.blit(fetch_text(f"scroll: {self.scroll}", font, (255, 255, 255)), self.rect.topleft)
            screen.blit(
                fetch_text(f"select: {self.showcase_card().get_name(self.showcase_card())}", font, (255, 255, 255)), self.rect.bottomleft
            )


class DeckBuilder:
    def __init__(self, savefile, font, small_font):
        self.decks: list[Deck] = []
        self.settings_handler = SettingsHandler(savefile)
        self.settings_handler.register_state("decks", [DEFAULT_DECK])
        self.reload_from_disk()
        if not len(self.decks):
            self.decks.append(DEFAULT_DECK)
        self.selected_deck_id = id(self.decks[0])

        # deck select
        # screen stuff
        width, height, = pygame.display.get_window_size()
        self.font = font
        self.small_font = small_font
        self.left_section_rect = pygame.Rect(0, 0, 300, height)
        self.middle_section_rect = pygame.Rect(300, 0, 500, height)
        self.right_section_rect = pygame.Rect(800, 0, width-self.left_section_rect.w-self.middle_section_rect.w, height)
        self.card_selector = CardSelector(self.right_section_rect.inflate(-20, -450).move(0, -70))
        self.card_selector.rect.h -= 50
        self.right_info_rect = self.right_section_rect.copy()
        self.right_info_rect.y = self.card_selector.rect.bottom
        self.right_info_rect.h = height-self.card_selector.rect.bottom
        self.right_info_rect = self.right_info_rect.inflate(-20, -20)

        # buttons
        self.change_deck_name = InputBox(
            (self.right_section_rect.left+10, 10, self.right_section_rect.w-100, 70),
            self.font,
            text_if_no_text="name of deck",
            max_len=20,
        )
        self.change_deck_name.change(text=self.selected_deck.name, font=self.font)
        self.add_deck_button = Button(
            (self.right_section_rect.left+10, 90, (self.right_section_rect.w/3)-15, 40),
            self.font,
            self.create_deck,
            "New deck",
            text="New Deck",
        )
        self.delete_deck_button = Button(
            (self.right_section_rect.left+10+(self.right_section_rect.w/3)-5, 90, (self.right_section_rect.w/3)-15, 40),
            self.font,
            self.delete_sel_deck,
            text="Delete Deck",
        )
        self.copy_deck_button = Button(
            (self.right_section_rect.left+5+(self.right_section_rect.w*2/3)-5, 90, (self.right_section_rect.w/3)-10, 40),
            self.font,
            self.copy_sel_deck,
            text="Copy Deck",
        )
        self.include_card_button = Button(
            (self.right_info_rect.left, self.right_info_rect.top+50, self.right_info_rect.w/2-5, 60),
            self.font,
            self.add_sel_card,
            text="Add card"
        )
        self.remove_card_button = Button(
            (self.right_info_rect.left+self.right_info_rect.w/2+10, self.right_info_rect.top+50, self.right_info_rect.w/2-5, 60),
            self.font,
            self.remove_sel_card,
            text="Remove card"
        )
        self.search_box = InputBox(
            pygame.Rect(self.right_info_rect.left, self.right_info_rect.top, self.right_info_rect.w/2-5, 40),
            self.font,
            text_if_no_text="search for card",
            max_len=30
        )
        self.filter_by_type = MultipleChoice(
            self.search_box.rect.move(self.right_info_rect.w/2+10, 0),
            self.font,
            ["All cards", "Incantations", "Animals", "Lands", "Talismans", "Equipments"]
        )

    def add_sel_card(self):
        self.selected_deck.add_card(self.card_selector.showcase_card())

    def remove_sel_card(self):
        self.selected_deck.remove_card(self.card_selector.showcase_card())

    def reload_from_disk(self):
        self.decks = self.settings_handler.get_state("decks")

    def save_to_disk(self):
        self.settings_handler.set_state("decks", self.decks)

    def create_deck(self, name: str):
        self.decks.append(Deck(name))

    def copy_sel_deck(self):
        deck = self.selected_deck
        _ = Deck(deck.name)
        _.loot_pool = deck.loot_pool.copy()
        names = [deck.name for deck in self.decks]
        while _.name in names:
            if not _.name[-6:-2] == "Copy":
                _.name += " Copy X"
            if not _.name[-1:].isnumeric():
                _.name = _.name[:-1] + "1"
            else:
                _.name = f"{_.name[:-1]}{int(_.name[-1:])+1}"
        self.decks.append(_)

    def get_deck_by_id(self, id_: int) -> tuple[Deck, int]:
        for count, _ in enumerate(self.decks):
            if id(_) == id_:
                return _, count
        raise NotImplementedError(f"no deck found (attempt was: {id_})")

    def inject_deck(self, deck: Deck, player: Player):
        player.loot_pool = deck.loot_pool

    def delete_sel_deck(self):
        if len(self.decks) > 1:
            indx = self.get_deck_by_id(self.selected_deck_id)[1]
            self.decks.remove(self.selected_deck)
            self.selected_deck_id = id(self.decks[clamp(indx, 0, len(self.decks)-1)])

    @property
    def selected_deck(self):
        return self.get_deck_by_id(self.selected_deck_id)[0]

    def draw(self, screen: pygame.Surface):
        def move_pos(p, of):
            return p[0]+of[0], p[1]+of[1]

        self.card_selector.draw(screen, self.font)
        width, height, = pygame.display.get_window_size()
        # right section
        screen.fill(BG_COLOR, self.middle_section_rect)
        screen.fill(BG_COLOR, self.left_section_rect)
        if self.change_deck_name.text != self.selected_deck.name:
            self.change_deck_name.change(text=self.selected_deck.name, font=self.font)
        screen.blit(fetch_text(
            f"Card name: {self.card_selector.showcase_card().get_name(self.card_selector.showcase_card())}", self.font
        ), self.right_info_rect.move(0, 130))
        screen.blit(fetch_text(
            f"Card type: {self.card_selector.showcase_card().repr_type_of_card(self.card_selector.showcase_card())}", self.font
        ), self.right_info_rect.move(0, 160))

        # draw ui
        self.delete_deck_button.draw(screen)
        self.add_deck_button.draw(screen)
        self.change_deck_name.draw(screen)
        self.copy_deck_button.draw(screen)
        self.include_card_button.draw(screen)
        self.remove_card_button.draw(screen)
        self.search_box.draw(screen)
        self.filter_by_type.draw(screen)
        self.filter_by_type.draw_select(screen)

        # two lines for seperation
        pygame.draw.aaline(
            screen, (60, 60, 60),
            move_pos(self.left_section_rect.topright, (0, 10)),
            move_pos(self.left_section_rect.bottomright, (0, -10))
        )
        pygame.draw.aaline(
            screen, (60, 60, 60),
            move_pos(self.middle_section_rect.topright, (0, 10)),
            move_pos(self.middle_section_rect.bottomright, (0, -10))
        )

        # deck listings
        for count, deck in enumerate(self.decks):

            # rectangle block
            block_rect = self.left_section_rect.inflate(-20, -20)
            block_rect.height = (height-10-len(self.decks)*10)/len(self.decks)
            block_rect.y = count*(height-10-len(self.decks)*10)/len(self.decks)+10*(count+1)
            inner_color = Color(255, 255, 255)
            if id(deck) == self.selected_deck_id:
                inner_color = Color(137, 128, 245)
            pygame.draw.rect(screen, (0, 0, 0), block_rect.inflate(4, 4))
            pygame.draw.rect(screen, inner_color.lerp((0, 0, 0), block_rect.collidepoint(pygame.mouse.get_pos())*0.1), block_rect)

            # text
            deck_text = fetch_text(deck.name, self.font)
            screen.blit(deck_text, deck_text.get_rect(center=block_rect.center))

        # card listings
        cards_title_text = fetch_text("Cards", self.font)
        cards_title_rect = cards_title_text.get_rect(topleft=(self.middle_section_rect.left+10, 10))
        screen.blit(cards_title_text, cards_title_rect)
        for count, card in enumerate(self.selected_deck.loot_pool):
            card_text = fetch_text(f"{card.get_name(card)} (x{self.selected_deck.loot_pool[card]})", self.small_font)
            screen.blit(card_text, card_text.get_rect(topleft=(self.middle_section_rect.left+10, 55+count*25)))

            # card add and subtract buttons
            add_more_rect = pygame.Rect(0, 0, 20, 20)
            add_more_rect.midleft = card_text.get_rect(topleft=(self.middle_section_rect.left+10, 55+count*25)).midright
            add_more_rect.move_ip(6, 2)
            pygame.draw.rect(screen, (0, 0, 0), add_more_rect.inflate(4, 4))
            pygame.draw.rect(screen, (255, 255, 255), add_more_rect)
            add_text = fetch_text("+", self.small_font)
            screen.blit(add_text, add_text.get_rect(center=add_more_rect.center))

            sub_less_rect = add_more_rect.move(25, 0)
            pygame.draw.rect(screen, (0, 0, 0), sub_less_rect.inflate(4, 4))
            pygame.draw.rect(screen, (255, 255, 255), sub_less_rect)
            sub_text = fetch_text("-", self.small_font)
            screen.blit(sub_text, sub_text.get_rect(center=sub_less_rect.center))
        if get_debug():
            draw_border_of_rect(screen, self.right_info_rect, (0, 255, 255))
        draw_cows_popups(screen, FRAMERATE)

    def handle_events(self, event: pygame.event.Event):
        width, height, = pygame.display.get_window_size()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # deck listings
                for count, deck in enumerate(self.decks):

                    # rectangle block
                    block_rect = self.left_section_rect.inflate(-20, -20)
                    block_rect.height = (height-10-len(self.decks)*10)/len(self.decks)
                    block_rect.y = count*(height-10-len(self.decks)*10)/len(self.decks)+10*(count+1)
                    if block_rect.collidepoint(pygame.mouse.get_pos()):
                        self.selected_deck_id = id(deck)
                        return True
                # card listings
                for count, card in enumerate(self.selected_deck.loot_pool):
                    card_text = fetch_text(f"{card.get_name(card)} (x{self.selected_deck.loot_pool[card]})", self.small_font)
                    # card add and subtract buttons
                    add_more_rect = pygame.Rect(0, 0, 20, 20)
                    add_more_rect.midleft = card_text.get_rect(topleft=(self.middle_section_rect.left+10, 55+count*25)).midright
                    add_more_rect.move_ip(6, 2)
                    sub_less_rect = add_more_rect.move(25, 0)
                    if add_more_rect.collidepoint(pygame.mouse.get_pos()):
                        self.selected_deck.add_card(card)
                        break
                    if sub_less_rect.collidepoint(pygame.mouse.get_pos()):
                        self.selected_deck.remove_card(card)
                        break

        # ui elements
        if self.change_deck_name.handle_events(event):
            self.selected_deck.name = self.change_deck_name.text
            return True
        if self.filter_by_type.handle_events(event):
            self.card_selector.type_filter = {
                "Animals": TYPE_ANIMAL,
                "Incantations": TYPE_INCANTATION,
                "Lands": TYPE_LAND,
                "Equipments": TYPE_EQUIPMENT,
                "Talismans": TYPE_TALISMAN
            }.get(self.filter_by_type.selected_option)
            return True
        if self.add_deck_button.handle_events(event):
            return True
        if self.delete_deck_button.handle_events(event):
            return True
        if self.copy_deck_button.handle_events(event):
            return True
        if self.include_card_button.handle_events(event):
            return True
        if self.remove_card_button.handle_events(event):
            return True
        if self.search_box.handle_events(event):
            self.card_selector.search_term = self.search_box.text
            return True
