import numpy as np
DECKS = 6
VALUES = np.array([1,2,3,4,5,6,7,8,9,10])

class Blackjack():
    def __init__(self):
        self.deck = np.array([1,2,3,4,5,6,7,8,9,10,10,10,10]*4*DECKS)

    def state(self):
        return self.player_hand, self.delear_hand, self.current_hand, self.bet_size
        
    def deal_card(self):
        card = self.deck[self.card_idx]
        self.card_idx += 1
        return card

    def start_game(self, bet_size=1):
        # reset deck
        self.deck = np.random.shuffle(self.deck)
        self.card_idx = 0
        
        # set up initial state
        self.current_hand = 0

        self.player_hand = np.zeros((4*DECKS,10))
        self.player_hand[self.current_hand][self.deal_card()-1] += 1
        self.player_hand[self.current_hand][self.deal_card()-1] += 1
        
        self.delear_hand = self.deal_card()
        
        
        self.bet_size = np.zeros(4*DECKS)
        self.bet_size[0] = bet_size

        self.is_terminal = False

        return self.state()
    
    def hit(self):
        self.player_hand[self.current_hand][self.deal_card()-1] += 1
        if np.dot(self.player_hand[self.current_hand], VALUES) > 21:
            return self.state(), -self.bet_size[self.current_hand]
        else:
            return self.state(), 0
        
    def dealer_play(self):
        while self.dealer_hand < 17:
            self.dealer_hand += self.deal_card()
        
    def calculate_winnings(self):
        self.dealer_play()

        played_hands = self.player_hand[:self.current_hand] 
        np.dot(played_hands, VALUES)

        # winnings = 0
        # for i in range(self.current_hand):             
        #     if np.dot(self.player_hand[i], VALUES) > 21:
        #         winnings += 0 # already lost
        #     elif self.delear_hand > 21:
        #         winnings += self.bet_size[i]
        #     elif np.dot(self.player_hand[i], VALUES) > self.delear_hand:
        #         winnings += self.bet_size[i]
        #     elif np.dot(self.player_hand[i], VALUES) == self.delear_hand:
        #         winnings += 0
        #     else:
        #         winnings -= self.bet_size[i]
    
    def stand(self):
        self.current_hand += 1
        if not self.player_hand[self.current_hand].any():
            self.is_terminal = True
            return self.state(), self.calculate_winnings()
        else:
            return self.state(), 0
        
    def double_down(self):
        self.bet_size[self.current_hand] *= 2
        return self.hit()
    
    def split(self):
        ...



        


        