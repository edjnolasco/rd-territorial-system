import time

from .metrics_schema import RequestMetrics


class MetricsCollector:

    def __init__(self, store):
        self.store = store

    def start(self):
        return time.perf_counter()

    def stop(self, start_time):
        return (time.perf_counter() - start_time) * 1000

    def record(self, event: RequestMetrics):
        self.store.save(event)