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

#Next step is probably creating order class

class Order:
    def __init__(self, order_id, arrival_time):
        self.id = order_id
        self.arrival_time = arrival_time
        self.start_time = None
        self.done_time = None

class Cafe: 
    def __init__(self,env,cfg):
        self.env = env
        self.cfg = cfg
        self.kassa = simpy.Resource(env, capacity=cfg.n_cashier)
        self.kaffe = simpy.Resource(env, capacity=cfg.n_drink)
        self.finished = [] #for the finished orders
    
    def process_order(self, order):
        print(f"{self.env.now:6.2f}  Order {order.id} kommer in")

        with self.kaffe.request() as req:
            yield req
            order.start_time = self.env.now
            print(f"{self.env.now:6.2f}  Order {order.id} börjar")
            yield self.env.timeout(random.expovariate(1 / self.cfg.drink_time))

        order.done_time = self.env.now
        self.finished.append(order)
        print(f"{self.env.now:6.2f}  Order {order.id} klar")