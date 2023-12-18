from abc import ABC
from collections import defaultdict

import numpy as np


class Hashable(ABC):
    def __hash__(self) -> int:
        raise NotImplementedError


class State(Hashable):
    pass


class Action(Hashable):
    pass


class Game(ABC):
    def state(self) -> State:
        raise NotImplementedError

    def get_actions(self) -> list[Action]:
        raise NotImplementedError

    def perform_action(self, action: Action) -> tuple[State, float]:
        raise NotImplementedError

    def is_terminal(self) -> bool:
        raise NotImplementedError

    def start_game(self) -> None:
        raise NotImplementedError


def default_zero() -> float:
    return 0.0


class Agent:
    def __init__(self, alpha: float = 0.1, gamma: float = 0.9, exploration: float = 0.5):
        self.alpha = alpha
        self.gamma = gamma
        self.exploration = exploration
        self.Q: defaultdict[tuple[State, Action], float] = defaultdict(default_zero)
        self.visits: defaultdict[tuple[State, Action], int] = defaultdict(default_zero)

    def choose_action(self, world: Game, state: State) -> Action:
        actions = world.get_actions()
        get_Q = lambda a: self.Q[(state, a)]
        get_V = lambda a: self.exploration / (1 + self.visits[(state, a)])
        max_value = max(get_Q(a) + get_V(a) for a in actions)
        best_actions = [a for a in actions if get_Q(a) + get_V(a) == max_value]
        return np.random.choice(best_actions)

    def update(
        self,
        world: Game,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
    ) -> None:
        actions = world.get_actions()
        best_action_value = max(self.Q[(next_state, a)] for a in actions)
        self.Q[(state, action)] += self.alpha * (
            reward + self.gamma * best_action_value - self.Q[(state, action)]
        )
        self.visits[(state, action)] = self.visits[(state, action)] + 1


def run_episode(world: Game, agent: Agent) -> float:
    state = world.state()
    total_reward = 0.0
    while not world.is_terminal():
        action = agent.choose_action(world, state)
        print(f"state: {state}")
        print(f"action: {action}")
        next_state, reward = world.perform_action(action)
        print(f"nxt state: {next_state}")
        print(f"reward: {reward}")
        print(f"-" * 30 + "\n")
        agent.update(world, state, action, reward, next_state)
        state = next_state
        total_reward += reward
    return total_reward


def teach_agent(world: Game, agent: Agent = None, num_episodes: int = 100) -> Agent:
    if agent is None:
        agent = Agent()
    avg_reward_sum = 0.0
    for i in range(num_episodes):
        print(f"Episode {i + 1}")
        print("*" * 30 + "\n")
        world.start_game()
        avg_reward_sum += run_episode(world, agent)
    return agent, avg_reward_sum / num_episodes
