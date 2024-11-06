"""
The model - a 2D lattice where agents live and have an opinion
"""
import random
from collections import Counter

import mesa


class ColorCell(mesa.Agent):
    """
    Represents a cell's opinion (visualized by a color)
    """

    OPINIONS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

    def __init__(self, pos, unique_id, model, initial_state):
        """
        Create a cell, in the given state, at the given row, col position.
        """
        super().__init__(unique_id, model)
        self._row = pos[0]
        self._col = pos[1]
        self._state = initial_state
        self._next_state = None
        self._is_cult_leader = False

    def get_col(self):
        """Return the col location of this cell."""
        return self._col

    def get_row(self):
        """Return the row location of this cell."""
        return self._row

    def get_state(self):
        """Return the current state (OPINION) of this cell."""
        return self._state

    def get_is_cult_leader(self):
        return self._is_cult_leader

    def determine_opinion(self):
        """
        Determines the agent opinion for the next step by polling its neighbors
        The opinion is determined by the majority of the 8 neighbors' opinion
        A choice is made at random in case of a tie
        The next state is stored until all cells have been polled
        """
        _cultist_influence = 4
        _neighbor_iter = self.model.grid.iter_neighbors((self._row, self._col), True)
        _check_cultist_iter = self.model.grid.iter_neighbors((self._row, self._col), False, radius=_cultist_influence)
        neighbors_opinion = Counter(n.get_state() for n in _neighbor_iter)
        # Following is a a tuple (attribute, occurrences)
        polled_opinions = neighbors_opinion.most_common()
        tied_opinions = []
        low_tied_opinions = []
        for neighbor in polled_opinions:
            if neighbor[1] == polled_opinions[0][1]:
                tied_opinions.append(neighbor)
            if neighbor[1] == polled_opinions[-1][1]:
                low_tied_opinions.append(neighbor)

        cult_leader_opinion = None
        dist = 10000
        for neighbor in _check_cultist_iter:
            if neighbor.get_is_cult_leader():
                new_dist = abs(self._row - neighbor.get_row()) + abs(
                    self._col - neighbor.get_col())  # Manhattan distance
                if new_dist < dist:
                    dist = new_dist
                cult_leader_opinion = neighbor.get_state()

        if cult_leader_opinion and random.random() < (0.9 - dist * 0.2):
            self._next_state = cult_leader_opinion
        elif random.random() < 0.1:
            self._next_state = self.random.choice(low_tied_opinions)[0]
        else:
            self._next_state = self.random.choice(tied_opinions)[0]

    def assume_opinion(self):
        """
        Set the state of the agent to the next state
        """
        if not self._is_cult_leader:
            self._state = self._next_state


class ColorPatches(mesa.Model):
    """
    represents a 2D lattice where agents live
    """

    def __init__(self, width=20, height=20):
        """
        Create a 2D lattice with strict borders where agents live
        The agents next state is first determined before updating the grid
        """
        super().__init__()
        self._grid = mesa.space.SingleGrid(width, height, torus=False)

        # self._grid.coord_iter()
        #  --> should really not return content + col + row
        #  -->but only col & row
        # for (contents, col, row) in self._grid.coord_iter():
        # replaced content with _ to appease linter
        for _, (row, col) in self._grid.coord_iter():
            cell = ColorCell(
                (row, col), row + col * row, self, ColorCell.OPINIONS[self.random.randrange(0, 16)]
            )
            self._grid.place_agent(cell, (row, col))

        self.step()
        self.running = True

    def step(self):
        """
        Perform the model step in two stages:
        - First, all agents determine their next opinion based on their neighbors current opinions
        - Then, all agents update their opinion to the next opinion
        """
        self.agents.do("determine_opinion")
        self.agents.do("assume_opinion")
        self._steps += 1

        if self._steps % 100 == 0:
            self.manipulate_random_cell()

    def manipulate_random_cell(self):
        """
        Selects a random cell in the grid and manipulates it by changing its opinion.
        """
        # Get a random (row, col) position from the grid
        random_position = self.random.choice(list(self.grid.coord_iter()))

        # Extract the coordinates from the random position tuple
        row, col = random_position[1]
        print(random_position)

        # Get the agent at the selected random position
        agent = self.grid.get_cell_list_contents([(row, col)])[0]

        # Manipulate the agent - change its opinion to a random new one
        new_opinion = ColorCell.OPINIONS[-1]
        agent._state = new_opinion
        agent._is_cult_leader = True

        print(f"Random cell at ({row}, {col}) changed its opinion to {new_opinion}")

    @property
    def grid(self):
        """
        /mesa/visualization/modules/CanvasGridVisualization.py
        is directly accessing Model.grid
             76     def render(self, model):
             77         grid_state = defaultdict(list)
        ---> 78         for y in range(model.grid.height):
             79             for x in range(model.grid.width):
             80                 cell_objects = model.grid.get_cell_list_contents([(x, y)])

        AttributeError: 'ColorPatches' object has no attribute 'grid'
        """
        return self._grid
