import gym
import logging

"""
    this module is a hack a needs a fundamental rework and redesign (chh/19Q2)
"""

def register(gym_env_name : str = None, gym_factory = None, log_steps : bool = False, log_reset : bool = False):
    """ Registers the LogEnv wrapper for the 'gym_env_name' environment.
        The wrapper is registered as 'Log-<env_name>'.

        Args:
        gym_env_name    the name of the gym environment to be wrapped by LogEnv (instead of gym_factor)
        gym_factory     a factory method to create a gym environment (instead of gym_env_name)
        log_steps       if set to False calls to the step method are not logged
        log_reset       if set to false calls to the reset method are not logged, except if
                        the current episode is not complete yet.

        Retuns:
        The new name of the wrapped environment.
    """
    assert gym_env_name is not None, "None is not an admissible environment name"
    assert type(gym_env_name) is str , "gym_env_name is not a str"
    assert len(gym_env_name) > 0, "empty string is not an admissible environment name"

    result = "Log" + gym_env_name
    LogEnv._log_steps = log_steps
    LogEnv._log_reset = log_reset
    if LogEnv._gym_env_name != gym_env_name:
        assert LogEnv._gym_env_name is None, "Another environment was already registered"

        LogEnv._gym_env_name = gym_env_name
        gym.envs.registration.register(id=result, entry_point=LogEnv)
    return result


class LogEnv(gym.Env):
    """Decorator for gym environments to log each method call on the logger
    """
    _gym_env_name = None
    _log_steps = False
    _log_reset = False
    _instanceCount = 0
    
    def __init__(self):
        target_env = gym.make( LogEnv._gym_env_name )
        self.env = target_env.unwrapped
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
        self.reward_range = self.env.reward_range
        self.metadata = self.env.metadata

        self._logStarted=False
        self._stepCount=0
        self._totalStepCount=0
        self._resetCount=0
        self._renderCount=0
        self._seedCount=0
        self._closeCount=0
        self._totalReward=0.0
        self._done=False
        self._instanceId=LogEnv._instanceCount
        LogEnv._instanceCount += 1

        self._log = logging.getLogger(__name__)
        self._log.setLevel(logging.DEBUG)
        return


    def _logCall(self, msg):
        if not self._logStarted:
            self._log.debug(f'#EnvId ResetCount.Steps [R=sumRewards]')
            self._logStarted=True
        logMsg = f'#{self._instanceId} {self._resetCount:3}.{self._stepCount:<3} [totalReward={self._totalReward:6.1f}] {msg}'
        self._log.debug(logMsg)
        return

    def step(self, action):        
        self._stepCount += 1
        self._totalStepCount += 1
        result = self.env.step(action)
        (state, reward, done, info ) = result
        self._totalReward += reward
        if self._log_steps:
            self._logCall(f'executing step( {action} ) = ( reward={reward}, state={state}, done={done}, info={info} )' )
        if done:
            self._logCall( f'game over' )
            self._done=True
        return result

    def reset(self, **kwargs):
        if self._log_reset or not self._done:
            msg = "executing reset(...)" 
            if not self._done and self._stepCount > 0:
                msg += " [episode not done]"
            self._logCall(msg)
        self._resetCount += 1
        self._stepCount=0
        self._totalReward=0.0
        self._done=False
        return self.env.reset(**kwargs)

    def render(self, mode='human', **kwargs):
        self._logCall("executing render(...)" )
        self._renderCount += 1
        return self.env.render(mode, **kwargs)

    def close(self):
        if self.env:
            self._logCall("executing close()" )
            self._closeCount += 1
            return self.env.close()

    def seed(self, seed=None):
        self._logCall( "executing seed(...)" )
        self._seedCount += 1
        return self.env.seed(seed)

    @property
    def unwrapped(self):
        return self.env.unwrapped

    @property
    def spec(self):
        return self.env.spec

