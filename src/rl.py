from abc import ABC


class State(ABC):
    ...

class Action(ABC):
    ...

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