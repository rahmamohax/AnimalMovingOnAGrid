import random
from typing import List, Tuple, Dict, Union

GRID_SIZE: Tuple[int, int] = (10, 10)
ROWS, COLS = GRID_SIZE

Animal = Dict[str, any]

GridContent = Union[Animal, str]
Grid = Dict[Tuple[int, int], GridContent]
Stats = Dict[str, int]

# Precomputed directions to avoid building lists inside recursive calls
DIRECTIONS = ((0, 1), (0, -1), (1, 0), (-1, 0))
DIRECTIONS_WITH_STAY = DIRECTIONS + ((0, 0),)



def initial_global_stats() -> Stats:
    """Created a pure initializer for stats to avoid mutating globals."""
    return {'total_deaths': 0, 'total_births': 0, 'food_eaten': 0, 'steps': 0}


def move_safe(pos: Tuple[int, int], direction: Tuple[int, int]) -> Tuple[int, int]:
    """Calculates the new position, wrapping around the grid"""
    new_r = (pos[0] + direction[0]) % ROWS
    new_c = (pos[1] + direction[1]) % COLS
    return (new_r, new_c)


def get_random_direction() -> Tuple[int, int]:
    return random.choice(DIRECTIONS_WITH_STAY)


def merge_stats(stats1: Stats, stats2: Stats) -> Stats:
    all_keys = list(set(stats1) | set(stats2))

    def _merge(keys: List[str], idx: int, acc: Stats) -> Stats:
        if idx == len(keys):
            return acc
        key = keys[idx]
        next_acc = {**acc, key: stats1.get(key, 0) + stats2.get(key, 0)}
        return _merge(keys, idx + 1, next_acc)

    return _merge(all_keys, 0, {})


def update_totals(global_stats: Stats, step_stats: Stats) -> Stats:
    """Accumulates totals without mutating shared state (functional fold)."""
    return {
        'total_deaths': global_stats['total_deaths'] + step_stats['deaths_starvation'],
        'total_births': global_stats['total_births'] + step_stats['births'],
        'food_eaten': global_stats['food_eaten'] + step_stats['food_eaten'],
        'steps': global_stats['steps'] + 1
    }


def build_coords(r: int = 0, c: int = 0, acc: List[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
    """Recursive grid coordinate builder."""
    acc = [] if acc is None else acc
    if r == ROWS:
        return acc
    next_acc = acc + [(r, c)]
    next_r, next_c = (r + 1, 0) if c + 1 == COLS else (r, c + 1)
    return build_coords(next_r, next_c, next_acc)


def place_entities(coords: List[Tuple[int, int]], grid: Grid, remaining: int, marker: GridContent) -> Tuple[Grid, List[Tuple[int, int]]]:
    if remaining == 0 or not coords:
        return grid, coords
    head, *tail = coords
    if head in grid:
        return place_entities(tail, grid, remaining, marker)
    new_grid = {**grid, head: marker}
    return place_entities(tail, new_grid, remaining - 1, marker)


def copy_grid_without(grid: Grid, skip_positions: set) -> Grid:
    """Recursively copies the grid while skipping provided positions."""
    items = list(grid.items())

    def _copy(idx: int, acc: Grid) -> Grid:
        if idx == len(items):
            return acc
        pos, content = items[idx]
        if pos in skip_positions:
            return _copy(idx + 1, acc)
        return _copy(idx + 1, {**acc, pos: content})

    return _copy(0, {})


    # Returns a list of ((row, col), animal_dict) for each animal
def collect_animals(grid: Grid) -> List[Tuple[Tuple[int, int], Animal]]:
    """Recursively gathers animals (replaces list comprehension)."""
    items = list(grid.items())

    def _collect(idx: int, acc: List[Tuple[Tuple[int, int], Animal]]) -> List[Tuple[Tuple[int, int], Animal]]:
        if idx == len(items):
            return acc
        pos, content = items[idx]
        if isinstance(content, dict) and 'id' in content:
            return _collect(idx + 1, acc + [(pos, content)])
        return _collect(idx + 1, acc)

    return _collect(0, [])


def count_animals(grid: Grid) -> int:
    items = list(grid.values())

    def _count(idx: int, acc: int) -> int:
        if idx == len(items):
            return acc
        increment = 1 if isinstance(items[idx], dict) and 'id' in items[idx] else 0
        return _count(idx + 1, acc + increment)

    return _count(0, 0)


def generate_neighbors(origin: Tuple[int, int]) -> List[Tuple[int, int]]:
    """ builds neighbor list to avoid comprehension."""
    directions = DIRECTIONS

    def _build(idx: int, acc: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        if idx == len(directions):
            return acc
        next_acc = acc + [move_safe(origin, directions[idx])]
        return _build(idx + 1, next_acc)

    return _build(0, [])


def find_first_empty(spots: List[Tuple[int, int]], grid: Grid, idx: int = 0) -> Union[Tuple[int, int], None]:
    """finds the first empty neighbor"""
    if idx == len(spots):
        return None
    if spots[idx] not in grid:
        return spots[idx]
    return find_first_empty(spots, grid, idx + 1)


def initialize_grid() -> Grid:
    """Pure recursive initialization of the grid (no loops)."""
    initial_grid: Grid = {
        (1, 1): {'id': 10, 'energy': 10, 'age': 0, 'type': 'Rabbit'},
        (3, 4): {'id': 20, 'energy': 10, 'age': 0, 'type': 'Rabbit'},
        (8, 8): {'id': 30, 'energy': 10, 'age': 0, 'type': 'Rabbit'},
    }

    coords = random.sample(build_coords(), ROWS * COLS)  # randomness preserved without loops
    obstacle_count = int(ROWS * COLS * 0.1)
    food_count = int(ROWS * COLS * 0.25)

    grid_with_obstacles, remaining = place_entities(coords, initial_grid, obstacle_count, '#')
    grid_with_food, _ = place_entities(remaining, grid_with_obstacles, food_count, 'F')
    return grid_with_food


# Higher-Order Function: Processes a single animal's turn
def pure_process_animal_turn(grid: Grid, pos: Tuple[int, int], animal: Animal) -> Tuple[Grid, Stats]:
    """
    Handles a single animal's movement and interaction (Pure Function).
    Returns a new grid state and the immutable statistics generated by this turn.
    """

    turn_stats: Stats = {
        'deaths_starvation': 0, 'births': 0, 'food_eaten': 0,
        'obstacle_encounters': 0, 'conflicts': 0
    }

    if animal['energy'] <= 0:
        # Recursive copy replaces comprehension-based removal
        new_grid = copy_grid_without(grid, {pos})
        turn_stats['deaths_starvation'] = 1
        return new_grid, turn_stats

    energy_cost = 2
    updated_animal = {**animal, 'energy': animal['energy'] - energy_cost, 'age': animal['age'] + 1}

    direction = get_random_direction()
    new_pos = move_safe(pos, direction)
    target_content = grid.get(new_pos)

    # Remove current position (and optionally consumed food) 
    skip_positions = {pos} | ({new_pos} if target_content == 'F' else set())
    grid_after_move = copy_grid_without(grid, skip_positions)

    final_pos = pos

    if target_content == '#':
        updated_animal = {**updated_animal, 'energy': updated_animal['energy'] - 1}
        turn_stats['obstacle_encounters'] = 1
        final_pos = pos

    elif isinstance(target_content, dict) and 'id' in target_content:
        updated_animal = {**updated_animal, 'energy': updated_animal['energy'] - 1}
        turn_stats['conflicts'] = 1
        final_pos = pos

    elif target_content == 'F':
        updated_animal = {**updated_animal, 'energy': updated_animal['energy'] + 5}
        turn_stats['food_eaten'] = 1
        final_pos = new_pos

    else:
        final_pos = new_pos

    final_grid = {**grid_after_move, final_pos: updated_animal}

    if updated_animal['energy'] > 5 and updated_animal['age'] > 2 and random.random() < 0.25:
        neighbors = generate_neighbors(final_pos)
        empty_spot = find_first_empty(neighbors, final_grid)

        if empty_spot:
            baby: Animal = {'id': random.randint(100, 999), 'energy': 3, 'age': 0, 'type': animal['type']}
            final_grid = {
                **final_grid,
                empty_spot: baby,
                final_pos: {**updated_animal, 'energy': updated_animal['energy'] // 2}
            }
            turn_stats['births'] = 1

    return final_grid, turn_stats


# --- 3. The Core Simulation Loop (Invariant Programming & Recursion) ---

def sim_step(current_grid: Grid) -> Tuple[Grid, Stats]:
    """Performs one step of the simulation, accumulating state changes and stats."""

    # Recursive collection replaces comprehension
    initial_animals: List[Tuple[Tuple[int, int], Animal]] = sorted(
        collect_animals(current_grid),
        key=lambda item: item[1]['id']
    )

    def recursive_processor(
        remaining_animals: List[Tuple[Tuple[int, int], Animal]],
        accumulated_grid: Grid,
        accumulated_stats: Stats
    ) -> Tuple[Grid, Stats]:
        """
        Tail-recursive function to process the list of animals.
        Accumulator (A): `(accumulated_grid, accumulated_stats)`.
        Work still to do (S): `remaining_animals`. (Invariant Programming)
        Principle of Communicating Vases: S shrinks (remaining_animals) while A grows (accumulated_grid).
        """
        if not remaining_animals:
            return accumulated_grid, accumulated_stats
        (pos, animal) = remaining_animals[0]
        rest = remaining_animals[1:]

        current_content = accumulated_grid.get(pos)

        if isinstance(current_content, dict) and 'id' in current_content and current_content['id'] == animal['id']:
            new_grid, turn_stats = pure_process_animal_turn(accumulated_grid, pos, animal)
            new_stats = merge_stats(accumulated_stats, turn_stats)
        else:
            new_grid = accumulated_grid
            new_stats = accumulated_stats

        return recursive_processor(rest, new_grid, new_stats)

    initial_stats: Stats = {
        'deaths_starvation': 0, 'births': 0, 'food_eaten': 0,
        'obstacle_encounters': 0, 'conflicts': 0
    }

    return recursive_processor(initial_animals, current_grid, initial_stats)


def run_simulation(initial_grid: Grid, steps: int, global_stats: Stats = None) -> Tuple[Grid, Stats]:
    """
    Main entry point for the simulation. Uses recursion (Divide and Conquer).
    The steps variable acts as the control for the outer recursion.
    """
    stats_acc = initial_global_stats() if global_stats is None else global_stats
    if steps == 0:
        return initial_grid, stats_acc

    next_grid, step_stats = sim_step(initial_grid)
    updated_global_stats = update_totals(stats_acc, step_stats)

    print(f"\n======== STEP {updated_global_stats['steps']} ========")

    display_grid(next_grid)

    current_animals = count_animals(next_grid)
    print(f"Animals: {current_animals} (Born: {step_stats['births']}, Died: {step_stats['deaths_starvation']})")
    print(f"Interactions: Food Eaten: {step_stats['food_eaten']}, Obstacles Hit: {step_stats['obstacle_encounters']}")

    if current_animals == 0:
        print("\nECOSYSTEM COLLAPSED: All animals are gone.")
        return next_grid, updated_global_stats

    return run_simulation(next_grid, steps - 1, updated_global_stats)


def build_row(grid: Grid, r: int, c: int = 0, acc: str = "|") -> str:
    """Recursive row builder to replace nested display loops."""
    if c == COLS:
        return f"{acc}"
    content = grid.get((r, c))
    display_char = '.'
    if isinstance(content, dict) and 'id' in content:
        display_char = content['type'][0]
    elif content == 'F':
        display_char = 'F'
    elif content == '#':
        display_char = '#'
    next_acc = f"{acc} {display_char} |"
    return build_row(grid, r, c + 1, next_acc)


def display_grid(grid: Grid, row: int = 0):
    """Prints the grid state recursively."""
    separator = "-" * (COLS * 3 + 1)
    if row == 0:
        print(separator)
    if row == ROWS:
        return
    print(build_row(grid, row))
    print(separator)
    return display_grid(grid, row + 1)



if __name__ == '__main__':
    initial_state = initialize_grid()
    print("--- FUNCTIONAL SIMULATION (Initial State) ---")
    display_grid(initial_state)

    final_state, final_stats = run_simulation(initial_state, 10)

    print("\n--- SIMULATION COMPLETE (Final Accumulator State) ---")
    print(f"Total Steps: {final_stats['steps']}")
    print(f"Total Deaths: {final_stats['total_deaths']}")
    print(f"Total Births: {final_stats['total_births']}")
    print(f"Total Food Eaten: {final_stats['food_eaten']}")