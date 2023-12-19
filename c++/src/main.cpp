#include <algorithm>
#include <cassert>
#include <concepts>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <unordered_map>
#include <vector>
using namespace std;

// using State = int[21][21][21][2][2][2][2][2][2][2][2][2][2][2][2][10][3][3];
// float Q[3413975041];

// Q: sate actions
// vistittation: state actions
// Action enums
enum Action {
  HIT,
  STAND,
  DOUBLE_DOWN,
  SPLIT,
  INSURANCE_HALF,
  INSURANCE_FULL,
  NUM_ACTIONS, // not an action
};

const char* actionNames[] = {"HIT", "STAND", "DOUBLE_DOWN", "SPLIT", "INSURANCE_HALF", "INSURANCE_FULL"};

float Q[3413975041][NUM_ACTIONS];
char visits[3413975041][NUM_ACTIONS];

/*************************game*********************************/
class Blackjack {
 private:
  static constexpr int DECKS = 1;
  static constexpr int MAX_HANDS = 3;
  // (21*2*2*2*2)^3*10*3*3

  vector<ushort> deck;
  vector<ushort> heroHand;    // 21 ^ MAX_HANDS
  vector<bool> heroHasAce;    // 2 ^ MAX_HANDS
  vector<bool> heroCanSplit;  // 2 ^ MAX_HANDS
  vector<bool> heroHasHit;    // 2 ^ MAX_HANDS
  vector<short> betSize;      // 2 ^ MAX_HANDS
  ushort dealerHand;          // 10
  ushort currentHand;         // MAX_HANDS
  ushort numHands;
  ushort cardIdx;
  double insuranceBet;  // 3
  bool terminal;

  default_random_engine rng;

 public:
  Blackjack() : rng(random_device{}()), heroHand(MAX_HANDS), heroHasAce(MAX_HANDS), heroCanSplit(MAX_HANDS), heroHasHit(MAX_HANDS), betSize(MAX_HANDS) {
    vector<int> oneDeck = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10};
    for (int i = 0; i < DECKS; i++) {
      for (int j = 0; j < 4; j++) {
        deck.insert(deck.end(), oneDeck.begin(), oneDeck.end());
      }
    }
  }

  uint state() {
    uint depth = 1;
    uint res = insuranceBet * depth;
    depth *= 3;
    res += currentHand * depth;
    depth *= MAX_HANDS;
    res += dealerHand * depth;
    depth *= 10;
    for (int i = 0; i < MAX_HANDS; i++) {
      res += betSize[i] * depth;
      depth *= 2;
      res += heroHasHit[i] * depth;
      depth *= 2;
      res += heroCanSplit[i] * depth;
      depth *= 2;
      res += heroHasAce[i] * depth;
      depth *= 2;
      res += heroHand[i] * depth;
      depth *= 21;
    }
    return res + 1;
  }

  int dealCard() {
    return deck[cardIdx++];
  }

  void setupHand(int idx, vector<int> cards, int initialBet) {
    heroHand[idx] = cards[0] + cards[1];
    heroHasAce[idx] = cards[0] == 1 || cards[1] == 1;
    heroCanSplit[idx] = cards[0] == cards[1];
    heroHasHit[idx] = false;
    betSize[idx] = initialBet;
  }

  void startGame(int initialBet = 1) {
    // reset deck
    shuffle(deck.begin(), deck.end(), rng);
    cardIdx = 0;

    // set up initial state
    currentHand = 0;
    numHands = 1;

    fill(heroHand.begin(), heroHand.end(), 0);
    fill(heroHasAce.begin(), heroHasAce.end(), false);
    fill(heroCanSplit.begin(), heroCanSplit.end(), false);
    fill(heroHasHit.begin(), heroHasHit.end(), false);
    fill(betSize.begin(), betSize.end(), 0);

    setupHand(0, {dealCard(), dealCard()}, initialBet);

    dealerHand = dealCard();

    insuranceBet = 0;

    terminal = false;

    // TODO: return state
  }

  bool dealerPlay() {
    int newCard = dealCard();
    bool hasAce = dealerHand == 1 || newCard == 1;
    dealerHand += newCard;
    if (dealerHand == 11 && hasAce) {
      dealerHand += 10;
      return true;  // blackjack
    }

    while (dealerHand < 21) {
      if (17 <= dealerHand && dealerHand <= 21) break;
      if (17 <= dealerHand + 10 * hasAce && dealerHand * 10 <= 21) {
        dealerHand += 10 * hasAce;
        break;
      }
      newCard = dealCard();
      hasAce = hasAce || newCard == 1;
      dealerHand += newCard;
    }
    return false;
  }

  double calculateWinnings() {
    double insuranceWinnings = dealerPlay() ? insuranceBet : -insuranceBet;

    double winnings = 0;

    for (int i = 0; i < numHands; i++) {
      int handValue = heroHand[i] + 10 * heroHasAce[i] <= 21 ? heroHand[i] + 10 * heroHasAce[i] : heroHand[i];
      int result = -1;
      if (heroHand[i] > 21)
        continue;  // already lost in hit
      else if (dealerHand > 21)
        result = 1;
      else if (handValue > dealerHand)
        result = 1;
      else if (handValue == dealerHand)
        result = 0;

      winnings += result * betSize[i];
      if (result == 1 && heroHand[i] == 11 && heroHasAce[i] && !heroHasHit[i]) winnings += 0.5 * betSize[i];  // blackjack bonus
    }

    return winnings + insuranceWinnings;
  }

  double stand() {
    if (++currentHand == numHands) {
      terminal = true;
      return calculateWinnings();
    }
    return 0;
  }

  double hit() {
    int card = dealCard();
    heroHasAce[currentHand] = heroHasAce[currentHand] || card == 1;
    heroHand[currentHand] += card;
    heroHasHit[currentHand] = true;
    if (heroHand[currentHand] > 21) {
      heroHand[currentHand] = 22;  // bust
      return -betSize[currentHand] + stand();
    }
    return 0;
  }

  double doubleDown() {
    betSize[currentHand] *= 2;
    double reward = hit();
    return terminal ? reward : reward + stand();
  }

  double split() {
    int card = heroHand[currentHand] / 2;
    setupHand(currentHand, {card, dealCard()}, betSize[currentHand]);
    setupHand(numHands++, {card, dealCard()}, betSize[currentHand]);
    return 0;
  }

  double insurance(double multiplier = 0.5) {
    insuranceBet = multiplier * betSize[currentHand];
    return 0;
  }

  bool isTerminal() const {
    return terminal;
  }

  vector<Action> getActions() const {
    if (isTerminal()) return {};
    vector<Action> actions = {HIT, STAND};
    if (!heroHasHit[currentHand] && 9 <= heroHand[currentHand] && heroHand[currentHand] <= 11) actions.push_back(DOUBLE_DOWN);
    if (!heroHasHit[currentHand] && heroCanSplit[currentHand] && numHands < MAX_HANDS) actions.push_back(SPLIT);
    if (dealerHand == 1 && insuranceBet == 0) actions.insert(actions.end(), {INSURANCE_HALF, INSURANCE_FULL});
    return actions;
  }

  double performAction(Action action) {
    switch (action) {
      case HIT:
        return hit();
      case STAND:
        return stand();
      case DOUBLE_DOWN:
        return doubleDown();
      case SPLIT:
        return split();
      case INSURANCE_HALF:
        return insurance(0.25);
      case INSURANCE_FULL:
        return insurance(0.5);
      default:
        throw runtime_error("Invalid action");
    }
  }

  void printState() const {
    cout << "Dealer: " << dealerHand << endl;
    // For each hand, print the value, hasAce, canSplit, hasHit, betSize, and indicate if it's the current hand
    // first print header with setw
    cout << "Hand\tValue\tHasAce\tCanSplit\tHasHit\tBet" << endl;
    for (int i = 0; i < numHands; i++) {
      cout << i << "\t" << heroHand[i] << "\t" << heroHasAce[i] << "\t" << heroCanSplit[i] << "\t" << heroHasHit[i] << "\t" << betSize[i] << "\t" << (i == currentHand ? "*" : "") << endl;
    }
    cout << "Insurance: " << insuranceBet << endl;
  }
};

////////////////////////////////////////////////////////////
////// Agent Stuff

class Agent {
  float alpha;
  float gamma;
  float epsilon;
  float exploration;

  // unordered_map<std::pair<State, Action>, float, pairhash> Q;
  // unordered_map<std::pair<State, Action>, float, pairhash> visits;

 public:
  Agent(float alpha = 0.1, float gamma = 0.9, float epsilon = 0.1, float exploration = 0.5) : alpha(alpha),
                                                                                              gamma(gamma),
                                                                                              epsilon(epsilon),
                                                                                              exploration(exploration) {}

  // Agent(string filename) {
  //   ifstream is(filename);
  //   if (!is) {
  //     throw runtime_error("Could not open file " + filename);
  //   }

  //   string line;
  //   while (getline(is, line)) {
  //     stringstream ss(line);
  //     string stateStr, actionStr;
  //     float value;
  //     ss >> stateStr >> actionStr >> value;
  //     State state = State().deserialize(stateStr);
  //     Action action = Action().deserialize(actionStr);
  //     Q[make_pair(state, action)] = value;
  //   }
  //   while (getline(is, line)) {
  //     stringstream ss(line);
  //     string stateStr, actionStr;
  //     float value;
  //     ss >> stateStr >> actionStr >> value;
  //     State state = State().deserialize(stateStr);
  //     Action action = Action().deserialize(actionStr);
  //     visits[make_pair(state, action)] = value;
  //   }
  //   getline(is, line);
  //   stringstream ss(line);
  //   ss >> alpha >> gamma >> epsilon >> exploration;
  //   int QSize;
  //   ss >> QSize;
  //   for (int i = 0; i < QSize; i++) {
  //     getline(is, line);
  //     stringstream ss(line);
  //     string stateStr, actionStr;
  //     float value;
  //     ss >> stateStr >> actionStr >> value;
  //     State state = State().deserialize(stateStr);
  //     Action action = Action().deserialize(actionStr);
  //     Q[make_pair(state, action)] = value;
  //   }
  //   int visitsSize;
  //   ss >> visitsSize;
  //   for (int i = 0; i < visitsSize; i++) {
  //     getline(is, line);
  //     stringstream ss(line);
  //     string stateStr, actionStr;
  //     float value;
  //     ss >> stateStr >> actionStr >> value;
  //     State state = State().deserialize(stateStr);
  //     Action action = Action().deserialize(actionStr);
  //     visits[make_pair(state, action)] = value;
  //   }
  // }

  Action chooseAction(const Blackjack& game, uint state) const {
    vector<Action> actions = game.getActions();
    vector<Action> bestActions;
    float bestValue = -1;
    for (Action action : actions) {
      float value = Q[state][action];
      if (value > bestValue) {
        bestValue = value;
        bestActions.clear();
        bestActions.push_back(action);
      } else if (value == bestValue) {
        bestActions.push_back(action);
      }
    }
    return bestActions[rand() % bestActions.size()];
  }

  void update(const Blackjack& game, uint state, Action action, uint nextState, float reward) {
    // pair<State, Action> key = make_pair(state, action);

    vector<Action> nextActions = game.getActions();
    assert(!nextActions.empty());

    // Find the best Q across all possible next actions
    float bestValue = 0;
    for (Action nextAction : nextActions) {
      bestValue = max(bestValue, Q[nextState][nextAction]);
    }

    Q[state][action] += alpha * (reward + gamma * bestValue - Q[state][action]);
    visits[state][action] += 1;
  }

  float run(Blackjack& game) {
    game.startGame();  // TODO: rename to reset
    float totalReward = 0;
    while (!game.isTerminal()) {
      uint state = game.state();
      cout << "State:" << endl;
      game.printState();

      Action action = chooseAction(game, state);
      cout << "Action: " << actionNames[action] << std::endl;

      float reward = game.performAction(action);
      cout << "New State:" << endl;
      game.printState();
      cout << "Reward: " << reward << std::endl;

      update(game, state, action, game.state(), reward);
      totalReward += reward;

      cout << string(80, '-') << std::endl;
    }
    return totalReward;
  }

  void train(Blackjack& game, int episodes) {
    float totalReward = 0;
    for (int i = 0; i < episodes; i++) {
      cout << "Episode " << i << std::endl;
      float reward = run(game);
      cout << "Total Reward: " << reward << std::endl;
      cout << string(80, '=') << std::endl;
      totalReward += reward;
    }
    std::cout << "Average reward: " << totalReward / episodes << std::endl;
  }

  // void dump(ostream& os) const {
  //   for (const auto& [key, value] : Q) {
  //     auto& [state, action] = key;
  //     os << state.serialize() << " " << action.serialize() << " ";
  //     os << value << endl;
  //   }
  //   os << endl;
  //   for (const auto& [key, value] : visits) {
  //     auto& [state, action] = key;
  //     os << state.serialize() << " " << action.serialize() << " ";
  //     os << value << endl;
  //   }
  //   os << endl;
  //   os << alpha << " " << gamma << " " << epsilon << " " << exploration << endl;
  //   os << Q.size() << endl;
  //   os << visits.size() << endl;
  // }
};

int main() {
  Blackjack game;
  Agent agent;
  fill(&Q[0][0], &Q[0][0] + sizeof(Q) / sizeof(Q[0][0]), 0);
  fill(&visits[0][0], &visits[0][0] + sizeof(visits) / sizeof(visits[0][0]), 0);
  agent.train(game, 1000);
  return 0;
}