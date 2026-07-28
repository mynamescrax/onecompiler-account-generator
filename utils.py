import time
import logging
import threading

logger = logging.getLogger(__name__)


class TimingTracker:

    def __init__(self):
        self.timings = {}
        self.current = {}
        self._lock = threading.Lock()

    def start(self, name):
        with self._lock:
            self.current[name] = time.time()

    def end(self, name):
        with self._lock:
            if name in self.current:
                elapsed = time.time() - self.current[name]
                self.timings[name] = elapsed
                del self.current[name]
                return elapsed
            return None

    def summary(self):
        with self._lock:
            if not self.timings:
                return "No timings recorded"

            lines = ["\nTiming Summary:"]
            total = 0
            for name, elapsed in self.timings.items():
                lines.append(f"  {name}: {elapsed*1000:.1f}ms")
                total += elapsed
            lines.append(f"  ")
            lines.append(f"  TOTAL: {total*1000:.1f}ms")
            return "\n".join(lines)


timing = TimingTracker()
