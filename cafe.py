import matplotlib.pyplot as plt
import argparse
import random
import simpy
from dataclasses import dataclass

@dataclass
class Config:
    lam: float = 2 #arrivals/minute
    drink_time: float = 1 #time to make a drink
    food_time: float = 1 #time to make food
    n_cashier: int = 2
    n_drinkmaker: int = 2
    sim_time: float = 120 #minutes
    register_time: float = 0.5
    
    p_online: float = 0.3 
    
    food_drink_ratio: float = 1.64  # 1:1.64 där 1 är mat och 1.64 är dryck
    p_both: float = 0.32            # andel ordrar med både mat och dryck(kan välja vad som men p_food_only och p_drink_only förändras med p_both)
    p_food_only: float = round((1 - food_drink_ratio * p_both) / (1 + food_drink_ratio), 4) #annars blir det 0.18000000000000005
    p_drink_only: float = round(1 - p_both - p_food_only, 4)


#Next step is probably creating order class

class Order:
    def __init__(self, order_id, arrival_time, has_food, has_drink, p_online):
        self.id = order_id
        self.arrival_time = arrival_time
        self.start_time = None 
        self.done_time = None #When food_done and drink_done both are True
        self.has_food = has_food      # True/False
        self.has_drink = has_drink    # True/False
        self.food_done = not has_food  #Inverted depending on has_food
        self.drink_done = not has_drink #Inverted depending on has_drink
        self.is_online = random.random() <= p_online

class Cafe: 
    def __init__(self,env,cfg):
        self.env = env
        self.cfg = cfg
        self.kassa = simpy.PriorityResource(env, capacity=cfg.n_cashier) #Station for cashiers with priority
        self.kaffe = simpy.PriorityResource(env, capacity=cfg.n_drinkmaker) #Station for drinkmakers
        self.arrived = [] 
        self.finished = [] #for the finished orders

    
    def process_order(self, order):
        self.arrived.append(order)
        print(f"{self.env.now:6.2f}  Order {order.id} kommer in")
        if not order.is_online:
            with self.kassa.request(priority=1) as req:
                yield req
                yield self.env.timeout(self.cfg.register_time)
        
        if order.has_food:
            self.env.process(self.make_food(order))
        if order.has_drink:
            self.env.process(self.make_drink(order))


        

    def make_food(self, order):
        if order.is_online:
            prio = 0
        else:
            prio = 1
        with self.kassa.request(priority=prio) as req:
            yield req
            order.start_time = self.env.now
            print(f"{self.env.now:6.2f}  Order {order.id} mat börjar")
            yield self.env.timeout(random.expovariate(1 / self.cfg.food_time))
        order.food_done = True
        self.check_done(order)

    def make_drink(self, order):
        if order.is_online:
            prio = 0
        else:
            prio = 1
        with self.kaffe.request(priority=prio) as req:
            yield req
            order.start_time = self.env.now
            print(f"{self.env.now:6.2f}  Order {order.id} dricka börjar")
            yield self.env.timeout(random.expovariate(1 / self.cfg.drink_time))
        order.drink_done = True
        self.check_done(order)

    def check_done(self, order):
        if order.food_done and order.drink_done:
            order.done_time = self.env.now
            self.finished.append(order)
            print(f"{self.env.now:6.2f}  Order {order.id} klar!")


def order_generator(env, cafe):
    order_id = 0
    while True:
        yield env.timeout(random.expovariate(cafe.cfg.lam))
        order_id += 1
        u = random.random()
        if 0 <= u <= cafe.cfg.p_food_only:
            has_food, has_drink = True, False
        elif cafe.cfg.p_food_only < u <= (cafe.cfg.p_food_only + cafe.cfg.p_drink_only):
            has_food, has_drink = False, True
        else:
            has_food, has_drink = True, True
        order = Order(order_id, env.now, has_food, has_drink, cafe.cfg.p_online)
        env.process(cafe.process_order(order))


def parse_args():
    p = argparse.ArgumentParser(description="Cafe queue simulation")
    p.add_argument("--lam", type=float, default=Config.lam)
    p.add_argument("--drink_time", type=float, default=Config.drink_time)
    p.add_argument("--food_time", type=float, default=Config.food_time)
    p.add_argument("--n_cashier", type=int, default=Config.n_cashier)
    p.add_argument("--n_drinkmaker", type=int, default=Config.n_drinkmaker)
    p.add_argument("--sim_time", type=float, default=Config.sim_time)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--p_online", type=float, default=0.3)
    return p.parse_args()

def print_stats(name, times):
    if times:
        print(f"{name:>16}: {len(times):4d} ordrar, medeltid {sum(times) / len(times):.2f} min")
    else:
        print(f"{name:>16}: inga klara ordrar")

if __name__ == "__main__":
    args = parse_args()
    random.seed(args.seed)
    cfg = Config(lam=args.lam, drink_time=args.drink_time,
                 food_time=args.food_time, n_cashier=args.n_cashier,
                 n_drinkmaker=args.n_drinkmaker, sim_time=args.sim_time, p_online=args.p_online)
    env = simpy.Environment()
    cafe = Cafe(env, cfg)
    env.process(order_generator(env, cafe))
    env.run(until=cfg.sim_time)
    unfinished = len(cafe.arrived) - len(cafe.finished)
    print(f"\n     Konfiguration:    {cfg}")
    print(f"  Antal klara ordrar:    {len(cafe.finished)}")
    
    print(f"Antal ankomna ordrar:    {len(cafe.arrived)}")
    print(f"   Ej klara vid slut:    {unfinished}")
    print(f"          varav i kö:    {len(cafe.kaffe.queue) + len(cafe.kassa.queue)}")
    print(f"      Kassa upptagen:    {cafe.kassa.count}")
    print(f"   Drickor i process:    {cafe.kaffe.count}")

    n_food = sum(o.has_food for o in cafe.arrived)
    n_drinkmaker = sum(o.has_drink for o in cafe.arrived)

    print("\n")

    print(f"Mat: {n_food}, dryck: {n_drinkmaker}, kvot 1:{n_drinkmaker / n_food:.2f}")

    print("\n")


    online = [o.done_time - o.arrival_time for o in cafe.finished if o.is_online]
    online_drink = [o.done_time - o.arrival_time for o in cafe.finished if o.is_online and o.has_drink and not o.has_food ]
    online_food = [o.done_time - o.arrival_time for o in cafe.finished if o.is_online and o.has_food and not o.has_drink ]

    physical = [o.done_time - o.arrival_time for o in cafe.finished if not o.is_online]
    physical_drink = [o.done_time - o.arrival_time for o in cafe.finished if not o.is_online and o.has_drink and not o.has_food ]
    physical_food = [o.done_time - o.arrival_time for o in cafe.finished if not o.is_online and o.has_food and not o.has_drink ]

    
    print_stats("Online", online)
    print_stats("Online dryck", online_drink)
    print_stats("Online mat", online_food)
    print()
    print_stats("Fysisk", physical)
    print_stats("Fysisk dryck", physical_drink)
    print_stats("Fysisk mat", physical_food)

#////////////////////////////////////////////////////////////////////////////////////////

    data = [online_drink, online_food, physical_drink, physical_food]
    labels = ["Online\ndryck", "Online\nmat", "Fysisk\ndryck", "Fysisk\nmat"]

    plt.boxplot(data, tick_labels=labels)
    plt.ylabel("Tid i caféet (min)")
    plt.title(f"Tid i systemet, ({cfg.n_cashier},{cfg.n_drinkmaker}), λ = {cfg.lam}")
    plt.savefig("tid_per_kundtyp.png", dpi=200)
    plt.show()


