from abc import ABC
from collections import defaultdict
import errno
import os


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


class Agent:
    def __init__(self, alpha: float = 0.1, gamma: float = 0.9):
        self.alpha = alpha
        self.gamma = gamma
        self.Q: dict[tuple[State, Action], float] = dict()
        self.visits: dict[tuple[State, Action], int] = dict()

    def choose_action(self, world: Game, state: State) -> Action:
        actions = world.get_actions()
        get_Q = lambda a: self.Q.get((state, a), 0)
        get_V = lambda a: 1 / (1 + self.visits.get((state, a), 0))
        return max(actions, key=lambda a: get_Q(a) + get_V(a))

    def update(
        self,
        world: Game,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
    ) -> None:
        actions = world.get_actions()
        best_action_value = max(self.Q.get((next_state, a), 0) for a in actions)
        prev_Q = self.Q.get((state, action), 0)
        self.Q[(state, action)] = prev_Q + self.alpha * (
            reward + self.gamma * best_action_value - prev_Q
        )
        self.visits[(state, action)] = self.visits.get((state, action), 0) + 1


def run_episode(world: Game, agent: Agent, max_steps: int = 100) -> float:
    state = world.state()
    total_reward = 0.0
    for _ in range(max_steps):
        action = agent.choose_action(world, state)
        next_state, reward = world.perform_action(action)
        agent.update(world, state, action, reward, next_state)
        state = next_state
        total_reward += reward
        if world.is_terminal():
            break
    return total_reward


def teach_agent(
    world: Game, agent: Agent = None, num_episodes: int = 100, max_steps: int = 100
) -> Agent:
    if agent is None:
        agent = Agent()
    world.start_game()
    avg_reward_sum = 0.0
    for _ in range(num_episodes):
        avg_reward_sum += run_episode(world, agent, max_steps)
    return agent, avg_reward_sum / num_episodes
