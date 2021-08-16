import random
import itertools
from enum import IntEnum

import numpy as np
import matplotlib.pyplot as plt
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from matplotlib import colors


class AgentAction(IntEnum):
    """
    Defines the action of an agent
    """

    STEP_FORWARD = 0
    STEP_BACKWARD = 1
    STEP_LEFT = 2
    STEP_RIGHT = 3
    ROTATE_LEFT = 4
    ROTATE_RIGHT = 5
    STAND_STILL = 6
    TAG = 7

    @classmethod
    def random(cls):
        """
        Return a random action out of the 8 possible values
        """
        return AgentAction(random.randint(0, cls.size() - 1))

    @classmethod
    def values(cls):
        """
        Return all possible values as integers
        """
        return [v.value for v in cls.__members__.values()]

    @classmethod
    def is_valid(cls, action):
        """
        Check if the given action is valid
        """
        if isinstance(action, int):
            return action in cls.values()
        elif isinstance(action, AgentAction):
            return action in cls.__members__.keys()
        return False

    @classmethod
    def size(cls):
        """
        Return the number of possible actions (i.e. 8)
        """
        return len(cls.__members__)


class CPRGridActionSpace(spaces.Discrete):
    """
    The action space spanned by all the possible agent actions
    """

    def __init__(self):
        super(CPRGridActionSpace, self).__init__(AgentAction.size())

    def sample(self):
        """
        Sample a random action from the action space
        """
        return AgentAction.random()

    def contains(self, action):
        """
        Check if the given action is contained in the action space
        """
        return AgentAction.is_valid(action)

    def __repr__(self):
        return "CPRGridActionSpace()"

    def __eq__(self, other):
        return isinstance(other, CPRGridActionSpace)


class AgentOrientation(IntEnum):
    """
    Defines the orientation of an agent in an unspecified position,
    as the 4 cardinal directions (N, E, S, W)
    """

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    def rotate_left(self):
        """
        Return a new orientation after the agent rotates itself to its left
        """
        return AgentOrientation((self.value - 1) % self.size())

    def rotate_right(self):
        """
        Return a new orientation after the agent rotates itself to its right
        """
        return AgentOrientation((self.value + 1) % self.size())

    @classmethod
    def random(cls):
        """
        Return a random orientation out of the 4 possible values
        """
        return AgentOrientation(random.randint(0, cls.size() - 1))

    @classmethod
    def size(cls):
        """
        Return the number of possible orientations (i.e. 4)
        """
        return len(cls.__members__)


class AgentPosition:
    """
    Defines the position of an agent as a triplet (x, y, o), where (x, y)
    are coordinates on a 2D grid (with origin on the upper left corner)
    and (o, ) is the orientation of the agent
    """

    def __init__(self, x, y, o):
        assert isinstance(
            o, AgentOrientation
        ), "The given orientation must be an instance of AgentOrientation"
        self.x = x
        self.y = y
        self.o = o

    def step_forward(self):
        """
        Return the new position of the agent after stepping forward
        """
        if self.o == AgentOrientation.UP:
            return AgentPosition(self.x, self.y - 1, self.o)
        elif self.o == AgentOrientation.RIGHT:
            return AgentPosition(self.x + 1, self.y, self.o)
        elif self.o == AgentOrientation.DOWN:
            return AgentPosition(self.x, self.y + 1, self.o)
        elif self.o == AgentOrientation.LEFT:
            return AgentPosition(self.x - 1, self.y, self.o)
        return self

    def step_backward(self):
        """
        Return the new position of the agent after stepping backward
        """
        if self.o == AgentOrientation.UP:
            return AgentPosition(self.x, self.y + 1, self.o)
        elif self.o == AgentOrientation.RIGHT:
            return AgentPosition(self.x - 1, self.y, self.o)
        elif self.o == AgentOrientation.DOWN:
            return AgentPosition(self.x, self.y - 1, self.o)
        elif self.o == AgentOrientation.LEFT:
            return AgentPosition(self.x + 1, self.y, self.o)
        return self

    def step_left(self):
        """
        Return the new position of the agent after stepping to its left
        """
        if self.o == AgentOrientation.UP:
            return AgentPosition(self.x - 1, self.y, self.o)
        if self.o == AgentOrientation.RIGHT:
            return AgentPosition(self.x, self.y - 1, self.o)
        if self.o == AgentOrientation.DOWN:
            return AgentPosition(self.x + 1, self.y, self.o)
        if self.o == AgentOrientation.LEFT:
            return AgentPosition(self.x, self.y + 1, self.o)

    def step_right(self):
        """
        Return the new position of the agent after stepping to its right
        """
        if self.o == AgentOrientation.UP:
            return AgentPosition(self.x + 1, self.y, self.o)
        if self.o == AgentOrientation.RIGHT:
            return AgentPosition(self.x, self.y + 1, self.o)
        if self.o == AgentOrientation.DOWN:
            return AgentPosition(self.x - 1, self.y, self.o)
        if self.o == AgentOrientation.LEFT:
            return AgentPosition(self.x, self.y - 1, self.o)

    def rotate_left(self):
        """
        Return the new position of the agent after rotating left
        """
        return AgentPosition(self.x, self.y, self.o.rotate_left())

    def rotate_right(self):
        """
        Return the new position of the agent after rotating right
        """
        return AgentPosition(self.x, self.y, self.o.rotate_right())

    def stand_still(self):
        """
        Return the new position of the agent after standing still
        """
        return self

    def tag(self):
        """
        Return the new position of the agent after taggin an opponent
        """
        return self

    def get_new_position(self, action):
        """
        Given an action, return the new position of the agent
        """
        assert isinstance(
            action, AgentAction
        ), "The given action must be an instance of AgentAction"
        return getattr(self, action.name.lower())()

    def __repr__(self):
        return f"AgentPosition({self.x}, {self.y}, {self.o})"

    def __eq__(self, other):
        return (
            isinstance(other, AgentPosition)
            and self.x == other.x
            and self.y == other.y
            and self.o == other.o
        )


class GridCell(IntEnum):
    """
    Defines what could fit in a cell of the 2D grid, i.e.
    either an agent or a resource or an empty cell
    """

    EMPTY = 0
    RESOURCE = 1
    AGENT = 2

    @classmethod
    def values(cls):
        """
        Return all possible values as integers
        """
        return [v.value for v in cls.__members__.values()]

    @classmethod
    def size(cls):
        """
        Return the number of possible cell types (i.e. 3)
        """
        return len(cls.__members__)


class CPRGridEnv(gym.Env):
    """
    Defines the CPR appropriation Gym environment
    """

    # Rewards
    RESOURCE_COLLECTION_REWARD = 1

    # Colors
    GRID_CELL_COLORS = {
        GridCell.EMPTY: "black",
        GridCell.RESOURCE: "green",
        GridCell.AGENT: "red",
    }
    FOV_OWN_AGENT_COLOR = "blue"
    COLORMAP = colors.ListedColormap(list(GRID_CELL_COLORS.values()))
    COLOR_BOUNDARIES = colors.BoundaryNorm(
        GridCell.values() + [GridCell.size()], GridCell.size()
    )

    # Rendering option
    FIGSIZE = (12, 10)

    # Gym variables
    metadata = {"render.modes": ["human", "rgb_array"]}

    def __init__(
        self,
        n_agents,
        grid_width,
        grid_height,
        fov_squares_front=20,
        fov_squares_side=10,
        tagging_ability=True,
        beam_squares_front=20,
        beam_squares_width=5,
        ball_radius=2,
        max_steps=1000,
    ):
        super(CPRGridEnv, self).__init__()

        self.n_agents = n_agents
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.fov_squares_front = fov_squares_front
        self.fov_squares_side = fov_squares_side
        self.tagging_ability = tagging_ability
        self.beam_squares_front = beam_squares_front
        self.beam_squares_width = beam_squares_width
        self.ball_radius = ball_radius
        self.max_steps = max_steps

        self.action_space = CPRGridActionSpace()
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(
                self.fov_squares_front,
                self.fov_squares_side * 2 + 1,
                3,
            ),
            dtype=np.uint8,
        )

        self.elapsed_steps = None
        self.agent_positions = None
        self.grid = None
        self.reset()

    def reset(self):
        """
        Spawns a new environment by assigning random positions to the agents
        and initializing a new 2D grid
        """
        self.elapsed_steps = 0
        self.agent_positions = [self._random_position() for _ in range(self.n_agents)]
        self.grid = self._get_initial_grid()

    def _random_position(self):
        """
        Returns a random position in the 2D grid
        """
        return AgentPosition(
            x=random.randint(0, self.grid_width - 1),
            y=random.randint(0, self.grid_height - 1),
            o=AgentOrientation.random(),
        )

    def _get_initial_grid(self):
        """
        Initializes the 2D grid by setting agent positions and
        initial random resources
        """
        # Assign agent positions in the grid
        grid = np.full((self.grid_height, self.grid_width), GridCell.EMPTY.value)
        for agent_position in self.agent_positions:
            grid[agent_position.y, agent_position.x] = GridCell.AGENT.value

        # Compute uniformely distributes resources
        resource_mask = np.random.randint(
            low=0, high=2, size=(self.grid_height, self.grid_width), dtype=bool
        )
        ys, xs = resource_mask.nonzero()
        resource_indices = list(zip(list(xs), list(ys)))

        # Assign resources to cells that are not occupied by agents
        for x, y in resource_indices:
            if grid[y, x] == GridCell.EMPTY.value:
                grid[y, x] = GridCell.RESOURCE.value

        return grid

    def step(self, actions):
        """
        Perform a step in the environment by moving all the agents
        and return one observation for each agent
        """
        assert (
            isinstance(actions, list) and len(actions) == self.n_agents
        ), "Actions should be given as a list with lenght equal to the number of agents"

        # Initiliaze variables
        observations = [None] * self.n_agents
        rewards = [-self.RESOURCE_COLLECTION_REWARD] * self.n_agents
        dones = [False] * self.n_agents

        # Move all agents
        for agent_handle, action in enumerate(actions):
            # Compute new position
            new_agent_position = self._compute_new_agent_position(agent_handle, action)
            self.agent_positions[agent_handle] = new_agent_position

            # Assign reward for resource collection
            if self._has_resource(new_agent_position):
                rewards[agent_handle] = self.RESOURCE_COLLECTION_REWARD

            # Move the agent only after checking for resource presence
            self._move_agent(agent_handle, new_agent_position)

        # Check if we reached end of episode
        self.elapsed_steps += 1
        if self._is_resource_depleted() or self.elapsed_steps == self.max_steps:
            dones = [True] * self.n_agents

        # Compute observations for each agent
        for agent_handle in range(self.n_agents):
            observations = self._get_observation(agent_handle)

        # Respawn resources
        self._respawn_resources()

        return observations, rewards, dones, {}

    def _compute_new_agent_position(self, agent_handle, action):
        """
        Compute a new position for the given agent, after performing
        the given action
        """
        assert agent_handle in range(
            self.n_agents
        ), "The given agent handle does not exist"

        # Compute new position
        current_position = self.agent_positions[agent_handle]
        new_position = current_position.get_new_position(action)

        # If move is not feasible the agent stands still
        if not self._is_move_feasible(new_position):
            return current_position

        return new_position

    def _move_agent(self, agent_handle, new_position):
        """
        Set the previous position as empty and the new one as occupied
        """
        assert isinstance(
            new_position, AgentPosition
        ), "The given position should be an instance of AgentPosition"
        current_position = self.agent_positions[agent_handle]
        self.grid[current_position.y, current_position.x] = GridCell.EMPTY.value
        self.grid[new_position.y, new_position.x] = GridCell.AGENT.value

    def _is_move_feasible(self, position):
        """
        Check if the move leading the agent to the given position
        is a feasible move or an illegal one
        """
        return self._is_position_in_grid(position) and not self._is_position_occupied(
            position
        )

    def _is_position_occupied(self, position):
        """
        Check if the given position is occupied by another agent in the grid
        """
        assert isinstance(
            position, AgentPosition
        ), "The given position should be an instance of AgentPosition"
        return self.grid[position.y, position.x] == GridCell.AGENT.value

    def _is_position_in_grid(self, position):
        """
        Check if the given position is within the boundaries of the grid
        """
        assert isinstance(
            position, AgentPosition
        ), "The given position should be an instance of AgentPosition"
        if position.x < 0 or position.x >= self.grid_width:
            return False
        if position.y < 0 or position.y >= self.grid_height:
            return False
        return True

    def _has_resource(self, position):
        """
        Check if the given position is occupied by a resource in the grid
        """
        assert isinstance(
            position, AgentPosition
        ), "The given position should be an instance of AgentPosition"
        return self.grid[position.y, position.x] == GridCell.RESOURCE.value

    def _is_resource_depleted(self):
        """
        Check if there is at least one resource available in the environment
        or if the resource is depleted
        """
        return len(self.grid[self.grid == GridCell.RESOURCE.value]) == 0

    def _get_observation(self, agent_handle):
        """
        Extract a rectangular FOV based on the given agent's position
        and convert it into an RGB image
        """
        # Extract the FOV and convert it to 3 channels
        fov = self._extract_fov(agent_handle)
        fov = np.stack((fov,) * 3, axis=-1)

        # Set colors for resources and agents
        fov = np.where(
            fov == GridCell.RESOURCE,
            colors.to_rgb(self.GRID_CELL_COLORS[GridCell.RESOURCE]),
            fov,
        )
        fov = np.where(
            fov == GridCell.AGENT,
            colors.to_rgb(self.GRID_CELL_COLORS[GridCell.AGENT]),
            fov,
        )
        fov[0, self.fov_squares_side] = colors.to_rgb(self.FOV_OWN_AGENT_COLOR)

        return fov

    def _respawn_resources(self):
        """
        Respawn resources based on the number of already-spawned resources
        in a ball centered around each currently empty location
        """
        for x, y in itertools.product(range(self.grid_width), range(self.grid_height)):
            if self.grid[y, x] == GridCell.EMPTY.value:
                l = len(self._extract_ball(x, y))
                p = self._respawn_probability(l)
                if np.random.binomial(1, p):
                    self.grid[y, x] = GridCell.RESOURCE.value

    def _respawn_probability(self, l):
        """
        Compute the respawn probability of a resource in an unspecified
        location based on the number of nearby resources
        """
        if l == 1 or l == 2:
            return 0.01
        elif l == 3 or l == 4:
            return 0.05
        elif l > 4:
            return 0.1
        return 0

    def _pad_grid(self, grid, x, y, xl, yl):
        """
        Pad the 2D grid by computing pad widths based
        on the given position and span lenghts in both axes
        """
        x_pad_width = (
            abs(np.clip(x - xl, None, 0)),
            np.clip(x + xl - self.grid_width + 1, 0, None),
        )
        y_pad_width = (
            abs(np.clip(y - yl, None, 0)),
            np.clip(y + yl - self.grid_height + 1, 0, None),
        )
        padded_grid = np.pad(
            grid,
            pad_width=[y_pad_width, x_pad_width],
            mode="constant",
            constant_values=GridCell.EMPTY.value,
        )
        return padded_grid, x_pad_width, y_pad_width

    def _extract_fov(self, agent_handle):
        """
        Extract a rectangular local observation from the 2D grid,
        from the point of view of the given agent
        """
        # Get the current agent's position
        agent_position = self.agent_positions[agent_handle]

        # Rotate the grid based on agent's orientation
        grid = self.grid.copy()
        k = (
            1
            if agent_position.o == AgentOrientation.LEFT
            else 2
            if agent_position.o == AgentOrientation.UP
            else 3
            if agent_position.o == AgentOrientation.RIGHT
            else 0
        )
        rotated_grid = np.rot90(grid, k=k)

        # Compute agent's coordinates on the rotated grid
        coords = list(
            itertools.product(range(self.grid_height), range(self.grid_width))
        )
        coords = np.array(coords).reshape(self.grid_height, self.grid_width, 2)
        rotated_coords = np.rot90(coords, k=k)
        rotated_y, rotated_x = np.argwhere(
            (rotated_coords[:, :, 0] == agent_position.y)
            & (rotated_coords[:, :, 1] == agent_position.x)
        )[0]

        # Pad the 2D grid so as not have indexing errors in FOV extraction
        padded_grid, x_pad_width, y_pad_width = self._pad_grid(
            rotated_grid,
            rotated_x,
            rotated_y,
            self.fov_squares_side,
            self.fov_squares_front + k % 2,
        )

        # Extract the FOV
        sx, ex = (
            x_pad_width[0] + rotated_x - self.fov_squares_side,
            x_pad_width[0] + rotated_x + self.fov_squares_side + 1,
        )
        sy, ey = (
            y_pad_width[0] + rotated_y,
            y_pad_width[0] + rotated_y + self.fov_squares_front,
        )
        fov = padded_grid[sy:ey, sx:ex]
        assert fov.shape == (
            self.fov_squares_front,
            self.fov_squares_side * 2 + 1,
        ), "There was an error in FOV extraction, incorrect shape"

        return fov

    def _extract_ball(self, x, y):
        """
        Extract a ball-shaped local patch from the 2D grid,
        centered around the given position
        """
        # Pad the 2D grid so as not have indexing errors in ball extraction
        padded_grid = self._pad_grid(
            self.grid,
            x,
            y,
            self.ball_radius,
            self.ball_radius,
        )

        # Extract the ball
        sx, ex = x - self.ball_radius, x + self.ball_radius + 1
        sy, ey = y - self.ball_radius, y + self.ball_radius + 1
        ball = padded_grid[sy:ey, sx:ex]

        # Compute a boolean mask shaped like a ball
        # (see https://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array)
        kernel = np.zeros((2 * self.ball_radius + 1, 2 * self.ball_radius + 1))
        yg, xg = np.ogrid[
            -self.ball_radius : self.ball_radius + 1,
            -self.ball_radius : self.ball_radius + 1,
        ]
        mask = xg ** 2 + yg ** 2 <= self.ball_radius ** 2
        kernel[mask] = 1

        return ball[kernel]

    def plot_observation(self, obs):
        """
        Plot the given observation as an RGB image
        """
        _, ax = plt.subplots(figsize=self.FIGSIZE)
        ax.imshow(obs * 255.0, origin="upper")
        ax.axis("off")
        plt.show()

    def render(self, mode="human"):
        """
        Render the environment as an RGB image
        """
        _, ax = plt.subplots(figsize=self.FIGSIZE)
        ax.imshow(
            self.grid, cmap=self.COLORMAP, norm=self.COLOR_BOUNDARIES, origin="upper"
        )
        ax.axis("off")
        plt.show()

    def close(self):
        return