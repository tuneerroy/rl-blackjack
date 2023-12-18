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

    def get_actions(self, state: State) -> list[Action]:
        raise NotImplementedError

    def perform_action(self, action: Action) -> tuple[State, float]:
        raise NotImplementedError

    def is_terminal(self) -> bool:
        raise NotImplementedError

    def start_game(self) -> None:
        raise NotImplementedError


class Agent:
    def __init__(self, alpha: float = 0.1, gamma: float = 0.9, filename: str = None):
        if filename is not None:
            self.__load_agent_data(filename)
        else:
            self.alpha = alpha
            self.gamma = gamma
            self.Q: dict[tuple[State, Action], float] = defaultdict(lambda: 0)
            self.visits: dict[tuple[State, Action], int] = defaultdict(lambda: 0)

    def choose_action(self, world: Game, state: State) -> Action:
        actions = world.get_actions(state)
        get_Q = lambda a: self.Q[(state, a)]
        get_V = lambda a: 1 / (1 + self.visits[(state, a)])
        return max(actions, key=lambda a: get_Q(a) + get_V(a))

    def update(
        self, state: State, action: Action, reward: float, next_state: State
    ) -> None:
        actions = self.world.get_actions(next_state)
        best_action_value = max(self.Q[(next_state, a)] for a in actions)
        self.Q[(state, action)] += self.alpha * (
            reward + self.gamma * best_action_value - self.Q[(state, action)]
        )
        self.visits[(state, action)] += 1

    def __load_agent_data(self, filename: str) -> None:
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        with open(filename) as f:
            for line in f:
                if line == "--\n":
                    break
                state, action, value = line.split(",")
                self.Q[(state, action)] = float(value)
            for line in f:
                if line == "--\n":
                    break
                state, action, value = line.split(",")
                self.visits[(state, action)] = int(value)
            self.alpha, self.gamma = map(float, f.readline().split(","))

    def dump_agent_data(self, filename: str, override: bool = False) -> None:
        if not override and os.path.isfile(filename):
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), filename)

        with open(filename, "w") as f:
            for (state, action), value in self.Q.items():
                f.write(f"{state},{action},{value}\n")
            f.write("--\n")
            for (state, action), value in self.visits.items():
                f.write(f"{state},{action},{value}\n")
            f.write("--\n")
            f.write(f"{self.alpha},{self.gamma}\n")


def run_episode(world: Game, agent: Agent, max_steps: int = 100) -> float:
    state = world.state()
    total_reward = 0.0
    for _ in range(max_steps):
        action = agent.choose_action(world, state)
        next_state, reward = world.perform_action(state, action)
        agent.update(state, action, reward, next_state)
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
    for _ in range(num_episodes):
        run_episode(world, agent, max_steps)
    return agent
