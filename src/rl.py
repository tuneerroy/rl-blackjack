from abc import ABC

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


class Agent(ABC):
    def __init__(self, world: World) -> None:
        self.world = world

    def choose_action(self, state: State) -> Action:
        raise NotImplementedError
    
    def update(self, state: State, action: Action, reward: float, next_state: State) -> None:
        raise NotImplementedError


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

def teach_agent(world: World, agent: Agent, num_episodes: int = 100, max_steps: int = 100) -> None:
    for _ in range(num_episodes):
        run_episode(world, agent, max_steps)