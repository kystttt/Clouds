import unittest
import os
from source.error_decorator import retry_on_error


class DummyClass(unittest.TestCase):
    def __init__(self, interactive=True):
        self.interactive = interactive
        self.call_count = 0

    @retry_on_error(max_retries=3, delay=0.1)
    def might_fail(self):
        self.call_count += 1
        raise ValueError("Test error")

    @retry_on_error(max_retries=3, delay=0.1)
    def always_passes(self):
        return "success"

    @retry_on_error(max_retries=3, delay=0.1)
    def succeeds_after_two_tries(self):
        self.call_count += 1
        if self.call_count < 3:
            raise ValueError("Retry needed")
        return "ok"


class TestRetryOnError(unittest.TestCase):

    def setUp(self):
        self.dummy = DummyClass(interactive=True)

    def test_success_without_errors(self):
        self.assertEqual(self.dummy.always_passes(), "success")

    def test_unit_test_mode_raises(self):
        os.environ["UNIT_TEST_MODE"] = "1"
        with self.assertRaises(ValueError):
            self.dummy.might_fail()
        del os.environ["UNIT_TEST_MODE"]

    def test_wrapper_preserves_function_name(self):
        self.assertEqual(self.dummy.might_fail.__name__, "might_fail")


if __name__ == "__main__":
    unittest.main()
