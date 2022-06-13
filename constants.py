from pygame import Color
# noinspection PyBroadException
try:
    # noinspection PyPackageRequirements
    from win32api import EnumDisplayDevices, EnumDisplaySettings
    FRAMERATE = EnumDisplaySettings(EnumDisplayDevices().DeviceName, -1).DisplayFrequency
except Exception:  # for whatever reason, if cannot find it or error with the module
    FRAMERATE = 60

# game events (G ame E vents) (causation) (also for delayed actions)
GE_SELF_TURN_START = 100
GE_ANY_TURN_START = 101
GE_SELF_PLAY_CARD = 102
GE_SELF_DRAW_CARD = 103
GE_SELF_DISCARD_CARD = 106
GE_SELF_COW_ABILITY = 109

# currency constants
DOLLAR = 900
MILK = 901
HAY = 902

# card types
TYPE_ANIMAL = 1000
TYPE_LAND = 1001
TYPE_EQUIPMENT = 1002
TYPE_INCANTATION = 1003
TYPE_TALISMAN = 1004

# input action choose types
PICK_PLAYER = 10000
PICK_CARD = 10001
PICK_COW = 10002
PICK_ANIMAL = 10003
PICK_LAND = 10004

# effect action type
DO_SELF_GIVE_DOLLAR = 2000
DO_SELF_GIVE_MILK = 2002
DO_SELF_GIVE_HAY = 2001
DO_STEAL_DOLLAR_FROM_ALL_OPPONENTS = 2003
DO_DISCARD_THIS_CARD = 2004
DO_SELF_DRAW_DAIRY_COW = 2005
DO_SELF_DRAW_MANURE = 2006
DO_TAKE_TOP_DISCARD_CARD = 2007

# variable placeholders (PL ace holders)
PL_SELF_TURNS_PASSED = 5000
PL_SELF_NUM_COWS_ON_FIELD = 5001
PL_SELF_DOLLAR_AMOUNT = 5002
PL_SELF_MILK_AMOUNT = 5003
PL_SELF_HAY_AMOUNT = 5004
PL_SELF_NUM_CARDS_ON_FIELD = 5005
PL_NUM_PLAYERS = 5006
PL_LAST_CARD_CHOSEN = 5007
PL_SELF_NUM_CARDS_IN_HAND = 5008
PL_SELF_NUM_ANIMAL_ON_FIELD = 5009

# conditional requirements (REQ uirements)
REQ_CARD_NUM_RESIDENTS = 12000

# conditional operators (COND itional operators)
COND_OPERATOR_EQUALS = 11000
COND_OPERATOR_LESS_THAN = 11001
COND_OPERATOR_MORE_THAN = 11002

# screen types
GAME_SCREEN = -10
LOBBY_SCREEN = -11
MAIN_MENU_SCREEN = -12
DECK_BUILDER_SCREEN = -13

# colors
BG_COLOR = Color(169, 228, 239)
DARK_BG_COLOR = Color(165, 210, 234)
MAIN_COLOR = Color(129, 244, 149)
