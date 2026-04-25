import json
import logging

logger = logging.getLogger("rd_metrics")


class MetricsStore:

    def save(self, event):
        logger.info(json.dumps(event.__dict__, ensure_ascii=False))