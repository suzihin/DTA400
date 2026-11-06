import argparse
import random
import simpy
from dataclasses import dataclass

@dataclass
class Config:
    lam: float = 1 / 2 #arrivals/minute
    drink_time: float = 1 #time to make a drink
    food_time: float = 1 #time to make food
    n_cashier: int = 1
    n_drink: int = 1
    sim_time: float = 120 #minutes  
