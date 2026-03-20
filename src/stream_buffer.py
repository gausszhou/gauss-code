import time
from typing import Generator, Optional


class StreamBuffer:
    def __init__(self, mode: str = "char", buffer_size: int = 20, buffer_interval: float = 0.05):
        self.mode = mode
        self.buffer_size = buffer_size
        self.buffer_interval = buffer_interval
        self._buffer = ""
        self._last_yield_time = 0.0
        self._stopped = False

    def stop(self):
        self._stopped = True

    def reset(self):
        self._buffer = ""
        self._last_yield_time = 0.0
        self._stopped = False

    def process(self, content: str) -> Generator[str, None, None]:
        if self._stopped:
            return

        if self.mode == "char":
            for char in content:
                if self._stopped:
                    return
                yield char
        elif self.mode == "buffer":
            self._buffer += content
            current_time = time.time()
            
            if len(self._buffer) >= self.buffer_size:
                elapsed = current_time - self._last_yield_time
                if elapsed >= self.buffer_interval:
                    if self._stopped:
                        return
                    yield self._buffer
                    self._buffer = ""
                    self._last_yield_time = current_time

    def flush(self) -> Generator[str, None, None]:
        if self._buffer:
            if not self._stopped:
                yield self._buffer
            self._buffer = ""
