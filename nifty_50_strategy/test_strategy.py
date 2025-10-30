
import unittest
from strategy import MeanReversionStrategy

class TestStrategy(unittest.TestCase):
    def test_strategy_instantiation(self):
        strategy = MeanReversionStrategy()
        self.assertIsInstance(strategy, MeanReversionStrategy)

if __name__ == '__main__':
    unittest.main()
