from yugo_tools import *
from effects import *
from pygamepopups import PauseMenu
# noinspection PyUnresolvedReferences
from packets import *
from cows import *
import pygame
from deckbuilder import DeckBuilder
pygame.init()

# pygame variables
WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
set_yugo_framerate(FRAMERATE)
screen = pygame.display.set_mode([WIDTH, HEIGHT], pygame.FULLSCREEN | pygame.SCALED | pygame.HWACCEL | pygame.HWSURFACE, vsync=1)
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

# deck builder
deck_builder = DeckBuilder("settings.pickle", font, small_font)
deck_builder.inject_deck(deck_builder.decks[0], get_local_player())


def set_screen(scr: int):
    global viewing_screen
    viewing_screen = scr
    if viewing_screen == GAME_SCREEN:
        if not get_local_player().has_drawn_starting:
            get_local_player().has_drawn_starting = True
            get_local_player().draw_starting_hand()
    if viewing_screen == DECK_BUILDER_SCREEN:
        deck_builder.inject_deck(deck_builder.selected_deck, get_local_player())
    play_sound(calming_ding_sound, 0.4)


def exit_cows():
    global running
    running = False


def minimize_cows(): pygame.display.iconify()


def packet_thread():
    pass


def window_buttons(back=True):
    minimize_button.draw(screen)
    exit_button.draw(screen)
    if back:
        back_button.draw(screen)
    for event in events:
        minimize_button.handle_events(event)
        exit_button.handle_events(event)
        if back:
            back_button.handle_events(event)


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
back_button = Button((WIDTH-80, 50, 70, 30), font, set_screen, MAIN_MENU_SCREEN, text="<")
exit_button = Button((WIDTH-40, 10, 30, 30), font, action=exit_cows, text="x")
minimize_button = Button((WIDTH-80, 10, 30, 30), font, action=minimize_cows, text="-")

# game ui
next_step_button = Button((10, HEIGHT-47, 156, 30), small_font, action=next_step, text="draw a card")
pause_menu = PauseMenu()
turn_count_text = Text((10, 10, 300, 60), font, "first turn", "topleft")


# main menu ui
server_input_box = InputBox(pygame.Rect(WIDTH/2-100, HEIGHT/2+50, 200, 40), font, text_if_no_text="enter ip here")
join_server_button = Button((WIDTH/2-100, HEIGHT/2+110, 200, 80), font, lambda: None, text="Join Server", color=(3, 206, 164))
sandbox_button = Button((WIDTH/2-100, HEIGHT/2+210, 200, 80), font, set_screen, GAME_SCREEN, text="Sandbox", color=(252, 202, 70))
deck_build_button = Button((WIDTH/2-100, HEIGHT/2+310, 200, 80), font, set_screen, DECK_BUILDER_SCREEN, text="Deck Builder", color=(230, 57, 70))
logo_image = get_image(join("images", "logo.png"))

# debug ui thingies
fps_text = Text((10, 10), font, "fps: 0", alignment="topleft")
mouse_pos_text = Text((10, 70), font, "mouse pos: (0, 0)", alignment="topleft")
cashes_text = Text((10, 100), font, "None", alignment="topleft")
camera_pos_text = Text((10, 130), font, "camera pos here", alignment="topleft")


# sounds
coin_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "coin.mp3"))
fold_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "cardfold.mp3"))
default_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "default.mp3"))
calming_ding_sound = pygame.mixer.Sound(join(getcwd(), "sounds", "ding.mp3"))


def stop_game():
    global running
    running = False


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

    # draw ui elements
    join_server_button.draw(screen)
    sandbox_button.draw(screen)
    server_input_box.draw(screen)
    deck_build_button.draw(screen)
    logo_rect = logo_image.get_rect(center=(WIDTH/2, HEIGHT/2-200))
    screen.blit(logo_image, logo_rect)


def draw_deck_builder():
    global viewing_screen
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                set_screen(MAIN_MENU_SCREEN)
                deck_builder.save_to_disk()
                deck_builder.inject_deck(deck_builder.selected_deck, get_local_player())

        deck_builder.handle_events(event)
    deck_builder.draw(screen)


def black_intro_screen():
    if 25-(3*(tick-FRAMERATE)*DELTATIME) > 0:
        ALL_BLACK_SURF.set_alpha(clamp(25-(3*(tick-FRAMERATE)*DELTATIME), 0, 255))
        screen.blit(ALL_BLACK_SURF, (0, 0))


def relocate_mouse_events():
    """move mouse motion events to the back"""
    kl_list = []
    for event_move in events:
        if event_move.type == pygame.MOUSEMOTION:
            kl_list.append(event_move)
    for hit_target in kl_list:
        events.remove(hit_target)
        events.append(hit_target)


running = True
while running:
    screen.fill(BG_COLOR)
    mouse_loc = pygame.mouse.get_pos()
    rel = pygame.mouse.get_rel()
    events = pygame.event.get()
    relocate_mouse_events()

    # dont register events until blackscreen starts fading
    if tick/FRAMERATE < 0.2:
        events = []

    # game menu
    if viewing_screen == GAME_SCREEN:
        draw_game()

    window_buttons(True)

    # main menu
    if viewing_screen == MAIN_MENU_SCREEN:
        draw_main_menu()

    # deck builder menu
    elif viewing_screen == DECK_BUILDER_SCREEN:
        draw_deck_builder()

    # update stuff
    black_intro_screen()
    draw_debug()
    update_popups(screen, FRAMERATE)
    pygame.display.flip()
    clock.tick(FRAMERATE)
    tick += 1
pygame.quit()
deck_builder.save_to_disk()
