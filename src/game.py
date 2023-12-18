from enum import Enum

import numpy as np

from rl import Action, Game, State

DECKS = 6
VALUES = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

class Actions(Enum):
    HIT = 0
    STAND = 1
    DOUBLE_DOWN = 2
    SPLIT = 3
    INSURANCE_1 = 4
    INSURANCE_2 = 5
    INSURANCE_3 = 6
    INSURANCE_4 = 7
    INSURANCE_5 = 8


class BlackjackState(State):
    def __init__(self, s):
        self.s = s

    def get(self):
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

    def get(self):
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
            Actions.INSURANCE_1: lambda: self.insurance(0.1),
            Actions.INSURANCE_2: lambda: self.insurance(0.2),
            Actions.INSURANCE_3: lambda: self.insurance(0.3),
            Actions.INSURANCE_4: lambda: self.insurance(0.4),
            Actions.INSURANCE_5: lambda: self.insurance(0.5),
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

        # self.player_hand = np.zeros((4 * DECKS, 10))
        # self.player_hand[self.current_hand][self.deal_card() - 1] += 1
        # self.player_hand[self.current_hand][self.deal_card() - 1] += 1
        self.hero_hand = np.zeros(4 * DECKS)
        self.hero_has_ace = np.zeros(4 * DECKS)
        self.hero_can_split = np.zeros(4 * DECKS)
        self.hero_has_hit = np.zeros(4 * DECKS)
        self.bet_size = np.zeros(4 * DECKS)
        self.setup_hand(0, [self.deal_card(), self.deal_card()], bet_size)
        
        self.dealer_hand = self.deal_card()

        self.insurance_bet = 0

        self.terminal = False

        return self.state()

    def dealer_play(self):
        has_ace = self.dealer_hand == 1
        while self.dealer_hand < 21:
            new_card = self.deal_card()
            if new_card == 10 and has_ace:
                return True  # blackjack
            has_ace = has_ace or new_card == 1
            self.dealer_hand += new_card
            if 17 <= self.dealer_hand <= 21:
                break
            if 17 <= self.dealer_hand + 10 * has_ace <= 21:
                self.dealer_hand += 10 * has_ace
                break
        return False

    def calculate_winnings(self):
        insurance_winnings = (
            self.insurance_bet if self.dealer_play() else -self.insurance_bet
        )

        played_hands = self.hero_hand[: self.current_hand]
        has_ace = self.hero_has_ace[: self.current_hand]
        results = -np.ones_like(played_hands)
        results[played_hands + 10 * has_ace == self.dealer_hand] = 0
        results[played_hands == self.dealer_hand] = 0
        results[played_hands + 10 * self.hero_has_ace > self.dealer_hand] = 1
        results[played_hands > self.dealer_hand] = 1
        results[self.dealer_hand > 21] = 1
        results[played_hands > 21] = 0  # already lost in hit

        results[(results == 1) & (played_hands == 11) & ~self.hero_has_hit[:self.current_hand]] = 1.5  # blackjack bonus

        # winnings = 0
        # for i in range(self.current_hand):
        #     player_value = np.dot(self.player_hand[i], VALUES)
        #     if player_value > 21:
        #         winnings += 0 # already lost in hit
        #     elif self.dealer_hand > 21:
        #         winnings += self.bet_size[i]
        #     elif player_value > self.dealer_hand:
        #         winnings += self.bet_size[i]
        #     elif player_value + 10 * (self.player_hand[i][0] > 0) > self.dealer_hand:
        #         winnings += self.bet_size[i]
        #     elif player_value == self.dealer_hand:
        #         winnings += 0
        #     elif player_value + 10 * (self.player_hand[i][0] > 0) == self.dealer_hand:
        #         winnings += 0
        #     else:
        #         winnings -= self.bet_size[i]

        return np.dot(results, self.bet_size[: self.current_hand]) + insurance_winnings

    def stand(self):
        self.current_hand += 1
        if self.hero_hand[self.current_hand] == 0:
            self.terminal = True
            return self.calculate_winnings()
        else:
            return 0

    def hit(self):
        self.hero_hand[self.current_hand] += self.deal_card()
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
        self.setup_hand(self.current_hand, [self.hero_hand[self.current_hand] // 2, self.deal_card()], self.bet_size[self.current_hand])
        self.setup_hand(self.current_hand + 1, [self.hero_hand[self.current_hand] // 2, self.deal_card()], self.bet_size[self.current_hand])
        return 0

    def insurance(self, bet_size=0.5):
        self.insurance_bet = self.bet_size[self.current_hand] * bet_size
        return 0

    def perform_action(self, action):
        action = action.get()
        reward = self.actions[action]()
        return self.state(), reward

    def is_terminal(self):
        return self.terminal

    def get_actions(self):
        actions = [Actions.HIT, Actions.STAND]
        if not self.hero_has_hit[self.current_hand] and 9 <= self.hero_hand[self.current_hand] <= 11:
            actions.append(Actions.DOUBLE_DOWN)
        if not self.hero_has_hit[self.current_hand] and self.hero_can_split[self.current_hand]:
            actions.append(Actions.SPLIT)
        if self.dealer_hand == 1 and self.insurance == 0:
            actions.extend(
                [
                    Actions.INSURANCE_1,
                    Actions.INSURANCE_2,
                    Actions.INSURANCE_3,
                    Actions.INSURANCE_4,
                    Actions.INSURANCE_5,
                ]
            )
        return list(map(BlackjackAction, actions))
