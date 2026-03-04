from .sim_config import SimulationConfig
from .simulation import DeliverySimulation


def main():
    cfg = SimulationConfig()
    sim = DeliverySimulation(cfg)
    sim.run()


if __name__ == "__main__":
    main()
