import queue
from typing import Any
from .interfaces import IQueue

class MemoryQueue(IQueue):
    def __init__(self, maxsize: int = 100):
        # We can have separate internal queues based on topics
        self.queues = {
            "audio": queue.Queue(maxsize=maxsize),
            "control": queue.Queue(maxsize=maxsize)
        }

    def push(self, topic: str, message: Any) -> None:
        if topic not in self.queues:
            self.queues[topic] = queue.Queue()
            
        try:
            # Non-blocking put, discard old if full or just block?
            # For real-time SDR, if audio queue is full, we should probably discard oldest
            # to avoid processing stale audio.
            if self.queues[topic].full():
                try:
                    self.queues[topic].get_nowait() # pop oldest
                except queue.Empty:
                    pass
            self.queues[topic].put_nowait(message)
        except queue.Full:
            pass # Shouldn't happen due to above, but just in case

    def pop(self, topic: str) -> Any:
        if topic not in self.queues:
            return None
            
        try:
            # Block for a short time to avoid busy looping
            return self.queues[topic].get(timeout=0.1)
        except queue.Empty:
            return None
