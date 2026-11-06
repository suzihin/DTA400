import argparse
import random
import simpy
from dataclasses import dataclass

@dataclass
class Config:
    lam: float = 5 #arrivals/minute
    drink_time: float = 1 #time to make a drink
    food_time: float = 1 #time to make food
    n_cashier: int = 1
    n_drink: int = 1
    sim_time: float = 120 #minutes
    food_drink_ratio: float = 1.64  # 1:1.64 där 1 är mat och 1.64 är dryck
    p_both: float = 0.32            # andel ordrar med både mat och dryck(kan välja vad som men p_food_only och p_drink_only förändras med p_both)
    p_food_only: float = (1 - food_drink_ratio * p_both) / (1 + food_drink_ratio)
    p_drink_only: float = 1 - p_both - p_food_only


#Next step is probably creating order class

class Order:
    def __init__(self, order_id, arrival_time, has_food, has_drink):
        self.id = order_id
        self.arrival_time = arrival_time
        self.has_food = has_food      # True/False
        self.has_drink = has_drink    # True/False
        self.start_time = None
        self.done_time = None

class Cafe: 
    def __init__(self,env,cfg):
        self.env = env
        self.cfg = cfg
        self.kassa = simpy.Resource(env, capacity=cfg.n_cashier)
        self.kaffe = simpy.Resource(env, capacity=cfg.n_drink)
        self.finished = [] #for the finished orders
        self.arrived = [] 

    
    def process_order(self, order):
        self.arrived.append(order)
        print(f"{self.env.now:6.2f}  Order {order.id} kommer in")

        with self.kaffe.request() as req:
            yield req
            order.start_time = self.env.now
            print(f"{self.env.now:6.2f}  Order {order.id} börjar")
            yield self.env.timeout(random.expovariate(1 / self.cfg.drink_time))

        order.done_time = self.env.now
        self.finished.append(order)
        print(f"{self.env.now:6.2f}  Order {order.id} klar")

def order_generator(env, cafe):
    order_id = 0
    while True:
        yield env.timeout(random.expovariate(cafe.cfg.lam))
        order_id += 1
        order = Order(order_id, env.now)
        env.process(cafe.process_order(order))

if __name__ == "__main__":
    random.seed(42)
    cfg = Config()
    env = simpy.Environment()
    cafe = Cafe(env, cfg)
    env.process(order_generator(env, cafe))
    env.run(until=cfg.sim_time)
    unfinished = len(cafe.arrived) - len(cafe.finished)
    print(f"\nKonfiguration: {cfg}")
    print(f"Antal klara ordrar: {len(cafe.finished)}")
    
    print(f"Antal ankomna ordrar: {len(cafe.arrived)}")
    print(f"Ej klara vid slut:   {unfinished}")
    print(f"  varav i kö:        {len(cafe.kaffe.queue)}")
    print(f"  varav serveras:    {cafe.kaffe.count}")