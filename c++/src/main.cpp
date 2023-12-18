#include <iostream>

/*************************game*********************************/
const int DECKS = 1;



    ////////////////////////////////////////////////////////////
    ////// Agent Stuuf

    class Agent {
 public:
    Agent(float alpha = 0.1, float gamma = 0.9, float epsilon = 0.1, float exploration = 0.5) : alpha(alpha), gamma(gamma), epsilon(epsilon), exploration(exploration) {
        // Initialize Q(s,a) arbitrarily
        for (int i = 0; i < 32; i++) {
            for (int j = 0; j < 11; j++) {
                for (int k = 0; k < 2; k++) {
                    Q[i][j][k] = 0;
                }
            }
        }
    }
};

int main() {
  std::cout << "Hello, World!" << std::endl;
  return 0;
}