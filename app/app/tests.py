from django.test import SimpleTestCase
from . import calc


class TestCalc(SimpleTestCase):
    """Test the calc module."""
    def test_add_numbers(self):
        """Test the add function."""
        r = calc.add(8, 5)
        
        self.assertEqual(r, 13)
        
    def test_subtract_numbers(self):
        """Test the subtract function."""
        r = calc.subtract(10, 15)
        
        self.assertEqual(r, 5)