from game import Blackjack
from rl import Agent, teach_agent


def main():
    agent = Agent(gamma=1)  # Agent(filename="agent_data.json")
    world = Blackjack()
    teach_agent(world, agent, num_episodes=10, max_steps=10)


if __name__ == "__main__":
    main()
