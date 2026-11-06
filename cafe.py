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
        u = random.random()
        if u < cafe.cfg.p_food_only:
            has_food, has_drink = True, False
        elif u < cafe.cfg.p_food_only + cafe.cfg.p_drink_only:
            has_food, has_drink = False, True
        else:
            has_food, has_drink = True, True
        order = Order(order_id, env.now, has_food, has_drink)
        env.process(cafe.process_order(order))


def parse_args():
    p = argparse.ArgumentParser(description="Cafe queue simulation")
    p.add_argument("--lam", type=float, default=Config.lam)
    p.add_argument("--drink_time", type=float, default=Config.drink_time)
    p.add_argument("--food_time", type=float, default=Config.food_time)
    p.add_argument("--n_cashier", type=int, default=Config.n_cashier)
    p.add_argument("--n_drink", type=int, default=Config.n_drink)
    p.add_argument("--sim_time", type=float, default=Config.sim_time)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    random.seed(args.seed)
    cfg = Config(lam=args.lam, drink_time=args.drink_time,
                 food_time=args.food_time, n_cashier=args.n_cashier,
                 n_drink=args.n_drink, sim_time=args.sim_time)
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

    n_food = sum(o.has_food for o in cafe.arrived)
    n_drink = sum(o.has_drink for o in cafe.arrived)
    print(f"Mat: {n_food}, dryck: {n_drink}, kvot 1:{n_drink / n_food:.2f}")