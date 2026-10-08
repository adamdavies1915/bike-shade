import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import canopy_stats,length_m

class CanopyStatsTests(unittest.TestCase):
    def test_missing_data_is_not_zero_canopy(self):
        self.assertIsNone(canopy_stats(0,0,100)['canopy_pct'])
        self.assertIsNone(canopy_stats(89,89,100)['canopy_pct'])

    def test_valid_denominator_excludes_unknown(self):
        self.assertEqual(canopy_stats(45,90,100),{'canopy_pct':50.0,'valid_coverage_pct':90.0})

    def test_real_zero_is_preserved(self):
        self.assertEqual(canopy_stats(0,100,100)['canopy_pct'],0)

    def test_invalid_counts_fail(self):
        with self.assertRaises(ValueError): canopy_stats(101,100,100)

    def test_geographic_length(self):
        self.assertAlmostEqual(length_m([[-90,30],[-90,30.001]]),111.195,places=2)

if __name__=='__main__': unittest.main()
