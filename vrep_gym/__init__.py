__version__ = '0.1.0'


from gym.envs.registration import register

from vrep_gym.envs import QuadrotorPositionControl

register(
    id='QuadrotorPositionControlEnv-v0',
    entry_point='vrep_gym.envs:QuadrotorPositionControl',
    max_episode_steps=1000,
)
