from yugo_tools import *
from effects import *
from pygamepopups import PauseMenu
# noinspection PyUnresolvedReferences
from packets import *
from cows import *
import pygame
from deckbuilder import DeckBuilder

# noinspection PyBroadException
try:
    # noinspection PyPackageRequirements
    from win32api import EnumDisplayDevices, EnumDisplaySettings
    FRAMERATE = EnumDisplaySettings(EnumDisplayDevices().DeviceName, -1).DisplayFrequency
except Exception:  # for whatever reason, if cannot find it or error with the module
    FRAMERATE = 60

pygame.init()

# colors
BG_COLOR = pygame.Color(169, 228, 239)
DARK_BG_COLOR = pygame.Color(165, 210, 234)
MAIN_COLOR = pygame.Color(129, 244, 149)

# pygame variables
WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
set_yugo_framerate(FRAMERATE)
screen = pygame.display.set_mode([WIDTH, HEIGHT], pygame.FULLSCREEN | pygame.SCALED | pygame.HWACCEL, vsync=1)
pygame.display.set_caption("Castle Cows Online")
DELTATIME = 75/FRAMERATE
font = pygame.font.SysFont("Arial", 30)
small_font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()
tick = 0

# big surfaces
ALL_BLACK_SURF = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
ALL_BLACK_SURF.fill((0, 0, 0))
PUTTING_IN_HAND_SURFACE = pygame.Surface((WIDTH, 170), pygame.SRCALPHA)
PUTTING_IN_HAND_SURFACE.fill((0, 0, 0))
PUTTING_IN_HAND_SURFACE.set_alpha(50)
HAND_BG_SURFACE = pygame.Surface((WIDTH, 170), pygame.SRCALPHA)
HAND_BG_SURFACE.fill(DARK_BG_COLOR)
HAND_BG_SURFACE.set_alpha(150)
DARK_BG_SURFACE = get_image(join("images", "darkbg.png"))

# game vars
get_local_player().update_visible_currencies()
right_click_menu = RightClickMenu()

# which screen
viewing_screen = MAIN_MENU_SCREEN


def exit_cows():
    global running
    running = False


def minimize_cows(): pygame.display.iconify()


def packet_thread():
    pass


def back_to_home():
    global viewing_screen
    viewing_screen = MAIN_MENU_SCREEN
    get_local_player().loot_pool = deck_builder.selected_deck.loot_pool


# deck builder
deck_builder = DeckBuilder("settings.pickle")
deck_builder.inject_deck(deck_builder.decks[0], get_local_player())


def next_step():
    play_sound(default_sound, 0.4)
    if not get_local_player().is_my_turn:
        add_debug_popup("not ur turn bro", small_font)
        return
    if get_local_player().next_turn_step():
        return
    get_local_player().update_visible_currencies()
    step_texts = {"collect": "draw a card", "draw": "use your cards", "use": "end your turn"}  # what the button will say
    next_step_button.change(text=step_texts[get_local_player().step], color=(0, 0, 0))
    if get_local_player().step == "collect":  # new turn
        get_local_player().hay = 0
        get_local_player().visible_hay = 0
        get_local_player().handle_card_actions(GE_SELF_TURN_START)
        get_local_player().reset_abilities()
        turn_count_text.change(font, f"{get_statistics_manager().turns_passed} turn{(get_statistics_manager().turns_passed>1)*'s'} passed")
    if get_local_player().step == "draw":
        play_sound(fold_sound, 0.5)


# important ui
back_button = Button((WIDTH-80, 50, 70, 30), font, action=back_to_home, text="<")
exit_button = Button((WIDTH-40, 10, 30, 30), font, action=exit_cows, text="x")
minimize_button = Button((WIDTH-80, 10, 30, 30), font, action=minimize_cows, text="-")

# game ui
next_step_button = Button((10, HEIGHT-47, 156, 30), small_font, action=next_step, text="draw a card")
pause_menu = PauseMenu()
turn_count_text = Text((10, 10, 300, 60), font, "first turn", "topleft")


def join_sandbox():
    global viewing_screen
    viewing_screen = GAME_SCREEN
    play_sound(calming_ding_sound, 0.6)
    get_local_player().draw_starting_hand()
    sandbox_button.pressed = False
    get_local_player().in_sandbox = True


def join_deck_builder():
    global viewing_screen
    viewing_screen = DECK_BUILDER_SCREEN
    play_sound(calming_ding_sound, 0.6)
    deck_build_button.pressed = False


# main menu ui
server_input_box = InputBox(pygame.Rect(WIDTH/2-100, HEIGHT/2-150, 200, 40), font, text_if_no_text="enter ip here", allowed_chars="0123456789.")
join_server_button = Button((WIDTH/2-100, HEIGHT/2-90, 200, 80), font, action=lambda: None, text="Join Server", color=(3, 206, 164))
sandbox_button = Button((WIDTH/2-100, HEIGHT/2+10, 200, 80), font, action=join_sandbox, text="Sandbox", color=(252, 202, 70))
deck_build_button = Button((WIDTH/2-100, HEIGHT/2+110, 200, 80), font, action=join_deck_builder, text="Deck Builder", color=(230, 57, 70))

# debug ui thingies
fps_text = Text((10, 10), font, "fps: 0", alignment="topleft")
mouse_pos_text = Text((10, 70), font, "mouse pos: (0, 0)", alignment="topleft")
cashes_text = Text((10, 100), font, "None", alignment="topleft")
camera_pos_text = Text((10, 130), font, "camera pos here", alignment="topleft")


def make_new_deck():
    if len(deck_builder.decks) < deck_builder.max_decks:
        deck_builder.create_deck(f"New Deck")
    else:
        add_popup(f"You can only have {deck_builder.max_decks} decks maximum")


def copy_deck():
    if len(deck_builder.decks) < deck_builder.max_decks:
        deck_builder.copy_deck(deck_builder.selected_deck)
    else:
        add_popup(f"You can only have {deck_builder.max_decks} decks maximum")


def delete_deck():
    if len(deck_builder.decks) > 1:
        deck_builder.decks.remove(deck_builder.selected_deck)
        deck_builder.selected_deck_id = id(deck_builder.decks[0])


def add_card_to_sel_deck():
    # for simplicity
    deck_add_list_items = [_ for _ in list(deck_add_item_cards_list.values())]

    # add if not there already
    if deck_add_list_items[deck_add_item_index] not in deck_builder.selected_deck.loot_pool:
        deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]] = 0

    # change it
    deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]] += 1

    # clamp
    deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]] = \
        clamp(deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]], 0, 4)


def remove_card_from_sel_deck():
    # for simplicity
    deck_add_list_items = [_ for _ in list(deck_add_item_cards_list.values())]

    # add if not there already
    if deck_add_list_items[deck_add_item_index] not in deck_builder.selected_deck.loot_pool:
        deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]] = 0

    # change it
    deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]] -= 1

    # clamp
    deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]] = \
        clamp(deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]], 0, 4)

    # remove if 0
    if not deck_builder.selected_deck.loot_pool[deck_add_list_items[deck_add_item_index]]:
        deck_builder.selected_deck.loot_pool.pop(deck_add_list_items[deck_add_item_index])


def see_different_card(move: int = 1):
    global deck_add_item_index
    deck_add_item_index = divmod(move+deck_add_item_index, len(deck_add_item_cards_list))[1]


# deck selecter ui
deck_select_space = 600
deck_create_button = Button((10, 10, WIDTH/2-deck_select_space/2-20, 90), font, action=make_new_deck, text="Make new deck")
deck_delete_button = Button((10, 110, WIDTH / 2 - deck_select_space / 2 - 20, 90), font, action=delete_deck, text="Delete selected deck")
deck_copy_button = Button((10, 210, WIDTH/2 - deck_select_space/2-20, 90), font, action=copy_deck, text="Copy selected deck")
deck_name_change = InputBox(pygame.Rect(WIDTH/2+deck_select_space/2+10, 10, WIDTH/2-deck_select_space/2-110, 40), small_font, text_if_no_text="deck name")
deck_add_card_button = Button((10, HEIGHT-230, WIDTH/2-deck_select_space/2-20, 100), font, action=add_card_to_sel_deck, text="Add card to selected deck")
deck_remove_card_button = Button((10, HEIGHT-120, WIDTH/2-deck_select_space/2-20, 100), font, action=remove_card_from_sel_deck, text="Remove card from selected deck")

# deck selecter items list
deck_add_item_cards_list = {card.get_name(card): card for card in Card.__subclasses__()}
deck_add_item_cards_list = dict(sorted(deck_add_item_cards_list.items(), reverse=True))
deck_add_item_index = len(deck_add_item_cards_list)-1
_ = pygame.Rect(0, 0, WIDTH/2-deck_select_space/2-20-80, 50)
_.midbottom = deck_add_card_button.rect.midtop
deck_add_item_rect = _.move(0, -10)
deck_next_card_button = Button((0, 0, 30, 50), font, see_different_card, text="<")
deck_next_card_button.rect.midright = deck_add_item_rect.move(-10, 0).midleft
deck_prev_card_button = Button((0, 0, 30, 50), font, see_different_card, -1, text=">")
deck_prev_card_button.rect.midleft = deck_add_item_rect.move(10, 0).midright

# sounds
coin_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "coin.mp3"))
fold_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "cardfold.mp3"))
default_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "default.mp3"))
calming_ding_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "ding.mp3"))


def stop_game():
    global running
    running = False


def change_screen(change_to: int):
    global viewing_screen
    viewing_screen = change_to


def draw_debug():
    if get_debug():
        fps_text.change(text=f"fps: {int(clock.get_fps())}")
        fps_text.draw(screen)
        mouse_pos_text.change(text=f"mouse pos: {pygame.mouse.get_pos()}")
        mouse_pos_text.draw(screen)
        cashes_text.change(text=f"cache: {get_local_player().dollar}, {get_local_player().milk}, {get_local_player().hay}")
        cashes_text.draw(screen)
        camera_pos_text.change(text=f"{get_local_player().camera}")
        camera_pos_text.draw(screen)
    for ev in events:
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_F11:
                toggle_debug()


def draw_game():
    def create_rcm_ability(ab) -> RightClickAbility:
        """Return a right click ability from an ability"""
        if isinstance(ab, list):
            ab2 = ab[0]
            return RightClickAbility(
                f"Ability: {ab2.name}", ab, get_local_player().can_pay_for(ab2.currency, ab2.cost) * (1-ab2.activated)
            )
        else:
            return RightClickAbility(
                f"Ability: {ab.name}", ab, get_local_player().can_pay_for(ab.currency, ab.cost) * (1-ab.activated)
            )
    for ev in events:
        if ev.type == pygame.QUIT:
            stop_game()

        # pause menu
        if pause_menu.handle_events(ev):
            break

        # right click abilities
        ability_rcm = right_click_menu.handle_events(ev)
        if ability_rcm and get_local_player().step == "collect":
            add_popup("You must draw a card first!")
            ability_rcm = False
        if isinstance(ability_rcm, Ability):
            ability_rcm.activate()
            get_local_player().clear_queue()
            break
        if isinstance(ability_rcm, list):
            for ability in ability_rcm:
                ability.activate()
            get_local_player().clear_queue()
            break

        # right click menu + debug things
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 3:
                for card_rcm_hitbox in get_local_player().get_cards_recursively().__reversed__():
                    if card_rcm_hitbox.get_rect().collidepoint(mouse_loc):
                        card_right_click_list = []
                        for ability in card_rcm_hitbox.abilities:
                            card_right_click_list.append(create_rcm_ability(ability))
                        right_click_menu.show(card_right_click_list)
                        break

        # camera controls
        if ev.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed(3)[2]:
                get_local_player().camera.x -= rel[0]
                get_local_player().camera.y -= rel[1]
                right_click_menu.x += rel[0]
                right_click_menu.y += rel[1]

        # card controls (both hand and field)
        if not get_local_player().doing_input_action:
            exit_button.handle_events(ev)
            minimize_button.handle_events(ev)
        if len(get_local_player().drawing_fake_cards) == 0:
            if next_step_button.handle_events(ev):
                break
        else:
            next_step_button.pressed = False
        if get_local_player().handle_events(ev, rel):
            break

        # popup handling
        handle_popup_events(ev)
        handle_cows_popups(ev)

    get_local_player().field.draw(screen, FRAMERATE)
    screen.blit(HAND_BG_SURFACE, (0, HEIGHT-168))
    get_local_player().hand.draw(screen, FRAMERATE)

    # bottom bar draw
    my_turn = get_local_player().is_my_turn
    get_local_player().draw(screen, small_font)
    next_step_button.color = pygame.Color(190+int(my_turn)*65, 190+int(my_turn)*65, 190+int(my_turn)*65)
    next_step_button.draw(screen)

    # important ui buttons
    if not get_local_player().doing_input_action:
        exit_button.draw(screen)
        minimize_button.draw(screen)
        turn_count_text.draw(screen)

    # currency particles
    remove_currency_particles = []
    for currency_particle in get_currency_particles():
        if currency_particle.draw(screen, FRAMERATE):
            remove_currency_particles.append(currency_particle)
    for remove_currency_particle in remove_currency_particles:
        coin_col = (255, 0, 0)
        if remove_currency_particle.currency == "money.png":
            get_local_player().visible_money += 1
            coin_col = (94, 252, 141)
        if remove_currency_particle.currency == "milk.png":
            get_local_player().visible_milk += 1
            coin_col = (163, 247, 255)
        if remove_currency_particle.currency == "hay.png":
            get_local_player().visible_hay += 1
            coin_col = (245, 230, 99)
        play_sound(coin_sound)
        for _ in range(10):
            get_circle_particles().append(CircleParticle((remove_currency_particle.x, remove_currency_particle.y), color=coin_col))
        get_currency_particles().remove(remove_currency_particle)

    # circle particles
    for particle in get_circle_particles():
        if particle.draw(screen, FRAMERATE):
            get_circle_particles().remove(particle)

    # right click menu
    right_click_menu.draw(screen)

    # cows popups
    draw_cows_popups(screen, FRAMERATE)

    # start up dark screen
    if len(get_local_player().drawing_fake_cards) > 0 or pause_menu.shown:
        screen.blit(DARK_BG_SURFACE, (0, 0))

    # draw fake cards
    get_local_player().draw_fake_cards(screen, FRAMERATE)

    # pause menu
    pause_menu.draw(screen)


def draw_main_menu():
    for ev in events:
        if ev.type == pygame.QUIT:
            stop_game()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                stop_game()

        # handle ui elements
        join_server_button.handle_events(ev)
        sandbox_button.handle_events(ev)
        server_input_box.handle_events(ev)
        deck_build_button.handle_events(ev)

        # handle important ui
        minimize_button.handle_events(ev)
        exit_button.handle_events(ev)

    # draw important ui
    minimize_button.draw(screen)
    exit_button.draw(screen)

    # draw ui elements
    join_server_button.draw(screen)
    sandbox_button.draw(screen)
    server_input_box.draw(screen)
    deck_build_button.draw(screen)


def draw_deck_builder():
    global deck_add_item_index
    deck_name_change.change(text=deck_builder.selected_deck.name, font=small_font)
    for ev in events:
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                change_screen(MAIN_MENU_SCREEN)

        # new deck button and stuff
        deck_create_button.handle_events(ev)
        deck_delete_button.handle_events(ev)
        deck_copy_button.handle_events(ev)
        if deck_name_change.handle_events(ev):
            deck_builder.selected_deck.name = deck_name_change.text

        # important ui buttons
        exit_button.handle_events(ev)
        minimize_button.handle_events(ev)
        back_button.handle_events(ev)

        # handle cows popups
        handle_cows_popups(ev)

        # handle decks and selecting them
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                escaped = False
                for deck_count, deck in enumerate(deck_builder.decks):
                    deck_height = screen.get_height()/deck_builder.max_decks
                    rect = pygame.Rect(WIDTH / 2 - deck_select_space / 2, deck_count * deck_height, deck_select_space, deck_height)
                    if rect.inflate(-16, -16).collidepoint(pygame.mouse.get_pos()):
                        deck_builder.selected_deck_id = id(deck)
                        escaped = True
                        break
                if escaped:
                    break

        # handle adding items to the selected deck
        if ev.type == pygame.MOUSEWHEEL:
            if deck_add_item_rect.collidepoint(pygame.mouse.get_pos()):
                deck_add_item_index = divmod(ev.y + deck_add_item_index, len(deck_add_item_cards_list))[1]
        deck_prev_card_button.handle_events(ev)
        deck_next_card_button.handle_events(ev)

        # add and removing cards handling
        deck_add_card_button.handle_events(ev)
        deck_remove_card_button.handle_events(ev)

    # draw new deck button and others
    deck_create_button.draw(screen)
    deck_delete_button.draw(screen)
    deck_name_change.draw(screen)
    deck_add_card_button.draw(screen)
    deck_remove_card_button.draw(screen)
    deck_copy_button.draw(screen)

    # deck add item chooser
    pygame.draw.rect(screen, (0, 0, 0), deck_add_item_rect.inflate(4, 4), border_radius=3)
    pygame.draw.rect(screen, (255, 255, 255), deck_add_item_rect, border_radius=3)
    deck_next_card_button.draw(screen)
    deck_prev_card_button.draw(screen)
    sel_add_option = list(deck_add_item_cards_list.keys())[deck_add_item_index]
    card_add_surf = fetch_text(f"Will add: {sel_add_option}", font)
    screen.blit(card_add_surf, card_add_surf.get_rect(center=deck_add_item_rect.center))

    # deck add item hover card
    hover_loc = deck_add_item_rect.midtop
    hover_loc = hover_loc[0], hover_loc[1]-10  # this sucks!!!!!!!!! where is my _move_pos function at???
    _ = deck_add_item_rect.midtop[1]-deck_delete_button.rect.midbottom[1]-20
    hover_img = get_image(join("images", "cards", list(deck_add_item_cards_list.values())[deck_add_item_index].image), (0.5, 0.5))
    screen.blit(hover_img, hover_img.get_rect(midbottom=hover_loc))

    # lines going up and down
    for _ in range(2):
        pygame.draw.line(screen, (30, 30, 30), (WIDTH/2-deck_select_space/2+_*deck_select_space, 10),
                         (WIDTH/2-deck_select_space/2+_*deck_select_space, HEIGHT-10), width=3)

    # important ui buttons
    exit_button.draw(screen)
    back_button.draw(screen)
    minimize_button.draw(screen)

    # draw decks in middle column
    for deck_count, deck in enumerate(deck_builder.decks):
        deck_height = screen.get_height()/deck_builder.max_decks
        rect = pygame.Rect(WIDTH / 2 - deck_select_space / 2, deck_count * deck_height, deck_select_space, deck_height)
        pygame.draw.rect(screen, (0, 0, 0), rect.inflate(-12, -12), border_radius=6)
        inner_color = pygame.Color(255, 255, 255)
        if id(deck) == deck_builder.selected_deck_id:
            inner_color = pygame.Color(102, 153, 204)
        if rect.inflate(-16, -16).collidepoint(pygame.mouse.get_pos()):
            inner_color = inner_color.lerp((0, 0, 0), pygame.mouse.get_pressed(3)[0]*0.2)
        pygame.draw.rect(screen, inner_color, rect.inflate(-16, -16), border_radius=4)
        screen.blit(fetch_text(deck.name, font), fetch_text(deck.name, font).get_rect(center=rect.center))

    # drawing cards in deck on the right column
    right_rect = pygame.Rect(WIDTH/2+deck_select_space/2, 80, deck_select_space, screen.get_height()-80)
    sel_deck = deck_builder.selected_deck
    for count, card_desc in enumerate(sel_deck.loot_pool):
        amount_of_card = sel_deck.loot_pool[card_desc]
        card_desc: Card
        amount_of_card: int
        text_surf = fetch_text(f"{card_desc.get_name(card_desc)} (x{amount_of_card})", font=small_font)
        screen.blit(text_surf, text_surf.get_rect(midleft=right_rect.move(20, count*30).topleft))

    # cows popups
    draw_cows_popups(screen, FRAMERATE)


def black_intro_screen():
    if 255-(3*(tick-FRAMERATE)*DELTATIME) > 0:
        ALL_BLACK_SURF.set_alpha(clamp(255-(3*(tick-FRAMERATE)*DELTATIME), 0, 255))
        screen.blit(ALL_BLACK_SURF, (0, 0))


def relocate_mouse_events():
    """move mouse button events to the front"""
    kl_list = []
    for event_move in events:
        if event_move.type == pygame.MOUSEBUTTONDOWN:
            kl_list.append(event_move)
    for hit_target in kl_list:
        events.remove(hit_target)
        events.insert(0, hit_target)


running = True
while running:
    screen.fill(BG_COLOR)
    mouse_loc = pygame.mouse.get_pos()
    rel = pygame.mouse.get_rel()
    events = pygame.event.get()
    relocate_mouse_events()

    # dont register events until blackscreen starts fading
    if tick/FRAMERATE < 1.3:
        events = []

    # game menu
    if viewing_screen == GAME_SCREEN:
        draw_game()

    # main menu
    if viewing_screen == MAIN_MENU_SCREEN:
        draw_main_menu()

    # deck builder menu
    elif viewing_screen == DECK_BUILDER_SCREEN:
        draw_deck_builder()

    # primary pygame stuff

    black_intro_screen()
    draw_debug()
    update_popups(screen, FRAMERATE)
    pygame.display.flip()
    clock.tick(FRAMERATE)
    tick += 1
pygame.quit()
deck_builder.save_to_disk()
