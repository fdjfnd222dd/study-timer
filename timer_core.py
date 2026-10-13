"""Timer logic with no GUI, so it can be unit-tested.

Uses a monotonic clock deadline instead of counting ticks: if the GUI
loop stalls (or the laptop suspends briefly), the displayed time stays
correct instead of drifting.
"""
import time

IDLE, RUNNING, PAUSED = "idle", "running", "paused"
STUDY, BREAK = "study", "break"


class StudyTimer:
    def __init__(self, study=30 * 60, rest=5 * 60, clock=time.monotonic):
        self.clock = clock
        self.study_len = study
        self.break_len = rest
        self.state = IDLE
        self.phase = STUDY
        self.sessions = 0          # completed study chunks
        self._left = study         # seconds left while idle/paused
        self._deadline = 0.0       # clock value when running ends

    def _phase_len(self):
        return self.study_len if self.phase == STUDY else self.break_len

    @property
    def remaining(self):
        if self.state == RUNNING:
            return max(0.0, self._deadline - self.clock())
        return self._left

    def configure(self, study, rest):
        """Change lengths. Only allowed while idle (Stop first)."""
        if self.state != IDLE:
            raise RuntimeError("stop the timer before changing lengths")
        if study <= 0 or rest <= 0:
            raise ValueError("lengths must be positive")
        self.study_len, self.break_len = study, rest
        self._left = study

    def start(self):
        if self.state == RUNNING:
            return
        self._deadline = self.clock() + self._left
        self.state = RUNNING

    def pause(self):
        if self.state == RUNNING:
            self._left = self.remaining
            self.state = PAUSED

    def stop(self):
        """End the session: back to idle, a fresh study chunk, counter kept."""
        self.state = IDLE
        self.phase = STUDY
        self._left = self.study_len

    def reset(self):
        """Restart the current phase from its full length (keeps run state)."""
        self._left = self._phase_len()
        if self.state == RUNNING:
            self._deadline = self.clock() + self._left

    def tick(self):
        """Advance phases. Returns the phase that just finished, or None."""
        if self.state != RUNNING or self.remaining > 0:
            return None
        done = self.phase
        if done == STUDY:
            self.sessions += 1
        self.phase = BREAK if done == STUDY else STUDY
        self._left = self._phase_len()
        self._deadline = self.clock() + self._left  # breaks chain automatically
        return done
