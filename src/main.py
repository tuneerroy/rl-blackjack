import os
import pickle

from game import Blackjack
from rl import Agent, teach_agent


def get_path(filename: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "output", filename
    )


def main():
    path = get_path("agent_data.pkl")
    if os.path.exists(path):
        agent = pickle.load(open(path, "rb"))
    else:
        agent = Agent(gamma=1)

    world = Blackjack()
    agent, avg_reward = teach_agent(world, agent, num_episodes=10, max_steps=10)
    print(f"Average reward: {avg_reward}")

    pickle.dump(agent, open(path, "wb"))


if __name__ == "__main__":
    main()
