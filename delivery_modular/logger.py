import csv
import json
import os
import time
from dataclasses import asdict

from .models import DispatchLog, OrderLog


class CSVLogger:
    def __init__(self, out_dir: str = "runs"):
        os.makedirs(out_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.dir = os.path.join(out_dir, ts)
        os.makedirs(self.dir, exist_ok=True)

        self._w_dispatch = open(os.path.join(self.dir, "dispatch.csv"), "w", newline="")
        self._w_orders = open(os.path.join(self.dir, "orders.csv"), "w", newline="")

        self.dw = csv.DictWriter(self._w_dispatch, fieldnames=[f.name for f in DispatchLog.__dataclass_fields__.values()])
        self.ow = csv.DictWriter(self._w_orders, fieldnames=[f.name for f in OrderLog.__dataclass_fields__.values()])
        self.dw.writeheader()
        self.ow.writeheader()

    def log_dispatch(self, rec: DispatchLog):
        self.dw.writerow(asdict(rec))
        self._w_dispatch.flush()

    def log_order(self, rec: OrderLog):
        self.ow.writerow(asdict(rec))
        self._w_orders.flush()

    def save_config(self, cfg: dict):
        with open(os.path.join(self.dir, "config.json"), "w") as f:
            json.dump(cfg, f, indent=2)

    def close(self):
        for fh in (self._w_dispatch, self._w_orders):
            try:
                fh.flush()
                fh.close()
            except Exception:
                pass
