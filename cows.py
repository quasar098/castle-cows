import pygame
from typing import Union
from yugo_tools import get_image, join, cserp, _move_pos, fetch_text, expand_rect
from numpy import clip as clamp, log2
from math import sqrt
# noinspection PyUnresolvedReferences
from pygamepopups import update_popups, handle_popup_events, RightClickMenu, RightClickOption, \
    RightClickAbility, get_pause_menu
from effects import CurrencyParticle, CircleParticle, play_sound_path, FakeCard
from constants import *
# noinspection PyUnresolvedReferences
from cowspopups import add_popup, draw_cows_popups, handle_cows_popups, add_debug_popup
from random import choices as randchoice


class Action:
    def __init__(self, card, action: int, amount: Union[int, callable], conditional=None):
        self.card: Card = card
        self.action = action
        self.amount = amount
        self.conditional: Union[ActionConditional, None] = conditional


class InputAction:
    def __init__(self, card, action: int, amount: int, what_choose: int, conditional=None):
        self.card: Card = card
        self.action = action
        self.amount = amount
        self.choose = what_choose
        self.conditional: Union[ActionConditional, None] = conditional


class DelayedAction:
    def __init__(self, card, action: int, amount: int, wait_for: int, conditional=None):
        self.card: Card = card
        self.action = action
        self.amount = amount
        self.wait_for = wait_for
        self.conditional: Union[ActionConditional, None] = conditional


class ActionConditional:
    def __init__(self, card, requirement, comparison_type, amount):
        """Its requirement | comparison type | amount,
        so more than means that requirement > amount"""
        self.card = card
        self.req = requirement
        self.comp = comparison_type
        self.amount = amount

    def is_true(self):
        amount1 = 0
        if self.req == REQ_CARD_NUM_RESIDENTS:
            amount1 = self.card.get_num_residents()
        amount2 = self.amount
        if self.comp == COND_OPERATOR_MORE_THAN:
            return amount1 > amount2
        if self.comp == COND_OPERATOR_EQUALS:
            return amount1 == amount2
        if self.comp == COND_OPERATOR_LESS_THAN:
            return amount1 < amount2
        return True


class Hand:
    def __init__(self):
        self.cards: list[Card] = []
        self.anim: dict[int, float] = {}
        self.in_anim: dict[int, float] = {}

    def draw(self, surface: pygame.Surface, framerate: int) -> None:
        padding_width = 200
        hand_rect = pygame.Rect(padding_width, surface.get_height()-300, surface.get_width()-padding_width*2, 300)
        for count, card in enumerate(self.cards):
            self.anim[id(card)] = self.anim.get(id(card), 0)
            self.in_anim[id(card)] = self.in_anim.get(id(card), 0)
            in_anim_sum = sum([cserp(self.in_anim.get(id(in_card), 0)) for in_card in self.cards])
            log_part = 1
            if not in_anim_sum == 0:
                log_part = log2(in_anim_sum+1)
            if log_part == 0:
                log_part = 1
            x = surface.get_width()/2  # start at center
            x -= in_anim_sum*125/log_part  # offset to the left
            x += count*250/log_part  # move to the right based on enum count
            y = surface.get_height()-180-(cserp(self.anim[id(card)])*145)
            card_rect = pygame.Rect(x, y,
                                    250/log_part+(250-250/log_part)*(int(len(self.cards)-1 == count)), 325)
            if card_rect.collidepoint(pygame.mouse.get_pos()):
                self.anim[id(card)] += 0.06*75/framerate
            else:
                self.anim[id(card)] -= 0.06*75/framerate
            self.anim[id(card)] = clamp(self.anim[id(card)], 0, 1)
            self.in_anim[id(card)] += 0.06*75/framerate
            self.in_anim[id(card)] = clamp(self.in_anim[id(card)], 0, 1)
            surface.blit(get_image(join("images", "cards", card.image), (0.5, 0.5)), (x, y))
            if debug:
                draw_border_of_rect(surface, card_rect)
                draw_border_of_rect(surface, hand_rect, (255, 0, 0))

    def handle_events(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                surface = pygame.display.get_surface()
                padding_width = 200
                hand_rect = pygame.Rect(padding_width, surface.get_height()-300, surface.get_width()-padding_width*2, 300)
                if hand_rect.collidepoint(pygame.mouse.get_pos()):
                    cards_hitboxes = {}
                    for count, card in enumerate(self.cards):
                        surface = pygame.display.get_surface()
                        self.anim[id(card)] = self.anim.get(id(card), 0)
                        in_anim_sum = sum([cserp(self.in_anim.get(id(in_card), 0)) for in_card in self.cards])
                        log_part = 1
                        if not in_anim_sum == 0:
                            log_part = log2(in_anim_sum+1)
                        if log_part == 0:
                            log_part = 1
                        x = surface.get_width()/2  # start at center
                        x -= in_anim_sum*125/log_part  # offset to the left
                        x += count*250/log_part  # move to the right based on enum count
                        cards_hitboxes[tuple(
                            pygame.Rect(x, surface.get_height()-180-cserp(self.anim[id(card)])*145, 250, 325)[:4])] = card
                    for card_hitbox in cards_hitboxes.__reversed__():
                        if pygame.Rect(card_hitbox).collidepoint(pygame.mouse.get_pos()):
                            return cards_hitboxes[card_hitbox]
        return


class Field:
    def __init__(self):
        self.cards: list[Card] = []
        self.land_bloom_out_anim: dict[int, float] = {}

    def draw(self, surface: pygame.Surface, framerate: int) -> None:
        for card in self.cards:
            if card.type == LAND_TYPE:
                self.land_bloom_out_anim[id(card)] = self.land_bloom_out_anim.get(id(card), 0)
                if card.get_rect().collidepoint(pygame.mouse.get_pos()):
                    self.land_bloom_out_anim[id(card)] += 0.05*75/framerate
                else:
                    self.land_bloom_out_anim[id(card)] -= 0.05*75/framerate
                self.land_bloom_out_anim[id(card)] = clamp(self.land_bloom_out_anim[id(card)], 0, 1)
                anim = cserp(self.land_bloom_out_anim[id(card)])
                pygame.draw.circle(surface, pygame.color.Color(169, 228, 239).lerp((255, 147, 61), 0.3+anim*0.4),
                                   _move_pos(card.mod_pos(), (125, 162)), 500)
        for card in self.cards:
            card.draw(surface)

    def handle_events(self, event: pygame.event.Event, rel: tuple[int, int]):
        for card in self.cards.__reversed__():
            sel_prev = card.selected
            mouseevent = card.handle_events(event, rel)
            if mouseevent == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.put_on_top(card)
                    return True
            elif mouseevent == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if sel_prev:
                        return card

    def put_on_top(self, card):
        card: Card
        self.cards.remove(card)
        self.cards.append(card)

    def discard_card(self, card):
        """This is for animation support"""
        width, height = pygame.display.get_surface().get_size()
        if self.cards.__contains__(card):
            self.cards.remove(card)
            get_local_player().discarding_fake_cards.append(
                FakeCard(card.image, card.mod_pos(), (width-160, height-130), grot=180, srot=180,
                         anim_time=0.7, real_card=card, endsize=(150, 197)))


class Camera:
    def __init__(self, pos: tuple[int, int]):
        self.x = pos[0]
        self.y = pos[1]
        self.zoom = 1

    def __str__(self):
        return f"Camera<({self.x}, {self.y})>"


class Player:
    # noinspection PyUnresolvedReferences
    def __init__(self, name: str):

        # important stuff
        self.money: int = 5
        self.milk: int = 5
        self.hay: int = 5
        self.username = name
        self.field: Field = Field()
        self.hand: Hand = Hand()
        self.camera = Camera((0, 0))
        self.is_my_turn = True
        self.step = "collect"

        # visible stuff
        self.visible_money = self.money
        self.visible_milk = self.milk
        self.visible_hay = self.hay

        # discard stuff
        self.discard_pile: list[Card] = []
        self.discarding_fake_cards: list[FakeCard] = []
        self.drawing_fake_cards: list[FakeCard] = []

        # queues and waiting
        self.doing_input_action = False
        self.delayed_action_queue: list[DelayedAction] = []
        self.action_queue: list[Union[InputAction, Action]] = []

        # misc
        self.loot_pool = {}
        self.index_of_grab = 0

    def update_visible_currencies(self):
        global currency_particles
        self.visible_money = self.money
        self.visible_milk = self.milk
        self.visible_hay = self.hay
        currency_particles = []

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        # ratios and div numbers
        box_width = 40
        box_height = 90
        text_height_from_top = 60
        border_rounding = 2
        spacing_x = 18
        box_height_from_top = 7

        # used a lot
        player_info_rect = pygame.Rect((10, pygame.display.get_surface().get_height()-160+box_height_from_top, 150, 150))

        # money border
        money_rectangle = pygame.Rect(player_info_rect.left, player_info_rect.top, box_width, box_height)
        pygame.draw.rect(surface, (0, 0, 0), expand_rect(money_rectangle, 4), border_radius=border_rounding)
        money_surf = pygame.Surface(money_rectangle.size)
        money_surf.set_alpha(127)
        money_surf.fill((94, 252, 141))
        surface.blit(money_surf, money_rectangle.topleft)

        # money text
        money_text_pos = _move_pos(money_rectangle.topleft, (box_width/2, text_height_from_top))
        surface.blit(fetch_text(f"{self.visible_money}", font),
                     fetch_text(f"{self.visible_money}", font).get_rect(midtop=money_text_pos))
        surface.blit(get_image(join("images", "money.png")), money_rectangle.topleft)

        # milk border
        milk_rectangle = pygame.Rect(player_info_rect.left+40+spacing_x, player_info_rect.top, box_width, box_height)
        pygame.draw.rect(surface, (0, 0, 0), expand_rect(milk_rectangle, 4), border_radius=border_rounding)
        milk_surf = pygame.Surface(milk_rectangle.size)
        milk_surf.set_alpha(127)
        milk_surf.fill((163, 247, 255))
        surface.blit(milk_surf, milk_rectangle.topleft)

        # milk text
        milk_text_pos = _move_pos(milk_rectangle.topleft, (box_width/2, text_height_from_top))
        surface.blit(fetch_text(f"{self.visible_milk}", font), fetch_text(f"{self.visible_milk}", font).get_rect(midtop=milk_text_pos))
        surface.blit(get_image(join("images", "milk.png")), milk_rectangle.topleft)

        # hay border
        hay_rectangle = pygame.Rect(player_info_rect.left+(40+spacing_x)*2, player_info_rect.top, box_width, box_height)
        pygame.draw.rect(surface, (0, 0, 0), expand_rect(hay_rectangle, 4), border_radius=border_rounding)
        hay_surf = pygame.Surface(hay_rectangle.size)
        hay_surf.set_alpha(127)
        hay_surf.fill((245, 230, 99))
        surface.blit(hay_surf, hay_rectangle.topleft)

        # hay text
        hay_text_pos = _move_pos(hay_rectangle.topleft, (box_width/2, text_height_from_top))
        surface.blit(fetch_text(f"{self.visible_hay}", font), fetch_text(f"{self.visible_hay}", font).get_rect(midtop=hay_text_pos))
        surface.blit(get_image(join("images", "hay.png")), hay_rectangle.topleft)

        # discard pile
        if len(self.discard_pile) > 0:
            discard_rect = pygame.Rect(pygame.display.get_surface().get_width()-160,
                                       pygame.display.get_surface().get_height()-130, 20, 20)
            discard_top_card_surf = get_image(join("images", "cards", self.discard_pile[len(self.discard_pile)-1].image), (0.3, 0.3))
            surface.blit(discard_top_card_surf, discard_top_card_surf.get_rect(topleft=discard_rect.topleft))
            surface.blit(fetch_text(f"Discard Pile", font), discard_rect.move(0, -25).topleft)

        # set the scraping land amount
        new_coll = get_pause_menu().land_scrape_accuracy.selected_option
        if land_collision_accuracy != new_coll:
            set_land_coll_acc(new_coll)

        # hover cards in fake cards
        hand_card_image_name = None
        card_hover = None
        inhabitants = []
        if hand_card_image_name is None:
            if len(self.drawing_fake_cards) > 0:
                tmp = self.drawing_fake_cards[0]
                if tmp.get_rect().collidepoint(pygame.mouse.get_pos()):
                    if tmp.anim > 0.5 and tmp.gy == tmp.sy:
                        hand_card_image_name = tmp.image
                        card_hover = self.drawing_fake_cards[0].real_card
        # hover card in hand cards
        if hand_card_image_name is None:
            for count, card in enumerate(self.hand.cards):
                self.hand.anim[id(card)] = self.hand.anim.get(id(card), 0)
                in_anim_sum = sum([cserp(self.hand.in_anim.get(id(in_card), 0)) for in_card in self.hand.cards])
                log_part = 1
                if not in_anim_sum == 0:
                    log_part = log2(in_anim_sum+1)
                if log_part == 0:
                    log_part = 1
                x = surface.get_width()/2  # start at center
                x -= in_anim_sum*125/log_part  # offset to the left
                x += count*250/log_part  # move to the right based on enum count
                card_rect = pygame.Rect(x, surface.get_height()-180-cserp(self.hand.anim[id(card)])*145, 250, 325)
                if card_rect.collidepoint(pygame.mouse.get_pos()):  # hovering over hand card
                    hand_card_image_name = card.image
                    card_hover = card
        # hover card in field cards
        if hand_card_image_name is None:
            for card in self.get_cards_recursively().__reversed__():
                if card.get_rect().collidepoint(pygame.mouse.get_pos()):  # hovering over field card
                    hand_card_image_name = card.image
                    card_hover = card
                    if len(inhabitants) == 0:
                        inhabitants = card.equipped.copy()
                    break
        # draw if hover card exists
        if hand_card_image_name is not None:
            if get_pause_menu().hover_opacity.selected_option == "Invisible":
                return
            hover_img = get_image(join("images", "cards", hand_card_image_name), (0.8, 0.8), 0.1).copy()
            if get_pause_menu().hover_opacity.selected_option == "Translucent":
                hover_img.set_alpha(90)
            hover_rect = hover_img.get_rect(midright=(surface.get_width()-10, surface.get_height()/2))
            surface.blit(hover_img, hover_rect)
            card_type_dict = {ANIMAL_TYPE: "animal", TALISMAN_TYPE: "talisman", LAND_TYPE: "land",
                              EQUIPMENT_TYPE: "equipment", INCANTATION_TYPE: "incantation"}
            card_type_text = fetch_text(f"card type: {card_type_dict[card_hover.type]}", font)
            surface.blit(card_type_text, card_type_text.get_rect(midtop=_move_pos(hover_rect.midtop, (0, 10))))

            def class_to_string(thing) -> str:
                thing = str(type(thing))[13:-2]
                newthing = ""
                for count_, letter in enumerate(thing):
                    letter: str
                    if not count_ == 0 and letter.isupper():
                        newthing += " " + letter.lower()
                        continue
                    newthing += letter
                    continue

                return newthing

            # draw inhabitants (e.g. "+ Greenest Grass")
            if len(inhabitants) > 0:
                for inhab_count, card_inhab in enumerate(inhabitants):
                    card_type_text = fetch_text(f"+ {class_to_string(card_inhab)}", font)
                    surface.blit(card_type_text,
                                 card_type_text.get_rect(
                                     midtop=_move_pos(hover_rect.midbottom, (0, 30*inhab_count+10))))

    def draw_fake_cards(self, surface: pygame.Surface, framerate: int):
        # draw the pick up cards
        if len(self.drawing_fake_cards) > 0:
            self.drawing_fake_cards[0].draw(surface, framerate)
            if get_debug():
                draw_border_of_rect(surface,  self.drawing_fake_cards[0].get_rect())
        kill_list = []
        for card in self.discarding_fake_cards:
            card.draw(surface, framerate)
            if card.anim == 1:
                get_local_player().discard_pile.append(card.real_card)
                kill_list.append(card)
        if len(self.drawing_fake_cards) > 0:
            fake_card = self.drawing_fake_cards[0]
            if fake_card.get_rect().collidepoint(pygame.mouse.get_pos()):
                if fake_card.grot == 0:
                    fake_card.reveal(0.6)
        for card_kill in kill_list:
            self.discarding_fake_cards.remove(card_kill)

    # noinspection PyTypeChecker
    def update_cursor_image(self):
        if self.doing_input_action:
            pygame.mouse.set_cursor(pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_CROSSHAIR))
        else:
            pygame.mouse.set_cursor(pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))

    def handle_events(self, event: pygame.event.Event, rel: tuple[int, int]):
        # prevent doing anything if getting input action
        if self.doing_input_action:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for card in self.get_cards_recursively().__reversed__():
                        if card.get_rect().collidepoint(pygame.mouse.get_pos()):
                            action = self.action_queue[0]
                            card_type_interpreter = {
                                PICK_CARD: lambda _: True,
                                PICK_COW: lambda _: _.is_cow,
                                PICK_PLAYER: lambda _: False,
                                PICK_LAND: lambda _: _.type == LAND_TYPE,
                                PICK_ANIMAL: lambda _: _.type == ANIMAL_TYPE
                            }
                            if card_type_interpreter[action.choose](card):
                                self.doing_input_action = False
                                self.action_queue.pop(0)
                                self.clear_queue()
                                self.update_cursor_image()
                                get_statistics_manager().last_cow_chosen = card
                            else:
                                add_popup("You can't do that!")
            return True

        # handling the drawing of cards
        if len(self.drawing_fake_cards) > 0:
            fake_card = self.drawing_fake_cards[0]
            if fake_card.get_rect().collidepoint(pygame.mouse.get_pos()):
                if fake_card.grot == 0:
                    pass
                elif fake_card.anim >= 0.5:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            self.hand.cards.append(fake_card.real_card)
                            self.drawing_fake_cards.remove(fake_card)
                            play_sound_path(join("sounds", "cardplay.mp3"), 0.5)

            return True

        # grabbing a card from the hand
        card = self.hand.handle_events(event)
        if card:
            if self.hand.cards.__contains__(card):
                for index_count, card_index_find in enumerate(self.hand.cards):
                    if card_index_find == card:
                        self.index_of_grab = index_count
                self.hand.cards.remove(card)
                card.x, card.y = _move_pos(mod_pos(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], True), (-125, -162))
                card.selected = True
                self.field.cards.append(card)
                return True

        # grabbing and letting go of card in field
        card_field = self.field.handle_events(event, rel)
        if self.field.cards.__contains__(card_field):
            if isinstance(card_field, Card):
                # let go of card
                if pygame.mouse.get_pos()[1] > pygame.display.get_surface().get_height()-170:
                    # on the hand area
                    if not card_field.was_on_field:
                        self.hand.cards.insert(self.index_of_grab, card_field)
                        self.field.cards.remove(card_field)
                        if self.step != "use":
                            play_sound_path(join("sounds", "error.mp3"))
                else:
                    # on your field
                    if get_local_player().step == "use":
                        if not card_field.was_on_field:
                            if not remove_currency_if_has(card_field.cost_currency, card_field.cost_amount):
                                self.field.cards.remove(card_field)
                                self.hand.cards.insert(self.index_of_grab, card_field)
                                return True
                            card_field.was_on_field = True
                            play_sound_path(join("sounds", "cardfold.mp3"), 0.4)
                        if card_field.type == INCANTATION_TYPE:
                            for ability in card_field.abilities:
                                ability.activate()
                            get_local_player().clear_queue()
                            self.field.discard_card(card_field)
                        else:
                            self.attempt_equip_card(card_field)
                    else:
                        play_sound_path(join("sounds", "error.mp3"))
                        self.field.cards.remove(card_field)
                        self.hand.cards.insert(self.index_of_grab, card_field)
                        if get_local_player().step == "collect":
                            add_popup("You must draw a card first!")
            return True
        if isinstance(card_field, bool):
            return True

        # prevent grabbing multiple cards at once (e.g. with auto clicker or low debounce time)
        if sum([int(card.selected) for card in self.field.cards]) > 1:
            one_done = False
            kill_list = []
            for card_prevent_grab in self.field.cards:
                if card_prevent_grab.selected:
                    if not one_done:
                        one_done = True
                    else:
                        kill_list.append(card_prevent_grab)
            for hit in kill_list:
                self.field.cards.remove(hit)
                self.hand.cards.append(hit)

    def attempt_equip_card(self, card_find):
        card_find: Card
        card_find.selected = False
        if card_find.type == EQUIPMENT_TYPE:
            for card in self.field.cards.__reversed__():
                if id(card) != id(card_find):
                    if card.get_rect().collidepoint(pygame.mouse.get_pos()):  # card dragged on card
                        if self.field.cards.__contains__(card_find):  # assert is not null
                            good_types = (card_find.can_go_on if isinstance(card_find.can_go_on, tuple) else (card_find.can_go_on,))
                            if good_types.__contains__(card.type):
                                self.field.cards.remove(card_find)
                                card.equipped.append(card_find)
                                return
            # could not find a card to go on top of
            if self.field.cards.__contains__(card_find):  # assert is not null (same as above)
                self.field.cards.remove(card_find)
                self.hand.cards.append(card_find)
            add_popup(f"You cannot do that there!")
            play_sound_path(join("sounds", "error.mp3"))

    def next_turn_step(self):
        if not self.is_my_turn:
            return True
        if self.do_validity_check():
            return True
        steps = ["collect", "draw", "use"]
        self.step = steps[divmod(steps.index(self.step)+1, len(steps))[1]]
        if self.step == "draw":
            self.draw_card()
            self.step = steps[divmod(steps.index(self.step)+1, len(steps))[1]]
        return False

    def do_validity_check(self) -> bool:
        """Returns true if cards are in an invalid state (e.g. incantations/equipments on their own)"""
        width, height = pygame.display.get_surface().get_size()

        def camera_to_card(_):
            get_local_player().camera.x = -width/2+_.x+150
            get_local_player().camera.y = -height/2+_.y+162

        # solo incantations and equipments
        for card in self.field.cards:
            if card.type in (INCANTATION_TYPE, EQUIPMENT_TYPE):
                add_popup("This needs to go on a card"*(card.type == EQUIPMENT_TYPE) +
                          "How did this happen?????"*(card.type == INCANTATION_TYPE))
                camera_to_card(card)
                return True

        # animals without a home
        not_homeless_cards = []
        for card in [_ for _ in self.field.cards if _.type == LAND_TYPE]:
            not_homeless_cards.extend(card.get_residents())
            not_homeless_cards.append(card)
        if len(self.field.cards) > len(not_homeless_cards):
            for card in self.field.cards:
                if not not_homeless_cards.__contains__(card):
                    camera_to_card(card)
                    add_popup("This animal needs a home!")
                    return True
        elif len(self.field.cards) < len(not_homeless_cards):
            raise ArithmeticError("Card is on two lands at once (probably)")
        return False

    def get_cards_recursively(self, rec_list=None):
        rec_list: list[Card]
        total_cards = rec_list.copy() if rec_list is not None else []
        if rec_list is None:
            rec_list = self.field.cards
            for card in rec_list:
                total_cards.append(card)
        for card_rec in rec_list:
            rec = self.get_cards_recursively(card_rec.equipped)
            total_cards.extend(rec)
        return total_cards

    def draw_card(self, amount=1):
        cards = list(self.loot_pool.keys())
        weights = list(self.loot_pool.values())
        for card_drawn in randchoice(cards, weights=weights, k=amount):
            card_var = card_drawn()
            width, height = pygame.display.get_surface().get_size()
            # noinspection PyTypeChecker
            self.drawing_fake_cards.append(FakeCard(card_var.image, (width/2-125, -250), (width/2-125, height/2-162),
                                                    anim_time=0.6, real_card=card_var))

    def can_pay_for(self, currency: int, cost: int) -> bool:
        """If the player can pay for a certain item, return true"""
        current_amount = (int(currency == DAIRY_DOLLAR)*self.money
                          + int(currency == MILK_COUNTER)*self.milk
                          + int(currency == HAY_COUNTER)*self.hay)
        if current_amount >= cost:
            return True
        return False

    def handle_card_actions(self, action: int):

        # run delayed actions
        delayed_action_kill_list = []
        for delayed_action in self.delayed_action_queue:
            if delayed_action.wait_for == action:
                execute_action(Action(delayed_action.card, delayed_action.action, delayed_action.amount))
                delayed_action_kill_list.append(delayed_action)
        for kill_me in delayed_action_kill_list:
            self.delayed_action_queue.remove(kill_me)

        # see if each action is valued by thing
        total_actions: list[Action, DelayedAction, InputAction] = []
        for card in self.get_cards_recursively():
            actions = card.handle_action(action)
            if actions in (None, []):
                continue
            for action_add in actions:
                total_actions.append(action_add)

        # sort the actions
        def sort_actions(_: Action):
            return _.action

        # sort actions by number and execute them in order
        total_actions.sort(key=sort_actions)
        for action in total_actions:
            if isinstance(action, DelayedAction):
                self.delayed_action_queue.append(action)
            else:
                self.action_queue.append(action)

        self.clear_queue()

    def clear_queue(self):
        """Run through the queue and clear as many actions from it as possible (before it hits an InputAction)"""
        kill_list = []
        for action in self.action_queue:
            if isinstance(action, Action):
                execute_action(action)
                kill_list.append(action)
            elif isinstance(action, InputAction):
                self.doing_input_action = True
                self.update_cursor_image()
        for _ in kill_list:
            self.action_queue.remove(_)

    def reset_abilities(self):
        for card in self.field.cards:
            card.reset_abilities()
        for card in self.discard_pile:
            card.reset_abilities()
        for card in self.hand.cards:
            card.reset_abilities()


class StatisticsManager:
    def __init__(self):
        """Keeps track of statistics throughout the game. Only for tracking stats of the local player, other's stats are gotten through packets (maybe)"""
        self.turns_passed = 0
        self.last_cow_chosen = None

    def get_num_cows(self):
        return len([card_cow for card_cow in get_local_player().get_cards_recursively() if card_cow.is_cow])

    def get_num_players(self):
        return 1

    def get_last_cow_chosen(self):
        return self.last_cow_chosen


# player + stats
local_player = Player("quasar098")
stat_man = StatisticsManager()

# other
card_LOD = 60  # card distance apart (lift off distance) when equipments are equipped
land_collision_accuracy = 3  # how accurate to be with collision when scraping (scrape) the edge of lands against other lands


def set_land_coll_acc(val):
    global land_collision_accuracy
    land_collision_accuracy = val


# special effects
currency_particles: list[CurrencyParticle] = []
circle_particles: list[CircleParticle] = []

# debug
debug = False


def get_currency_particles():
    return currency_particles


def get_circle_particles():
    return circle_particles


def get_parent(card_find):
    card_find: Card
    for card in get_local_player().field.cards:
        if card.equipped.__contains__(card_find):
            return card


def toggle_debug() -> bool:
    global debug
    debug = not debug
    return debug


def get_debug() -> bool:
    return debug


def get_local_player() -> Player:
    return local_player


def get_statistics_manager() -> StatisticsManager:
    return stat_man


def draw_border_of_rect(surf: pygame.Surface, rect: pygame.rect.Rect, color: tuple[int, int, int] = (0, 0, 0)) -> None:
    """Draws the lines around the pygame rectangle"""
    pygame.draw.line(surf, color, rect.topleft, rect.topright, 5)
    pygame.draw.line(surf, color, rect.bottomright, rect.topright, 5)
    pygame.draw.line(surf, color, rect.bottomright, rect.bottomleft, 5)
    pygame.draw.line(surf, color, rect.topleft, rect.bottomleft, 5)


def mod_x(x):
    return x-get_local_player().camera.x


def sub_real_amount(var_placeholder: int):
    if var_placeholder == SELF_TURNS_PASSED:
        return get_statistics_manager().turns_passed
    if var_placeholder == SELF_MONEY_AMOUNT:
        return get_local_player().money
    if var_placeholder == SELF_MILK_AMOUNT:
        return get_local_player().milk
    if var_placeholder == SELF_HAY_AMOUNT:
        return get_local_player().hay
    if var_placeholder == SELF_COWS_ON_FIELD:
        return get_statistics_manager().get_num_cows()
    if var_placeholder == NUM_PLAYERS:
        return get_statistics_manager().get_num_players()
    if var_placeholder == LAST_CARD_CHOSEN:
        return get_statistics_manager().last_cow_chosen
    return var_placeholder


def mod_y(y):
    return y-get_local_player().camera.y


def mod_pos(x, y, inv=False):
    if not inv:
        return mod_x(x), mod_y(y)
    else:
        return x+get_local_player().camera.x, y+get_local_player().camera.y


def remove_currency_if_has(currency_type: int, amount: int) -> bool:
    """Returns true if the currency has been removed from the players total balance"""
    def create_loss_particles(pos: tuple[float, float], am: int):
        for _ in range(am):
            get_circle_particles().append(CircleParticle(pos, color=(250, 60, 60)))
    width, height = pygame.display.get_surface().get_size()
    if currency_type == DAIRY_DOLLAR:
        if get_local_player().money >= amount:
            get_local_player().money -= amount
            get_local_player().visible_money -= amount
            create_loss_particles((27, height-135), amount*2)
            return True
    if currency_type == MILK_COUNTER:
        if get_local_player().milk >= amount:
            get_local_player().milk -= amount
            get_local_player().visible_milk -= amount
            create_loss_particles((85, height-135), amount*2)
            return True
    if currency_type == HAY_COUNTER:
        if get_local_player().hay >= amount:
            get_local_player().hay -= amount
            get_local_player().visible_hay -= amount
            create_loss_particles((145, height-135), amount*2)
            return True
    if currency_type is None:
        return True
    play_sound_path(join("sounds", "error.mp3"))
    return False


def execute_action(action: Union[Action, DelayedAction, InputAction]) -> None:
    if action.conditional is not None:
        if not action.conditional.is_true():
            return
    if isinstance(action, Action):
        # substitute the real amount in for a placeholder (e.g. NUM_COWS -> [actual number of cows])
        amount = sub_real_amount(action.amount)

        # particle position
        particle_pos = _move_pos(action.card.mod_pos(), (125, 162))

        # add X particles where X is the amount
        for _ in range(amount):
            if action.action == SELF_GIVE_MONEY:
                get_local_player().money += 1
                currency_particles.append(CurrencyParticle(particle_pos, DAIRY_DOLLAR))
            if action.action == SELF_GIVE_DAIRY:
                get_local_player().milk += 1
                currency_particles.append(CurrencyParticle(particle_pos, MILK_COUNTER))
            if action.action == SELF_GIVE_HAY:
                get_local_player().hay += 1
                currency_particles.append(CurrencyParticle(particle_pos, HAY_COUNTER))

    elif isinstance(action, DelayedAction):
        # add delayed action to queue
        get_local_player().delayed_action_queue.append(action)

    elif isinstance(action, InputAction):
        # do input action right now
        add_debug_popup("todo: do this")


class Ability:
    def __init__(self, action: Union[Action, DelayedAction, InputAction], cost_amount: int, cost_currency: int = None,
                 ab_name: str = "NaN"):
        self.cost = cost_amount
        self.currency = cost_currency
        self.action = action
        self.name = ab_name
        self.activated = False

    def activate(self):
        if not self.activated:
            if remove_currency_if_has(self.currency, self.cost):
                if isinstance(self.action, DelayedAction):
                    execute_action(self.action)
                else:
                    get_local_player().action_queue.append(self.action)
                self.activated = True
        else:
            play_sound_path(join("sounds", "error.mp3"))


class Card:
    image: str = None

    def __init__(self, pos: Union[list[int, int], tuple[int, int]] = (100, 100)):

        # main stuff
        self.x = pos[0]
        self.y = pos[1]
        self.type = None  # category/type of card
        self.selected = False
        self.abilities: set[Ability] = set()
        self.was_on_field = False

        # cost stuff
        self.cost_amount: int = 0
        self.cost_currency: int = DAIRY_DOLLAR

        # equipment shenanies
        self.equipped: list[Card] = []
        self.can_go_on: Union[int, tuple[int, ...]] = ANIMAL_TYPE, TALISMAN_TYPE, EQUIPMENT_TYPE, LAND_TYPE, INCANTATION_TYPE

        # other
        self.is_cow = False

    def mod_x(self):
        return self.x-get_local_player().camera.x

    def mod_y(self):
        return self.y-get_local_player().camera.y

    def mod_pos(self):
        return self.mod_x(), self.mod_y()

    def reset_abilities(self):
        for ability in self.abilities:
            ability.activated = False

    def draw(self, surface: pygame.Surface):
        """Draw the card to the screen"""
        surface.blit(get_image(join("images", "cards", self.image), (0.5, 0.5)), self.mod_pos())

        for count, equipped in enumerate(self.equipped):
            equipped.x = self.x
            equipped.y = self.y + (count+1) * card_LOD
            equipped.draw(surface)

        # debug stuff
        if debug:
            draw_border_of_rect(surface, self.get_rect())

    def get_num_residents(self) -> int:
        return len(self.get_residents(self))

    def get_land_im_on(self, player: Player = None):
        for card_find in get_local_player().field.cards:
            if card_find.type == LAND_TYPE:
                if card_find.get_residents(player=player).__contains__(self):
                    return card_find
        return None

    @staticmethod
    def get_name(card_type):
        """Get the name of the card (e.g. greenest_grass.png -> Greenest Grass)"""
        # noinspection PyTypeHints
        card_type.image: str
        name = card_type.image.replace("_", " ")  # remove underscores
        name = name.split(" ")
        for word in name:
            name = word[0].upper() + word[1:-4]
        return "".join(name)

    def get_residents(self, card=None, player: Player = None) -> list:
        """Uses the local player if no player is specified"""
        def distance(p1: tuple[float, float], p2: tuple[float, float]) -> float: return sqrt(abs(p1[0]-p2[0])**2 + abs(p1[1]-p2[1])**2)
        if player is None:
            player = get_local_player()
        if card is None:
            card = self
        residents = []
        if card.type != LAND_TYPE:
            return residents
        if not player.field.cards.__contains__(card):
            raise TypeError(f"Object of type {card.type} cannot have residents")
        for card_try in player.field.cards:
            social_distance = distance((card.x+150, card.y+162), (card_try.x+150, card_try.y+162))
            if social_distance < 500:
                residents.append(card_try)
        if residents.__contains__(card):
            residents.remove(card)
        return residents

    def get_rect(self):
        """The queue means whether or not to follow queue protocols when in a lock slot"""
        rect = get_image(join("images", "cards", self.image), (0.5, 0.5)).get_rect(topleft=(self.mod_x(), self.mod_y()))
        return rect

    def handle_action(self, action: int) -> Union[None, list[Action, DelayedAction, InputAction]]:
        """This is where actions will get activated.
        Every card will have this function called when any action is done but then the cards will use if statements
        to determine if the card is eligible to perform a special thing on that action or not"""
        pass

    def handle_events(self, event: pygame.event.Event, rel: tuple[int, int], rect_h=None) -> int:
        global debug

        rect_of_self = self.get_rect()
        rect_of_self.h += card_LOD*len(self.equipped)
        if rect_h is not None:
            rect_of_self.h = rect_h
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if rect_of_self.collidepoint(pygame.mouse.get_pos()):
                    self.selected = True
                    return pygame.MOUSEBUTTONDOWN
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.selected = False
                return pygame.MOUSEBUTTONUP
        if event.type == pygame.WINDOWLEAVE:
            self.selected = False
        if event.type == pygame.MOUSEMOTION:
            if self.selected:
                if self.type != LAND_TYPE or rel == (0, 0):
                    self.y += rel[1]
                    self.x += rel[0]
                else:
                    other_lands = [card for card in get_local_player().field.cards if card.type == LAND_TYPE]
                    other_lands.remove(self)
                    centers = [(land.x+125, land.y+162) for land in other_lands]
                    def pyth_theorem(pos1, pos2): return sqrt((pos1[0]-pos2[0])**2+(pos1[1]-pos2[1])**2)
                    for _ in range(land_collision_accuracy):
                        self.x += rel[0]/land_collision_accuracy
                        for center in centers:
                            self_center = (self.x+125, self.y+162)
                            while pyth_theorem(center, self_center) < 1000:
                                self.x -= rel[0]/10
                                self_center = (self.x+125, self.y+162)
                                if pyth_theorem(center, self_center) > 1000:
                                    break
                        self.y += rel[1]/land_collision_accuracy
                        for center in centers:
                            self_center = (self.x+125, self.y+162)
                            while pyth_theorem(center, self_center) < 1000:
                                self.y -= rel[1]/10
                                self_center = (self.x+125, self.y+162)
                                if pyth_theorem(center, self_center) > 1000:
                                    break

        return False

    def __str__(self):
        return f"Card(<name={self.image}, type={self.type}, x={self.x}, y={self.y}>)"


class Castle(Card):
    image = "castle.png"

    def __init__(self, pos: Union[list[int], tuple[int, int]] = (100, 100)):
        super().__init__(pos)
        self.type = LAND_TYPE
        # cost is free

    def handle_action(self, action: int) -> Union[list[Action, DelayedAction, InputAction], None]:
        if action == SELF_TURN_START:
            return [Action(self, SELF_GIVE_HAY, 2)]
        return None


class Arson(Card):
    image = "arson.png"

    def __init__(self, pos: Union[list[int], tuple[int, int]] = (100, 100)):
        super().__init__(pos)
        self.type = INCANTATION_TYPE
        self.abilities = [Ability(InputAction(self, REMOVE_CHOSEN_CARD, 1, PICK_LAND,
                                              ActionConditional(self, REQ_CARD_NUM_RESIDENTS,
                                                                COND_OPERATOR_LESS_THAN, 2)), 3, DAIRY_DOLLAR)]


class GreenestGrass(Card):
    image = "greenestgrass.png"

    def __init__(self, pos: Union[list[int], tuple[int, int]] = (100, 100)):
        super().__init__(pos)
        self.type = EQUIPMENT_TYPE
        self.cost_amount = 3
        self.cost_currency = HAY_COUNTER
        self.abilities = [Ability(Action(self, SELF_GIVE_MONEY, NUM_PLAYERS), 3, HAY_COUNTER, "+X money"),
                          Ability(Action(self, SELF_GIVE_MONEY, 1), 1, MILK_COUNTER, "Milk to dollar")]
        self.can_go_on = ANIMAL_TYPE


class KingCow(Card):
    image = "kingcow.png"

    def __init__(self, pos: Union[list[int], tuple[int, int]] = (100, 100)):
        super().__init__(pos)
        self.type = ANIMAL_TYPE
        self.is_cow = True
        # notice how the cost is free
        self.abilities = [Ability(Action(self, SELF_GIVE_MONEY, SELF_COWS_ON_FIELD), 1, HAY_COUNTER, "Tax the poor"),
                          Ability(DelayedAction(self, SELF_GIVE_HAY, 1, SELF_TURN_START), 2, HAY_COUNTER,
                                  "Bribe the king")]


class BlackBrie(Card):
    image = "blackbrie.png"

    def __init__(self, pos: Union[list[int], tuple[int, int]] = (100, 100)):
        super().__init__(pos)
        self.type = INCANTATION_TYPE
        self.abilities = [Ability(Action(self, SELF_GIVE_MONEY, 2), 0, DAIRY_DOLLAR)]
