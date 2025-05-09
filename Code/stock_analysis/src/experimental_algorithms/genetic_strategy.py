import numpy as np
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import random
from ..strategies.base_strategy import BaseStrategy

@dataclass
class GeneticOperator:
    """Represents a genetic operator that can be used in strategy evolution"""
    name: str
    function: Callable
    parameters: Dict[str, Any]

class GeneticStrategy(BaseStrategy):
    """A strategy that evolves using genetic algorithms"""
    
    def __init__(
        self,
        symbol: str,
        population_size: int = 100,
        generations: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elite_size: int = 5
    ):
        super().__init__(symbol)
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.operators = []
        self.best_individual = None
        self.population = []
        self.fitness_history = []
    
    def add_operator(self, operator: GeneticOperator) -> None:
        """Add a genetic operator to the strategy"""
        self.operators.append(operator)
    
    def initialize_population(self) -> None:
        """Initialize the population with random individuals"""
        raise NotImplementedError("Subclasses must implement initialize_population")
    
    def evaluate_fitness(self, individual: Any) -> float:
        """Evaluate the fitness of an individual"""
        raise NotImplementedError("Subclasses must implement evaluate_fitness")
    
    def select_parents(self) -> List[Any]:
        """Select parents for reproduction using tournament selection"""
        tournament_size = 3
        parents = []
        
        for _ in range(2):
            tournament = random.sample(self.population, tournament_size)
            winner = max(tournament, key=lambda x: self.evaluate_fitness(x))
            parents.append(winner)
        
        return parents
    
    def crossover(self, parent1: Any, parent2: Any) -> Any:
        """Perform crossover between two parents"""
        raise NotImplementedError("Subclasses must implement crossover")
    
    def mutate(self, individual: Any) -> Any:
        """Mutate an individual"""
        raise NotImplementedError("Subclasses must implement mutate")
    
    def evolve(self) -> None:
        """Run the genetic algorithm"""
        self.initialize_population()
        
        for generation in range(self.generations):
            # Evaluate fitness for all individuals
            fitness_scores = [self.evaluate_fitness(ind) for ind in self.population]
            
            # Store best individual
            best_idx = np.argmax(fitness_scores)
            if self.best_individual is None or fitness_scores[best_idx] > self.evaluate_fitness(self.best_individual):
                self.best_individual = self.population[best_idx]
            
            # Store average fitness
            self.fitness_history.append(np.mean(fitness_scores))
            
            # Create new population
            new_population = []
            
            # Elitism: keep best individuals
            sorted_indices = np.argsort(fitness_scores)[::-1]
            for i in range(self.elite_size):
                new_population.append(self.population[sorted_indices[i]])
            
            # Create rest of new population
            while len(new_population) < self.population_size:
                if random.random() < self.crossover_rate:
                    # Crossover
                    parents = self.select_parents()
                    child = self.crossover(parents[0], parents[1])
                else:
                    # Clone
                    child = random.choice(self.population)
                
                # Mutation
                if random.random() < self.mutation_rate:
                    child = self.mutate(child)
                
                new_population.append(child)
            
            self.population = new_population
    
    def plot_fitness_history(self, save_path: Optional[str] = None) -> None:
        """Plot the evolution of fitness over generations"""
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(self.fitness_history)), self.fitness_history)
        plt.title('Fitness Evolution')
        plt.xlabel('Generation')
        plt.ylabel('Average Fitness')
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            plt.close()
        else:
            plt.show()
    
    def run_strategy(self, **kwargs) -> None:
        """Run the evolved strategy"""
        if self.best_individual is None:
            self.evolve()
        
        # Implementation depends on how the strategy is encoded in individuals
        raise NotImplementedError("Subclasses must implement run_strategy")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the current parameters of the strategy"""
        return {
            'population_size': self.population_size,
            'generations': self.generations,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'elite_size': self.elite_size
        }
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set new parameters for the strategy"""
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)

class MyGeneticStrategy(GeneticStrategy):
    def initialize_population(self):
        # Initialize population with random trading rules
        pass
    
    def evaluate_fitness(self, individual):
        # Evaluate trading rules performance
        pass
    
    def crossover(self, parent1, parent2):
        # Combine trading rules
        pass
    
    def mutate(self, individual):
        # Modify trading rules
        pass 