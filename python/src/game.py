from enum import Enum

import numpy as np

from rl import Action, Game, State

DECKS = 1
VALUES = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
MAX_HANDS = 3


class Actions(Enum):
    HIT = 0
    STAND = 1
    DOUBLE_DOWN = 2
    SPLIT = 3
    INSURANCE_HALF = 4
    INSURANCE_FULL = 5


class BlackjackState(State):
    def __init__(self, s):
        self.s = s

    def unpack(self):
        return self.s

    def __hash__(self):
        s = list(self.s)
        for i in range(len(s)):
            if isinstance(s[i], np.ndarray):
                s[i] = self.s[i].tostring()
        return hash(tuple(s))

    def __str__(self):
        return str(self.s)


class BlackjackAction(Action):
    def __init__(self, a: Actions):
        self.a = a

    def unpack(self):
        return self.a

    def __hash__(self):
        return hash(self.a)

    def __str__(self):
        return str(self.a)


class Blackjack(Game):
    def __init__(self):
        self.deck = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10] * 4 * DECKS)

        self.actions = {
            Actions.HIT: self.hit,
            Actions.STAND: self.stand,
            Actions.DOUBLE_DOWN: self.double_down,
            Actions.SPLIT: self.split,
            Actions.INSURANCE_HALF: lambda: self.insurance(0.25),
            Actions.INSURANCE_FULL: lambda: self.insurance(0.5),
        }

    def state(self):
        return BlackjackState(
            (
                self.hero_hand,
                self.hero_has_ace,
                self.hero_can_split,
                self.hero_has_hit,
                self.bet_size,
                self.dealer_hand,
                self.current_hand,
                self.insurance_bet,
            )
        )

    def deal_card(self):
        card = self.deck[self.card_idx]
        self.card_idx += 1
        return card

    def setup_hand(self, idx, cards, bet_size):
        self.hero_hand[idx] = sum(cards)
        self.hero_has_ace[idx] = any(c == 1 for c in cards)
        self.hero_can_split[idx] = cards[0] == cards[1]
        self.hero_has_hit[idx] = False
        self.bet_size[idx] = bet_size

    def start_game(self, bet_size=1):
        # reset deck
        np.random.shuffle(self.deck)
        self.card_idx = 0

        # set up initial state
        self.current_hand = 0
        self.num_hands = 1

        self.hero_hand = np.zeros(MAX_HANDS)
        self.hero_has_ace = np.zeros(MAX_HANDS).astype(bool)
        self.hero_can_split = np.zeros(MAX_HANDS).astype(bool)
        self.hero_has_hit = np.zeros(MAX_HANDS).astype(bool)
        self.bet_size = np.zeros(MAX_HANDS)
        self.setup_hand(0, [self.deal_card(), self.deal_card()], bet_size)

        self.dealer_hand = self.deal_card()

        self.insurance_bet = 0

        self.terminal = False

        return self.state()

    def dealer_play(self):
        new_card = self.deal_card()
        has_ace = self.dealer_hand == 1 or new_card == 1
        self.dealer_hand += new_card
        if self.dealer_hand == 11 and has_ace:
            self.dealer_hand += 10
            return True  # blackjack

        while self.dealer_hand < 21:
            if 17 <= self.dealer_hand <= 21:
                break
            if 17 <= self.dealer_hand + 10 * has_ace <= 21:
                self.dealer_hand += 10 * has_ace
                break
            new_card = self.deal_card()
            has_ace = has_ace or new_card == 1
            self.dealer_hand += new_card
        return False

    def calculate_winnings(self):
        insurance_winnings = (
            self.insurance_bet if self.dealer_play() else -self.insurance_bet
        )

        played_hands = self.hero_hand[: self.num_hands]
        has_ace = self.hero_has_ace[: self.num_hands]

        hand_values = played_hands + 10 * has_ace
        hand_values[hand_values > 21] = played_hands[hand_values > 21]

        results = -np.ones_like(hand_values)
        results[hand_values == self.dealer_hand] = 0
        results[hand_values > self.dealer_hand] = 1
        results[self.dealer_hand > 21] = 1
        results[hand_values > 21] = 0  # already lost in hit

        results[
            (results == 1)
            & (played_hands == 11)
            & (has_ace)
            & ~self.hero_has_hit[: self.num_hands]
        ] = 1.5  # blackjack bonus

        return np.dot(results, self.bet_size[: self.current_hand]) + insurance_winnings

    def stand(self):
        self.current_hand += 1
        if self.current_hand == self.num_hands:
            self.terminal = True
            return self.calculate_winnings()
        else:
            return 0

    def hit(self):
        card = self.deal_card()
        self.hero_has_ace[self.current_hand] = (
            self.hero_has_ace[self.current_hand] or card == 1
        )
        self.hero_hand[self.current_hand] += card
        self.hero_has_hit[self.current_hand] = True
        if self.hero_hand[self.current_hand] > 21:
            return -self.bet_size[self.current_hand] + self.stand()
        else:
            return 0

    def double_down(self):
        self.bet_size[self.current_hand] *= 2
        reward = self.hit()
        if not self.terminal:
            reward += self.stand()
        return reward

    def split(self):
        card = self.hero_hand[self.current_hand] // 2
        self.setup_hand(
            self.current_hand,
            [card, self.deal_card()],
            self.bet_size[self.current_hand],
        )
        self.setup_hand(
            self.num_hands,
            [card, self.deal_card()],
            self.bet_size[self.current_hand],
        )
        self.num_hands += 1
        return 0

    def insurance(self, bet_size=0.5):
        self.insurance_bet = self.bet_size[self.current_hand] * bet_size
        return 0

    def perform_action(self, action):
        action = action.unpack()
        reward = self.actions[action]()
        return self.state(), reward

    def is_terminal(self):
        return self.terminal

    def get_actions(self):
        if self.terminal:
            return []
        actions = [Actions.HIT, Actions.STAND]
        if (
            not self.hero_has_hit[self.current_hand]
            and 9 <= self.hero_hand[self.current_hand] <= 11
        ):
            actions.append(Actions.DOUBLE_DOWN)
        if (
            not self.hero_has_hit[self.current_hand]
            and self.hero_can_split[self.current_hand] and self.num_hands < MAX_HANDS
        ):
            actions.append(Actions.SPLIT)
        if self.dealer_hand == 1 and self.insurance_bet == 0:
            actions.extend(
                [
                    Actions.INSURANCE_HALF,
                    Actions.INSURANCE_FULL,
                ]
            )
        return list(map(BlackjackAction, actions))
