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

const char PRETTY_PRINT = 0;
const char CSV_PRINT = 1;
const char NO_PRINT = 2;
static char PRINT_MODE = NO_PRINT;
static long episodeNumber = 0;

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
  NUM_ACTIONS,  // not an action
};

const char* actionNames[] = {"HIT", "STAND", "DOUBLE_DOWN", "SPLIT", "INSURANCE_HALF", "INSURANCE_FULL"};

// float Q[3413975041][NUM_ACTIONS];
// char visits[3413975041][NUM_ACTIONS];
// 3413975041
// 81935441920
// float Q[1][NUM_ACTIONS];
// char visits[1][NUM_ACTIONS];

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
    if (terminal) return 0;
    uint depth = 1;
    uint res = (insuranceBet * 4) * depth;
    depth *= 3;
    res += currentHand * depth;
    depth *= MAX_HANDS;
    res += (dealerHand - 1) * depth;
    depth *= 10;
    for (int i = 0; i < MAX_HANDS; i++) {
      res += (betSize[i] - 1) * depth;
      depth *= 2;
      res += heroHasHit[i] * depth;
      depth *= 2;
      res += heroCanSplit[i] * depth;
      depth *= 2;
      res += heroHasAce[i] * depth;
      depth *= 2;
      res += (heroHand[i] - 2) * depth;
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
    if (PRINT_MODE == PRETTY_PRINT) {
      cout << "Dealer: " << dealerHand << endl;
      cout << "" << setw(10) << left << "Hand" << setw(10) << left << "Has Ace" << setw(10) << left << "Can Split" << setw(10) << left << "Has Hit" << setw(10) << left << "Bet Size" << setw(10) << left << "Current" << endl;
      for (int i = 0; i < numHands; i++) {
        cout <<  "" << setw(10) << left << heroHand[i] << setw(10) << left << (heroHasAce[i] ? "v " : " ") << setw(10) << left << (heroCanSplit[i] ? "v " : " ") << setw(10) << left << (heroHasHit[i] ? "v " : " ") << setw(10) << left << betSize[i] << setw(10) << left << (i == currentHand ? "*" : " ") << endl;
      }
      cout << "Insurance: " << insuranceBet << endl << endl;
    } else if (PRINT_MODE == CSV_PRINT) {
      cout << episodeNumber << "," << dealerHand << "," << currentHand << "," << numHands << "," << heroHand[currentHand] << "," << heroHasAce[currentHand] << "," << heroCanSplit[currentHand] << "," << heroHasHit[currentHand] << "," << betSize[currentHand] << "," << insuranceBet;
    }
  }
};

////////////////////////////////////////////////////////////
////// Agent Stuff

class Agent {
  float alpha;
  float gamma;
  float epsilon;
  float exploration;

  // float Q[1][NUM_ACTIONS];
  // char visits[1][NUM_ACTIONS];

  unordered_map<uint, unordered_map<Action, float>> Q;
  unordered_map<uint, unordered_map<Action, char>> visits;

  // unordered_map<std::pair<State, Action>, float, pairhash> Q;
  // unordered_map<std::pair<State, Action>, float, pairhash> visits;

 public:
  Agent(float alpha = 0.1, float gamma = 0.9, float epsilon = 0.1, float exploration = 0.5) : alpha(alpha),
                                                                                              gamma(gamma),
                                                                                              epsilon(epsilon),
                                                                                              exploration(exploration) {}

  Action chooseAction(const Blackjack& game, uint state) {
    vector<Action> actions = game.getActions();
    vector<Action> bestActions;
    float bestValue = numeric_limits<float>::lowest();
    for (Action action : actions) {
      float value = Q[state][action] + exploration / (1 + visits[state][action]);
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

    // Find the best Q across all possible next actions
    float bestValue = numeric_limits<float>::lowest();
    for (Action nextAction : nextActions) {
      bestValue = max(bestValue, Q[nextState][nextAction]);
    }
    if (nextActions.empty()) bestValue = 0;

    Q[state][action] += alpha * (reward + gamma * bestValue - Q[state][action]);
    visits[state][action]++;
  }

  float run(Blackjack& game) {
    game.startGame();  // TODO: rename to reset
    float totalReward = 0;
    while (!game.isTerminal()) {
      if (PRINT_MODE != NO_PRINT) game.printState();
      uint state = game.state();

      Action action = chooseAction(game, state);

      float reward = game.performAction(action);
      update(game, state, action, game.state(), reward);
      totalReward += reward;

      // if (PRINT_MODE == PRETTY_PRINT) {
      //   cout << "Action: " << actionNames[action] << " -> " << reward << " reward" << endl;
      // } else 
      if (PRINT_MODE == CSV_PRINT) {
        cout << "," << actionNames[action] << "," << reward << ",";
        if (game.isTerminal()) cout << totalReward;
        cout << endl;
      }
    }
    // if (PRINT_MODE == PRETTY_PRINT) game.printState();
    return totalReward;
  }

  void printCsvHeader() {
    cout << "Episode,Dealer,Current Hand,Num Hands,Hand,Has Ace,Can Split,Has Hit,Bet Size,Insurance,Action,Reward,Episode Net Reward" << endl;
  }

  void train(Blackjack& game, long episodes, int checkpoints = 10) {
    float totalReward = 0;
    long checkpointLength = episodes / checkpoints;

    if (PRINT_MODE == CSV_PRINT) printCsvHeader();

    for (int c = 0; c < checkpoints; c++) {
      for (long i = 0; i < checkpointLength; i++) {
        if (PRINT_MODE == NO_PRINT && i == checkpointLength - checkpointLength / 10) {
          freopen(("output_" + to_string(c) + ".csv").c_str(), "w", stdout);
          PRINT_MODE = CSV_PRINT;
          printCsvHeader();
        }
        episodeNumber = i + c * checkpointLength;
        // if (PRINT_MODE == PRETTY_PRINT) cout << "Episode " << episodeNumber << endl;
        float reward = run(game);
        // if (PRINT_MODE == PRETTY_PRINT) cout << "Total Reward: " << reward << std::endl;
        // if (PRINT_MODE == PRETTY_PRINT) cout << std::endl << string(60, '*') << std::endl << std::endl;
        totalReward += reward;
      }
      fclose(stdout);
      PRINT_MODE = NO_PRINT;
      cerr << "Average reward after " << (c + 1) * checkpointLength << " episodes: " << totalReward / ((c + 1) * checkpointLength) << " (" << (100.0 * (c + 1) / checkpoints) << "% complete)" << endl;
    }

    // if (PRINT_MODE == PRETTY_PRINT) cout << "Average reward: " << totalReward / episodes << std::endl;
  }
};

int main(int argc, char** argv) {
  Blackjack game;
  Agent agent;
  // fill(&Q[0][0], &Q[0][0] + sizeof(Q) / sizeof(Q[0][0]), 0);
  // fill(&visits[0][0], &visits[0][0] + sizeof(visits) / sizeof(visits[0][0]), 0);
  long trainingIterations = 1e9;
  if (argc > 1) {
    stringstream ss(argv[1]);
    ss >> trainingIterations;
  }
  agent.train(game, trainingIterations);
  return 0;
}