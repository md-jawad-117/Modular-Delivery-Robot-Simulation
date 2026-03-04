from delivery_modular.sim_config import SimulationConfig
from delivery_modular.simulation import DeliverySimulation


def main():
    cfg = SimulationConfig()
    sim = DeliverySimulation(cfg)
    sim.run()


if __name__ == "__main__":
    main()
