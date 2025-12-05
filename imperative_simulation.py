import random
from typing import List, Tuple, Optional, Dict, Union

GRID_SIZE: Tuple[int, int] = (10, 10)
ROWS, COLS = GRID_SIZE

class Animal:
    """Represents a creature in the simulation with mutable state."""
    def __init__(self, animal_id: int, r: int, c: int, type: str, energy: int = 10, age: int = 0):
        self.id = animal_id
        self.r = r  # Row 
        self.c = c  # Col 
        self.type = type
        self.energy = energy 
        self.age = age       
        self.moved = False   

    def __repr__(self):
        return f"{self.type[:1]}:({self.r},{self.c},E={self.energy})"

class SimulationStats:
    """track statistics across all steps."""
    def __init__(self):
        self.total_deaths = 0
        self.total_births = 0
        self.food_eaten = 0
        self.steps = 0

# GridContent: Animal object, 'F' (Food), '#' (Obstacle), or None (Empty)
GridContent = Union[Animal, str, None]
Grid = List[List[GridContent]]

SIM_STATS = SimulationStats()

def initialize_grid() -> Grid:
    """Initializes the mutable grid state with animals, food, and obstacles."""
    grid: Grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    
    # Place initial animals
    rabbit1 = Animal(10, 1, 1, 'Rabbit')
    rabbit2 = Animal(20, 3, 4, 'Rabbit')
    rabbit3 = Animal(30, 8, 8, 'Rabbit')
    
    # Direct index assignment
    grid[1][1] = rabbit1
    grid[3][4] = rabbit2
    grid[8][8] = rabbit3
    
    # Place Obstacles ('#') and Food ('F') randomly
    for _ in range(int(ROWS * COLS * 0.1)): 
        r, c = random.randint(0, ROWS - 1), random.randint(0, COLS - 1)
        if grid[r][c] is None:
            grid[r][c] = '#'

    for _ in range(int(ROWS * COLS * 0.15)): 
        r, c = random.randint(0, ROWS - 1), random.randint(0, COLS - 1)
        if grid[r][c] is None:
            grid[r][c] = 'F' 
            
    return grid

def move_safe(r: int, c: int, dr: int, dc: int) -> Tuple[int, int]:
    #Calculates the new position
    new_r = (r + dr) % ROWS
    new_c = (c + dc) % COLS
    return new_r, new_c

def get_random_direction() -> Tuple[int, int]:
    return random.choice([(0, 1), (0, -1), (1, 0), (-1, 0), (0, 0)])

def process_turn_imperative(grid: Grid, animal: Animal, step_stats: Dict[str, int]):

    if animal.moved: 
        return

    # 1. Check for Death
    if animal.energy <= 0:
        grid[animal.r][animal.c] = None 
        SIM_STATS.total_deaths += 1 
        step_stats['deaths_starvation'] += 1
        return

    # 2. Update energy and age
    animal.energy -= 3 
    animal.age += 1 

    # 3. Calculate Move
    dr, dc = get_random_direction()
    new_r, new_c = move_safe(animal.r, animal.c, dr, dc)
    
    target_cell = grid[new_r][new_c]
    
    # Handle Obstacle
    if target_cell == '#':
        animal.energy -= 1 
        step_stats['obstacle_encounters'] += 1
        return

    # Handle Conflict/Interaction with another Animal
    if isinstance(target_cell, Animal) and target_cell.id != animal.id:
        animal.energy -= 2  
        step_stats['conflicts'] += 1
        return
        
    # Handle Food
    elif target_cell == 'F':
        animal.energy += 5 
        grid[new_r][new_c] = None 
        SIM_STATS.food_eaten += 1 
        step_stats['food_eaten'] += 1
        
    # Handle Move to Empty Cell
    if grid[new_r][new_c] is None: 
        grid[animal.r][animal.c] = None 
        animal.r, animal.c = new_r, new_c
        grid[new_r][new_c] = animal      
        animal.moved = True              

    # 4. Reproduction 
    if animal.energy > 5 and animal.age > 2 and random.random() < 0.2:
        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for ndr, ndc in neighbors:
            baby_r, baby_c = move_safe(animal.r, animal.c, ndr, ndc)
            if grid[baby_r][baby_c] is None: 
                new_id = random.randint(1000, 9999)
                baby = Animal(new_id, baby_r, baby_c, animal.type, energy=3, age=0)
                grid[baby_r][baby_c] = baby 
                animal.energy //= 2 
                
                SIM_STATS.total_births += 1 
                step_stats['births'] += 1
                break
        
def sim_step_imperative(grid: Grid) -> Dict[str, int]:
    """Performs one step of the simulation using nested loops and mutation."""
    
    step_stats = {
        'deaths_starvation': 0, 'births': 0, 'food_eaten': 0,
        'obstacle_encounters': 0, 'conflicts': 0
    }
    
    # 1. Collect all animals and reset 'moved' state
    animals_to_process: List[Animal] = []
    for r in range(ROWS): 
        for c in range(COLS): 
            animal = grid[r][c]
            if isinstance(animal, Animal):
                animals_to_process.append(animal)
                animal.moved = False 
    
    # 2. Process turns
    for animal in animals_to_process: 
        process_turn_imperative(grid, animal, step_stats)
        
    SIM_STATS.steps += 1 
    return step_stats

def run_simulation_imperative(grid: Grid, steps: int):
    """Main entry point for the imperative simulation using a procedural while loop."""
    print("--- IMPERATIVE SIMULATION (Procedural Programming) ---")
    
    i = 0
    while i < steps:
        print(f"\n======== STEP {i + 1} ========")
        
        step_stats = sim_step_imperative(grid)
        i += 1
        
        display_grid_imperative(grid)
        
        current_animals = sum(1 for r in range(ROWS) for c in range(COLS) if isinstance(grid[r][c], Animal))
        print(f"Animals: {current_animals} (Born: {step_stats['births']}, Died: {step_stats['deaths_starvation']})")
        print(f"Interactions: Food Eaten: {step_stats['food_eaten']}, Obstacles Hit: {step_stats['obstacle_encounters']}")
        
        if current_animals == 0:
            print("\nECOSYSTEM COLLAPSED: All animals are gone.")
            break

    print("\n--- SIMULATION COMPLETE (Final Mutable State) ---")
    print(f"Total Steps: {SIM_STATS.steps}")
    print(f"Total Deaths: {SIM_STATS.total_deaths}")
    print(f"Total Births: {SIM_STATS.total_births}")
    print(f"Total Food Eaten: {SIM_STATS.food_eaten}")


def display_grid_imperative(grid: Grid):
    # R=Rabbit, F=Food, #=Obstacle, .=Empty
    print("-" * (COLS * 3 + 1))
    for r in range(ROWS):
        row_str = "|"
        for c in range(COLS):
            content = grid[r][c]
            
            display_char = '.'
            if isinstance(content, Animal):
                display_char = content.type[0]
            elif content == 'F':
                display_char = 'F'
            elif content == '#':
                display_char = '#'
                
            row_str += f" {display_char} |"
        print(row_str)
        print("-" * (COLS * 3 + 1))


if __name__ == '__main__':
    grid_state = initialize_grid()
    run_simulation_imperative(grid_state, 10)