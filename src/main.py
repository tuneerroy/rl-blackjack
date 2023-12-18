import os
import pickle
from game import Blackjack
from rl import Agent, teach_agent


def main():
    if os.path.exists("agent_data.pkl"):
        agent = pickle.load(open("agent_data.pkl", "rb"))
    else:
        agent = Agent(gamma=1)

    world = Blackjack()
    agent, avg_reward = teach_agent(world, agent, num_episodes=10, max_steps=10)
    print(f"Average reward: {avg_reward}")

    pickle.dump(agent, open("agent_data.pkl", "wb"))


if __name__ == "__main__":
    main()
