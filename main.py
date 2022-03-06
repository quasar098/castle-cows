from yugo_tools import *
from effects import *
from pygamepopups import PauseMenu
from packets import *
from cows import *
import pygame
from win32api import EnumDisplayDevices, EnumDisplaySettings
from deckbuilder import DeckBuilder

pygame.init()

# colors
BG_COLOR = pygame.Color(169, 228, 239)
DARK_BG_COLOR = pygame.Color(165, 210, 234)
MAIN_COLOR = pygame.Color(129, 244, 149)

# pygame variables
WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
FRAMERATE = EnumDisplaySettings(EnumDisplayDevices().DeviceName, -1).DisplayFrequency
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


def minimize_cows():
    pygame.display.iconify()


def packet_thread():
    pass


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
    if not get_local_player().is_my_turn:
        next_step_button.change(text="not ur turn", color=(0, 0, 0))
        get_statistics_manager().turns_passed += 1
    if get_local_player().step == "collect":  # new turn
        get_local_player().hay = 0
        get_local_player().visible_hay = 0
        get_local_player().handle_card_actions(SELF_TURN_START)
        get_local_player().reset_abilities()
    if get_local_player().step == "draw":
        play_sound(fold_sound, 0.5)


# game ui
exit_button = Button((WIDTH-40, 10, 30, 30), font, action=exit_cows, text="x")
minimize_button = Button((WIDTH-80, 10, 30, 30), font, action=minimize_cows, text="-")
next_step_button = Button((10, HEIGHT-47, 156, 30), small_font, action=next_step, text="draw a card")
pause_menu = PauseMenu()


def join_sandbox():
    global viewing_screen
    viewing_screen = GAME_SCREEN
    play_sound(calming_ding_sound, 0.6)
    get_local_player().draw_card(4)
    sandbox_button.pressed = False


def join_deck_builder():
    global viewing_screen
    viewing_screen = DECK_SELECT_SCREEN
    play_sound(calming_ding_sound, 0.6)
    deck_build_button.pressed = False


# main menu ui
server_input_box = InputBox(pygame.Rect(WIDTH/2-100, HEIGHT/2-150, 200, 40), font, text_if_no_text="enter ip here", allowed_chars="0123456789.")
join_server_button = Button((WIDTH/2-100, HEIGHT/2-90, 200, 80), font, action=lambda: None, text="Join Server", color=(3, 206, 164))
sandbox_button = Button((WIDTH/2-100, HEIGHT/2+10, 200, 80), font, action=join_sandbox, text="Sandbox", color=(252, 202, 70))
deck_build_button = Button((WIDTH/2-100, HEIGHT/2+110, 200, 80), font, action=join_deck_builder, text="Deck Builder", color=(230, 57, 70))

# debug ui thingies
fps_text = Text((10, 10), font, "fps: 0", alignment="topleft")
packet_buffer_text = Text((10, 40), font, "No buffer data available", alignment="topleft")
mouse_pos_text = Text((10, 70), font, "mouse pos: (0, 0)", alignment="topleft")
cashes_text = Text((10, 100), font, "None", alignment="topleft")
camera_pos_text = Text((10, 130), font, "camera pos here", alignment="topleft")
debug_saved_packet_size = 0


def make_new_deck():
    if len(deck_builder.decks) < deck_builder.max_decks:
        deck_builder.create_deck(f"New Deck #{rand(0, 69420)}")  # hehe
    else:
        add_popup(f"You can only have {deck_builder.max_decks} decks maximum")


def delete_deck():
    if len(deck_builder.decks) > 1:
        deck_builder.decks.remove(deck_builder.selected_deck)
        deck_builder.selected_deck_id = id(deck_builder.decks[0])


def add_card_to_sel_deck():
    pass


# deck selecter ui
deck_select_space = 600
deck_create_button = Button((10, 10, WIDTH/2-deck_select_space/2-20, 90), font, action=make_new_deck, text="Make new deck")
deck_delete_button = Button((10, 110, WIDTH / 2 - deck_select_space / 2 - 20, 90), font, action=delete_deck, text="Delete selected deck")
deck_name_change = InputBox(pygame.Rect(WIDTH/2+deck_select_space/2+10, 10, WIDTH/2-deck_select_space/2-110, 40), small_font, text_if_no_text="deck name")
deck_add_card_button = Button((10, HEIGHT-120, WIDTH/2-deck_select_space/2-20, 100), font, action=add_card_to_sel_deck, text="Add card to selected deck")

# sounds
coin_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "coin.mp3"))
fold_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "cardfold.mp3"))
default_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "default.mp3"))
calming_ding_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "ding.mp3"))

running = True
while running:
    screen.fill(BG_COLOR)
    mouse_loc = pygame.mouse.get_pos()
    rel = pygame.mouse.get_rel()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_debug()

    # dont register events until blackscreen starts fading
    if 255-(5*(tick-FRAMERATE)*DELTATIME) > 0:
        events = []

    if viewing_screen == GAME_SCREEN:
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if pause_menu.handle_events(event):
                break
            ability_rcm = right_click_menu.handle_events(event)
            if isinstance(ability_rcm, Ability):
                ability_rcm.activate()
                get_local_player().clear_queue()
                break
            if isinstance(ability_rcm, list):
                for ability in ability_rcm:
                    ability.activate()
                get_local_player().clear_queue()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    for card_rcm_hitbox in get_local_player().get_cards_recursively().__reversed__():
                        if card_rcm_hitbox.get_rect().collidepoint(mouse_loc):
                            # right click menu options
                            card_right_click_list = []
                            if get_debug():
                                card_right_click_list.append(RightClickOption(f"[debug] get image",
                                                                              lambda: add_debug_popup(f"{card_rcm_hitbox.image}")))
                                card_right_click_list.append(RightClickOption(f"[debug] get pos",
                                                                              lambda: add_debug_popup(f"{card_rcm_hitbox.x, card_rcm_hitbox.y}")))
                                card_right_click_list.append(RightClickOption(f"[debug] is cow?",
                                                                              lambda: add_debug_popup(f"{card_rcm_hitbox.is_cow}")))
                            for ability in card_rcm_hitbox.abilities:
                                if isinstance(ability, list):
                                    ab2 = ability[0]
                                    card_right_click_list.append(RightClickAbility(f"Ability: {ab2.name}", ability,
                                                                                   get_local_player().can_pay_for(ab2.currency, ab2.cost)
                                                                                   * (1-ab2.activated)))

                                else:
                                    card_right_click_list.append(RightClickAbility(f"Ability: {ability.name}", ability,
                                                                                   get_local_player().can_pay_for(ability.currency, ability.cost)
                                                                                   * (1-ability.activated)))
                            right_click_menu.show(card_right_click_list)
                            break

            # camera controls
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed(3)[2]:
                    get_local_player().camera.x -= rel[0]
                    get_local_player().camera.y -= rel[1]
                    right_click_menu.x += rel[0]
                    right_click_menu.y += rel[1]

            # card controls (both hand and field)
            if not get_local_player().doing_input_action:
                exit_button.handle_events(event)
                minimize_button.handle_events(event)
            if len(get_local_player().drawing_fake_cards) == 0:
                if next_step_button.handle_events(event):
                    break
            else:
                next_step_button.pressed = False
            if get_local_player().handle_events(event, rel):
                break

            # popup handling
            handle_popup_events(event)
            handle_cows_popups(event)

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

        # debug stuff
        if get_debug():
            packet_buffer_text.change(text=f"packet size: {debug_saved_packet_size}")
            if tick % FRAMERATE == 0:
                debug_saved_packet_size = str(len(encode_packet(ClientPacket(PACKET_TYPE_REQUEST_GAME_INFO, get_local_player()))))
            packet_buffer_text.draw(screen)

        # pause menu
        pause_menu.draw(screen)

    # main menu
    if viewing_screen == MAIN_MENU_SCREEN:
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            # handle ui elements
            join_server_button.handle_events(event)
            sandbox_button.handle_events(event)
            server_input_box.handle_events(event)
            deck_build_button.handle_events(event)

        # draw ui elements
        join_server_button.draw(screen)
        sandbox_button.draw(screen)
        server_input_box.draw(screen)
        deck_build_button.draw(screen)

    # deck builder menu
    if viewing_screen == DECK_SELECT_SCREEN:
        deck_name_change.change(text=deck_builder.selected_deck.name, font=small_font)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    viewing_screen = MAIN_MENU_SCREEN

            # new deck button
            deck_create_button.handle_events(event)
            deck_delete_button.handle_events(event)
            if deck_name_change.handle_events(event):
                deck_builder.selected_deck.name = deck_name_change.text

            # important ui buttons
            exit_button.handle_events(event)
            minimize_button.handle_events(event)

            # handle cows popups
            handle_cows_popups(event)

            # handle decks and selecting them
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
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

        # draw new deck button
        deck_create_button.draw(screen)
        deck_delete_button.draw(screen)
        deck_name_change.draw(screen)

        # lines going up and down
        for _ in range(2):
            pygame.draw.line(screen, (30, 30, 30), (WIDTH/2-deck_select_space/2+_*deck_select_space, 10),
                             (WIDTH/2-deck_select_space/2+_*deck_select_space, HEIGHT-10), width=3)

        # important ui buttons
        exit_button.draw(screen)
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
                inner_color = inner_color.lerp((0, 0, 0), pygame.mouse.get_pressed(3)[0]*0.5)
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

    # black screen
    if 255-(3*(tick-FRAMERATE)*DELTATIME) > 0:
        ALL_BLACK_SURF.set_alpha(clamp(255-(3*(tick-FRAMERATE)*DELTATIME), 0, 255))
        screen.blit(ALL_BLACK_SURF, (0, 0))

    # debugging
    if get_debug():
        fps_text.change(text=f"fps: {int(clock.get_fps())}")
        fps_text.draw(screen)
        mouse_pos_text.change(text=f"mouse pos: {pygame.mouse.get_pos()}")
        mouse_pos_text.draw(screen)
        cashes_text.change(text=f"cache: {get_local_player().money}, {get_local_player().milk}, {get_local_player().hay}")
        cashes_text.draw(screen)
        camera_pos_text.change(text=f"{get_local_player().camera}")
        camera_pos_text.draw(screen)

    # primary pygame stuff
    update_popups(screen, FRAMERATE)
    pygame.display.flip()
    clock.tick(FRAMERATE)
    tick += 1
pygame.quit()
deck_builder.save_to_disk()
