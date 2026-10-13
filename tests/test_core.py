import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from timer_core import StudyTimer, IDLE, RUNNING, PAUSED, STUDY, BREAK


class Fake:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.c = Fake()
        self.t = StudyTimer(60, 10, clock=self.c)

    def test_idle_shows_full_length(self):
        self.assertEqual(self.t.remaining, 60)
        self.assertEqual(self.t.state, IDLE)

    def test_counts_down(self):
        self.t.start()
        self.c.t += 25
        self.assertEqual(self.t.remaining, 35)

    def test_pause_freezes_and_resume_continues(self):
        self.t.start()
        self.c.t += 20
        self.t.pause()
        self.c.t += 500
        self.assertEqual(self.t.remaining, 40)
        self.assertEqual(self.t.state, PAUSED)
        self.t.start()
        self.c.t += 10
        self.assertEqual(self.t.remaining, 30)

    def test_stop_returns_to_idle_keeps_sessions(self):
        self.t.start()
        self.c.t += 60
        self.t.tick()
        self.t.stop()
        self.assertEqual((self.t.state, self.t.phase, self.t.remaining), (IDLE, STUDY, 60))
        self.assertEqual(self.t.sessions, 1)

    def test_reset_while_running_restarts_phase(self):
        self.t.start()
        self.c.t += 40
        self.t.reset()
        self.assertEqual(self.t.remaining, 60)
        self.assertEqual(self.t.state, RUNNING)

    def test_reset_while_paused_stays_paused(self):
        self.t.start()
        self.c.t += 40
        self.t.pause()
        self.t.reset()
        self.assertEqual((self.t.state, self.t.remaining), (PAUSED, 60))

    def test_study_to_break_to_study_chain(self):
        self.t.start()
        self.c.t += 60
        self.assertEqual(self.t.tick(), STUDY)
        self.assertEqual((self.t.phase, self.t.remaining, self.t.sessions), (BREAK, 10, 1))
        self.assertEqual(self.t.state, RUNNING)
        self.c.t += 10
        self.assertEqual(self.t.tick(), BREAK)
        self.assertEqual((self.t.phase, self.t.remaining, self.t.sessions), (STUDY, 60, 1))

    def test_tick_noop_when_not_finished_or_not_running(self):
        self.assertIsNone(self.t.tick())
        self.t.start()
        self.c.t += 5
        self.assertIsNone(self.t.tick())

    def test_configure_only_when_idle(self):
        self.t.configure(120, 20)
        self.assertEqual(self.t.remaining, 120)
        self.t.start()
        with self.assertRaises(RuntimeError):
            self.t.configure(30, 5)
        self.t.stop()
        with self.assertRaises(ValueError):
            self.t.configure(0, 5)


if __name__ == "__main__":
    unittest.main()
