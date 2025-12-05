import random
from typing import Dict, List, Tuple, Set

GRID_SIZE = 10
INITIAL_ANIMALS = 8
FOOD_SPAWN_RATE = 0.07      # chance each turn for new food on an empty cell
OBSTACLE_DENSITY = 0.10     # ~10% of cells become obstacles at start

INITIAL_ENERGY = 6
INITIAL_HEALTH = 10

REPRODUCTION_ENERGY = 10    # energy level at which animals can reproduce
MAX_AGE = 40


# ------------------------------
# Types (for clarity)
# ------------------------------

# Each animal is represented as an immutable-ish dict
Animal = Dict[str, int]

# World holds all state; functions will take a world and return a new world
World = Dict[str, object]


def make_animal(x: int, y: int) -> Animal:
    return {
        "x": x,
        "y": y,
        "energy": INITIAL_ENERGY,
        "health": INITIAL_HEALTH,
        "age": 0,
    }


def move_animal(animal: Animal, obstacles: Set[Tuple[int, int]]) -> Animal:
    """Return a NEW animal dict after attempting to move and losing energy."""
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    random.shuffle(directions)

    x, y = animal["x"], animal["y"]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            if (nx, ny) not in obstacles:
                x, y = nx, ny
                break

    # return a *new* animal record with updated position and energy
    return {
        **animal,
        "x": x,
        "y": y,
        "energy": animal["energy"] - 1,
    }


def animal_after_eating(animal: Animal) -> Animal:
    """Return a NEW animal dict after gaining energy from food."""
    return {**animal, "energy": animal["energy"] + 4}


def update_life(animal: Animal) -> Animal:
    """
    Age and health update (pure).
    Returns a NEW animal dict.
    """
    age = animal["age"] + 1
    health = animal["health"]
    energy = animal["energy"]

    # Age-related decay
    if age % 8 == 0:
        health -= 1

    # Starvation penalty
    if energy <= 1:
        health -= 2

    # Recovery when well fed
    if energy >= 8 and health < INITIAL_HEALTH:
        health += 1

    health = max(0, min(INITIAL_HEALTH, health))

    return {
        **animal,
        "age": age,
        "health": health,
    }


def is_dead(animal: Animal) -> bool:
    return (
        animal["energy"] <= 0
        or animal["health"] <= 0
        or animal["age"] >= MAX_AGE
    )
# Yarab Shahd T2bad bl Dollar $$$$$$$$$$$
# I Love Shahd Mustafa Abdelnaby Mustafa Mohamed Shalaby<3
#Toz fy Ammar El Desuky
#El Abd eleswed Amr Ramadan Mohamed Mohamed Mohamed

# ------------------------------
# World construction (functional style)
# ------------------------------

def random_obstacles() -> Set[Tuple[int, int]]:
    """Return a new set of obstacle positions."""
    coords: Set[Tuple[int, int]] = set()
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if random.random() < OBSTACLE_DENSITY:
                coords.add((i, j))
    return coords


def random_animals(obstacles: Set[Tuple[int, int]]) -> List[Animal]:
    """Return a list of animals placed on non-obstacle cells."""
    animals: List[Animal] = []
    occupied: Set[Tuple[int, int]] = set(obstacles)

    while len(animals) < INITIAL_ANIMALS:
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        if (x, y) not in occupied:
            animals.append(make_animal(x, y))
            occupied.add((x, y))

    return animals


def empty_world() -> World:
    """Create an initial world using pure builders."""
    obstacles = random_obstacles()
    animals = random_animals(obstacles)
    food: Set[Tuple[int, int]] = set()

    return {
        "animals": animals,
        "food": food,
        "obstacles": obstacles,
    }


# ------------------------------
# World update functions (pure)
# ------------------------------

def spawn_food(world: World) -> World:
    """
    Return a new world where food has been spawned on some empty cells.
    Functional: we don't mutate world in-place.
    """
    animals: List[Animal] = world["animals"]  # type: ignore
    food: Set[Tuple[int, int]] = world["food"]  # type: ignore
    obstacles: Set[Tuple[int, int]] = world["obstacles"]  # type: ignore

    occupied = {
        (a["x"], a["y"]) for a in animals
    } | food | obstacles

    new_food = set(food)

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            pos = (i, j)
            if pos not in occupied and random.random() < FOOD_SPAWN_RATE:
                new_food.add(pos)

    return {
        **world,
        "food": new_food,
    }


def step_world(world: World) -> Tuple[World, Dict[str, int]]:
    """
    Perform one simulation step in a functional way.
    Input: old world
    Output: (new world, stats)
    """
    animals: List[Animal] = world["animals"]  # type: ignore
    food: Set[Tuple[int, int]] = world["food"]  # type: ignore
    obstacles: Set[Tuple[int, int]] = world["obstacles"]  # type: ignore

    stats = {
        "moves": 0,
        "eats": 0,
        "births": 0,
        "deaths": 0,
    }

    new_food = set(food)
    new_animals: List[Animal] = []

    for animal in animals:
        # movement
        moved_animal = move_animal(animal, obstacles)
        if (moved_animal["x"], moved_animal["y"]) != (animal["x"], animal["y"]):
            stats["moves"] += 1

        # eating
        pos = (moved_animal["x"], moved_animal["y"])
        if pos in new_food:
            moved_animal = animal_after_eating(moved_animal)
            new_food.remove(pos)
            stats["eats"] += 1

        # life update
        life_animal = update_life(moved_animal)

        # death check
        if is_dead(life_animal):
            stats["deaths"] += 1
            continue

        # reproduction
        offspring: List[Animal] = []
        if life_animal["energy"] >= REPRODUCTION_ENERGY:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)

            occupied_positions = {
                (a["x"], a["y"]) for a in new_animals
            } | { (life_animal["x"], life_animal["y"]) } | new_food | obstacles

            for dx, dy in directions:
                nx, ny = life_animal["x"] + dx, life_animal["y"] + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if (nx, ny) not in occupied_positions:
                        child = make_animal(nx, ny)
                        # split energy between parent and child (purely via new values)
                        child_energy = life_animal["energy"] // 2
                        child = {**child, "energy": child_energy}
                        life_animal = {
                            **life_animal,
                            "energy": life_animal["energy"] - child_energy,
                        }
                        offspring.append(child)
                        stats["births"] += 1
                        break

        new_animals.append(life_animal)
        new_animals.extend(offspring)

    new_world: World = {
        "animals": new_animals,
        "food": new_food,
        "obstacles": obstacles,  # obstacles never change here
    }

    return new_world, stats


# ------------------------------
# Rendering (side effect only here)
# ------------------------------

def render_world(world: World) -> None:
    animals: List[Animal] = world["animals"]  # type: ignore
    food: Set[Tuple[int, int]] = world["food"]  # type: ignore
    obstacles: Set[Tuple[int, int]] = world["obstacles"]  # type: ignore

    animal_positions = {(a["x"], a["y"]) for a in animals}

    print("Grid (functional version):")
    for i in range(GRID_SIZE):
        row_symbols = []
        for j in range(GRID_SIZE):
            pos = (i, j)
            if pos in animal_positions:
                row_symbols.append("A")
            elif pos in food:
                row_symbols.append("F")
            elif pos in obstacles:
                row_symbols.append("X")
            else:
                row_symbols.append(".")
        print("   ".join(row_symbols))
    print()


# ------------------------------
# Simulation loop (functional style)
# ------------------------------

def run_simulation_functional(steps: int = 10) -> None:
    """
    Functional-style main loop:
    - world is treated as immutable; each step returns a *new* world
    """
    world = empty_world()
    print("Starting functional simulation...\n")

    for step in range(steps):
        print(f"=== Step {step + 1} ===")

        # food spawn creates a new world
        world = spawn_food(world)

        # step_world returns a new world and stats
        world, stats = step_world(world)

        render_world(world)

        animals: List[Animal] = world["animals"]  # type: ignore
        food: Set[Tuple[int, int]] = world["food"]  # type: ignore
        obstacles: Set[Tuple[int, int]] = world["obstacles"]  # type: ignore

        animal_count = len(animals)
        food_count = len(food)
        obstacle_count = len(obstacles)

        if animal_count > 0:
            avg_energy = sum(a["energy"] for a in animals) / animal_count
            avg_age = sum(a["age"] for a in animals) / animal_count
        else:
            avg_energy = 0.0
            avg_age = 0.0

        print(
            f"Animals: {animal_count} | Food: {food_count} | Obstacles: {obstacle_count}"
        )
        print(
            f"Moves: {stats['moves']}, Eats: {stats['eats']}, "
            f"Births: {stats['births']}, Deaths: {stats['deaths']}"
        )
        print(
            f"Average energy: {avg_energy:.2f}, Average age: {avg_age:.2f}"
        )

        if animal_count == 0:
            print("All animals have died.")
            break


if __name__ == "__main__":
    run_simulation_functional()



