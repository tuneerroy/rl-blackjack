from abc import ABC
from collections import defaultdict


class Hashable(ABC):
    def __hash__(self) -> int:
        raise NotImplementedError


class State(Hashable):
    pass


class Action(Hashable):
    pass


class World(ABC):
    def get_current_state(self) -> State:
        raise NotImplementedError

    def get_actions(self, state: State) -> list[Action]:
        raise NotImplementedError

    def get_reward_and_state(self, state: State, action: Action) -> tuple[float, State]:
        raise NotImplementedError

    def is_terminal(self, state: State) -> bool:
        raise NotImplementedError


class Agent:
    def __init__(self, world: World, alpha: float = 0.1, gamma: float = 0.9):
        self.world = world
        self.alpha = alpha
        self.gamma = gamma
        self.Q: dict[tuple[State, Action], float] = defaultdict(lambda: 0)
        self.visits: dict[tuple[State, Action], int] = defaultdict(lambda: 0)

    def choose_action(self, state: State) -> Action:
        actions = self.world.get_actions(state)
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


def run_episode(world: World, agent: Agent, max_steps: int = 100) -> float:
    state = world.get_current_state()
    total_reward = 0.0
    for _ in range(max_steps):
        action = agent.choose_action(state)
        reward, next_state = world.get_reward_and_state(state, action)
        agent.update(state, action, reward, next_state)
        state = next_state
        total_reward += reward
        if world.is_terminal(state):
            break
    return total_reward


def teach_agent(
    world: World, agent: Agent = None, num_episodes: int = 100, max_steps: int = 100
) -> Agent:
    if agent is None:
        agent = Agent()
    for _ in range(num_episodes):
        run_episode(world, agent, max_steps)
    return agent
