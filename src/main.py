import argparse
import os
import pickle
import sys

from game import Blackjack
from rl import Agent, teach_agent


def get_path(filename: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "output", filename
    )


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--new", action="store_true", default=False)
    parser.add_argument("--agent_file", default="agent_data")
    parser.add_argument("--num_episodes", type=int, default=10000)
    parser.add_argument("--num_checkpoints", type=int, default=1)
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    new_agent = args.new
    agent_file = args.agent_file + ".pkl"
    num_episodes = args.num_episodes
    num_checkpoints = args.num_checkpoints

    path = get_path(agent_file)
    if not new_agent and os.path.exists(path):
        agent = pickle.load(open(path, "rb"))
    else:
        agent = Agent(gamma=1)

    world = Blackjack()
    per_checkpoint = num_episodes // num_checkpoints
    for i in range(num_checkpoints):
        if i == num_checkpoints - 1:
            per_checkpoint = num_episodes - (num_checkpoints - 1) * per_checkpoint

        agent, avg_reward = teach_agent(world, agent, num_episodes=per_checkpoint)
        print(f"Average reward: {avg_reward}")
        pickle.dump(agent, open(path, "wb"))


if __name__ == "__main__":
    main()
