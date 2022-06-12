from settingshandler import SettingsHandler
from cows import *
import pygame
from yugo_tools import Button, InputBox
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
        self.loot_pool[card_class] -= 1
        if not self.loot_pool.get(card_class):
            self.loot_pool.pop(card_class)


DEFAULT_DECK = Deck("Default Deck")


class DeckBuilder:
    def __init__(self, savefile, font, small_font):
        self.decks: list[Deck] = []
        self.settings_handler = SettingsHandler(savefile)
        self.settings_handler.register_state("decks", [DEFAULT_DECK])
        self.reload_from_disk()
        if not len(self.decks):
            self.decks.append(DEFAULT_DECK)
        self.selected_deck_id = id(self.decks[0])

        # deck select screen stuff
        width, height, = pygame.display.get_window_size()
        self.font = font
        self.small_font = small_font
        self.left_section_rect = pygame.Rect(0, 0, 300, height)
        self.middle_section_rect = pygame.Rect(300, 0, 500, height)
        self.right_section_rect = pygame.Rect(800, 0, width-self.left_section_rect.w-self.middle_section_rect.w, height)

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

        width, height, = pygame.display.get_window_size()
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

        # right section
        if self.change_deck_name.text != self.selected_deck.name:
            self.change_deck_name.change(text=self.selected_deck.name, font=self.font)
        self.delete_deck_button.draw(screen)
        self.add_deck_button.draw(screen)
        self.change_deck_name.draw(screen)
        self.copy_deck_button.draw(screen)

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

        if self.change_deck_name.handle_events(event):
            self.selected_deck.name = self.change_deck_name.text
            return True
        if self.add_deck_button.handle_events(event):
            return True
        if self.delete_deck_button.handle_events(event):
            return True
        if self.copy_deck_button.handle_events(event):
            return True
