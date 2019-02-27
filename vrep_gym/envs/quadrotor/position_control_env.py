from gym import error, spaces, utils
import numpy as np

from vrep_gym.envs.vrep_env import VREPEnv, get_scene
from vrep_gym.vrep.vrep_object import VREPObject

OBSERVATION_SPACE = (16,)
ACTION_SPACE = (4,)

DIST_THRESHOLD = 0.5
TIME_THRESHOLD = 1000

UPPER_BOUNDS = np.array([-2.5, -2.5, 0.5])
LOWER_BOUNDS = np.array([2.5, 2.5, 2.5])

import logging
log = logging.getLogger(__name__)

class DroneStates:
    FOLLOW_REF = 0
    PROP_CONTROL = 1
    LAND = 2


class QuadrotorPositionControl(VREPEnv):
    """Quadrotor Position Control Environment

    In this environment, we have a quadrotor whose position we want to control.
    This would traditionally be accomplished by using multiple PID controllers over
    the position and orientation of the quadrotor, with fine-tuned gains.

    The challenge here will be to control the quadrotor using the following observations
    and actions.

    Observation space
    -----------------

    0, 1, 2: Position of Quadrotor
    3, 4, 5: Euler angles of Quadrotor
    6, 7, 8: Linear Velocity of Quadrotor
    9, 10, 11: Angular velocity of Quadrotor
    12, 13, 14: Goal Position of Quadrotor
    15: collision flag

    Action space
    ------------

    0, 1, 2, 3: Angular Velocity command for each propeller

    Initialization
    --------------

    The drone and goal are instantiated at a random spot in the following box

    x in [-2.5, 2.5] m
    y in [-2.5, 2.5] m
    z in [ 0.5, 2.5] m

    Termination
    -----------

    Time Steps >= 1000 (1000 * 10ms = 10s)

    Reward function
    ---------------

    We want the drone to reach the position and hover so, we use the (modified)
    reward function from https://arxiv.org/pdf/1707.05110.pdf

    cost_t
        = 4e-3 * ||error(p_t)||
        + 5e-4 * ||vel_t||
        + 2e-4 * ||angle_t||
        + 3e-4 * ||avel_t||
    r_t = -cost_t

    """

    scene_file = get_scene('quadrotor')

    def __init__(self, *args, **kwargs):
        kwargs['scene'] = self.scene_file
        super().__init__(*args, **kwargs)

        self.drone = None # type: VREPObject
        self.goal = None # type: VREPObject
        self.ref = None # type: VREPObject

        self.observation_space = spaces.Box(-np.inf,
                                            np.inf, OBSERVATION_SPACE, dtype=np.float)
        self.action_space = spaces.Box(-np.inf,
                                       np.inf, ACTION_SPACE, dtype=np.float)

        self.time_step = 0

        self.collision = False

    def _do_reset(self):
        self.drone = self.sim.get_object_by_name('Quadricopter')
        self.goal = self.sim.get_object_by_name('Quadricopter_goal')
        self.ref = self.sim.get_object_by_name('Quadricopter_ref')

        drone_pos = self.drone.get_position(stream=True)
        drone_ori = self.drone.get_orientation(stream=True)
        drone_lv, drone_av = self.drone.get_velocity(stream=True)

        goal_pos = np.array(self.goal.get_position(stream=True))

        self._rand_init_drone()
        self._gen_goal()
        self.sim.step_blocking_simulation()

        self.time_step = 0

    def _gen_goal(self):
        goal_pos = np.random.uniform(LOWER_BOUNDS, UPPER_BOUNDS)
        self.goal.set_position(*goal_pos)

    def _rand_init_drone(self):
        drone_pos = np.random.uniform(LOWER_BOUNDS, UPPER_BOUNDS)
        log.debug('Resetting drone to: {}'.format(drone_pos.tolist()))
        # TODO: ANother hack
        self.sim.call_script_function(
            'reset_quad_position',
            (
                [],
                drone_pos.tolist(),
                [],
                ''
            ),
            script_name='Quadricopter'
        )

    def _do_action(self, action: np.ndarray):
        assert action.shape == ACTION_SPACE
        if self.sim.get_signal('drone_state', int) != DroneStates.PROP_CONTROL:
            self.sim.set_signal('drone_state', DroneStates.PROP_CONTROL)

        log.debug('Setting actions: {}'.format(action.tolist()))
        for i in range(ACTION_SPACE[0]):
            self.sim.set_signal('prop{}_vel'.format(i + 1), action[i])

        self.time_step += 1

    def _get_done(self):
        # Compute distance between goal and drone
        # goal_pos = np.array(self.goal.get_position(stream=True))
        # drone = np.array(self.drone.get_position(stream=True))
        # dist = np.linalg.norm(goal_pos - drone)

        return (self.time_step >= TIME_THRESHOLD) or self.collision

    def _get_obs(self):
        drone_pos = self.drone.get_position(stream=True)
        drone_ori = self.drone.get_orientation(stream=True)
        drone_lv, drone_av = self.drone.get_velocity(stream=True)

        goal_pos = np.array(self.goal.get_position(stream=True))

        # TODO: Hack because the only collidable object is floor
        if drone_pos[2] <= 0.0155:
            collision = 1
        else:
            collision = 0

        self.collision = bool(collision)

        return np.concatenate([
            drone_pos, drone_ori,
            drone_lv, drone_av,
            goal_pos,
            (collision,),
        ])

    def _get_reward(self):
        drone_pos = self.drone.get_position(stream=True)
        drone_ori = self.drone.get_orientation(stream=True)
        drone_lv, drone_av = self.drone.get_velocity(stream=True)

        goal_pos = np.array(self.goal.get_position(stream=True))

        p_t = np.linalg.norm(drone_pos - goal_pos)
        angle_t = np.linalg.norm(drone_ori)
        vel_t = np.linalg.norm(drone_lv)
        avel_t = np.linalg.norm(drone_av)

        cost_t = 4e-3 * p_t + 5e-4 * vel_t + 2e-4 * angle_t + 3e-4 * avel_t

        return -cost_t
