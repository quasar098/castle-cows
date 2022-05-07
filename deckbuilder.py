from settingshandler import SettingsHandler
from cows import *


DEFAULT_LOOT_POOL = {
    KingCow: 4,
    Castle: 4,
    GreenestGrass: 2
}


class Deck:
    def __init__(self, name):
        self.name: str = name
        self.loot_pool: dict[type(Card), int] = DEFAULT_LOOT_POOL

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


DEFAULT_DECK = Deck("Default Deck")


class DeckBuilder:
    def __init__(self, savefile):
        self.decks: list[Deck] = []
        self.settings_handler = SettingsHandler(savefile)
        self.settings_handler.register_state("decks", [DEFAULT_DECK])
        self.reload_from_disk()
        self.selected_deck_id = id(self.decks[0])
        self.max_decks = 4

    def reload_from_disk(self):
        self.decks = self.settings_handler.get_state("decks")

    def save_to_disk(self):
        self.settings_handler.set_state("decks", self.decks)

    def create_deck(self, name: str):
        self.decks.append(Deck(name))

    def copy_deck(self, deck: Deck):
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

    def get_deck_by_id(self, id_: int) -> Deck:
        for _ in self.decks:
            if id(_) == id_:
                return _
        raise NotImplementedError(f"no deck found (attempt was: {id_})")

    def inject_deck(self, deck: Deck, player: Player):
        player.loot_pool = deck.loot_pool

    @property
    def selected_deck(self):
        return self.get_deck_by_id(self.selected_deck_id)
