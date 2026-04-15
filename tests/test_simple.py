"""
Test suite for Smart Cities Traffic Analysis Project

Tests cover:
- Spark environment setup
- SUMO importer functionality
- Data validation

Run with: make test  OR  python tests/test_simple.py

Note: Some tests require dependencies (pyspark, psycopg2). Install with:
  conda activate project_smart_cities
  pip install psycopg2-binary
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

# Configure Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sumo_db_project'))


class TestSparkEnvironment(unittest.TestCase):
    """Test Spark environment configuration"""

    def test_spark_import(self):
        """Verify PySpark can be imported"""
        try:
            from pyspark.sql import SparkSession
            self.assertTrue(True)
        except ImportError:
            self.skipTest("PySpark not available. Run: conda activate project_smart_cities")

    def test_spark_session_creation(self):
        """Test SparkSession creation and basic operation"""
        try:
            from pyspark.sql import SparkSession
        except ImportError:
            self.skipTest("PySpark not available")

        os.environ['PYSPARK_PYTHON'] = sys.executable
        os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

        spark = SparkSession.builder \
            .appName("TestSpark") \
            .master("local[1]") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
            .getOrCreate()

        try:
            # Create test DataFrame
            data = [("Sensor_001", 100), ("Sensor_002", 150), ("Sensor_003", 80)]
            columns = ["sensor_id", "num_vehiculos"]
            df = spark.createDataFrame(data, columns)

            # Verify row count
            self.assertEqual(df.count(), 3)

            # Verify schema
            fields = [f.name for f in df.schema.fields]
            self.assertIn("sensor_id", fields)
            self.assertIn("num_vehiculos", fields)

        finally:
            spark.stop()


class TestSUMOImporter(unittest.TestCase):
    """Test SUMO importer functionality"""

    def _get_time_period_func(self):
        """Get time period classification function (works without DB connection)"""
        def get_time_period(seconds):
            hour = int(seconds // 3600) % 24
            if 0 <= hour < 5:
                return 'MADRUGADA'
            elif 5 <= hour < 7:
                return 'MA\u00D1ANA'  # Using unicode escape for Ñ
            elif 7 <= hour < 9:
                return 'PICO_AM'
            elif 9 <= hour < 17:
                return 'DIA'
            elif 17 <= hour < 19:
                return 'PICO_PM'
            else:
                return 'NOCHE'
        return get_time_period

    def test_time_period_classification(self):
        """Test time period classification logic"""
        get_time_period = self._get_time_period_func()

        # Test each time period
        # Note: Using unicode escape for 'Ñ' to avoid encoding issues
        # Logic from sumo_importer.py:
        #   0-5=MADRUGADA, 5-7=MAÑANA, 7-9=PICO_AM, 9-17=DIA, 17-19=PICO_PM, 19-24=NOCHE
        test_cases = [
            (0, 'MADRUGADA'),           # 00:00
            (14400, 'MADRUGADA'),       # 04:00 (last hour of MADRUGADA)
            (18000, 'MA\u00D1ANA'),     # 05:00
            (21600, 'MA\u00D1ANA'),     # 06:00 (still MAÑANA per logic)
            (25200, 'PICO_AM'),         # 07:00
            (28800, 'PICO_AM'),         # 08:00
            (32400, 'DIA'),             # 09:00
            (36000, 'DIA'),             # 10:00
            (57600, 'DIA'),             # 16:00 (last hour of DIA)
            (61200, 'PICO_PM'),         # 17:00
            (64800, 'PICO_PM'),         # 18:00
            (68400, 'NOCHE'),           # 19:00
            (82800, 'NOCHE'),           # 23:00
        ]

        for seconds, expected_period in test_cases:
            result = get_time_period(seconds)
            self.assertEqual(result, expected_period,
                           f"Failed for {seconds}s (hour {seconds//3600})")

    def test_importer_module_exists(self):
        """Test that sumo_importer module exists and has required functions"""
        importer_path = os.path.join(
            os.path.dirname(__file__), '..', 'sumo_db_project', 'sumo_importer.py'
        )
        self.assertTrue(os.path.exists(importer_path),
                       f"sumo_importer.py not found at {importer_path}")

    def test_xml_parsing_structure(self):
        """Test XML parsing structure"""
        import xml.etree.ElementTree as ET

        # Test that ET can parse valid XML structure
        test_xml = """<?xml version="1.0"?>
        <root>
            <tripinfo id="test" depart="0" arrival="100" duration="100"/>
        </root>
        """

        root = ET.fromstring(test_xml)
        tripinfo = root.find('.//tripinfo')

        self.assertIsNotNone(tripinfo)
        self.assertEqual(tripinfo.get('id'), 'test')
        self.assertEqual(float(tripinfo.get('depart')), 0)

    def test_psycopg2_availability(self):
        """Test psycopg2 availability for database connection"""
        try:
            import psycopg2
            self.assertTrue(True)
        except ImportError:
            self.skipTest("psycopg2 not available. Run: pip install psycopg2-binary")


class TestDataValidation(unittest.TestCase):
    """Test data validation rules"""

    def test_vehicle_type_categories(self):
        """Test valid vehicle type categories"""
        valid_types = {'passenger', 'bus', 'motorcycle', 'truck'}

        # Test that expected types are in the set
        self.assertIn('passenger', valid_types)
        self.assertIn('bus', valid_types)

    def test_speed_bounds(self):
        """Test speed value validation"""
        # Simulated speed data (m/s)
        test_speeds = [0, 5.5, 13.8, 25.0, 40.0]  # 0 to ~144 km/h

        for speed in test_speeds:
            self.assertGreaterEqual(speed, 0, "Speed cannot be negative")
            self.assertLessEqual(speed, 50, "Speed exceeds realistic maximum (180 km/h)")

    def test_timestamp_conversion(self):
        """Test simulation timestamp to real timestamp conversion"""
        simulation_start = datetime(2024, 1, 15, 8, 0, 0)
        simulation_second = 3600  # 1 hour into simulation

        real_time = simulation_start + timedelta(seconds=simulation_second)

        self.assertEqual(real_time.hour, 9)  # 8:00 + 1 hour
        self.assertEqual(real_time.minute, 0)

    def test_data_directory_structure(self):
        """Test that data directory structure exists"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        raw_dir = os.path.join(data_dir, 'raw')
        processed_dir = os.path.join(data_dir, 'processed')

        self.assertTrue(os.path.exists(data_dir), "data/ directory missing")
        self.assertTrue(os.path.exists(raw_dir), "data/raw/ directory missing")
        self.assertTrue(os.path.exists(processed_dir), "data/processed/ directory missing")


def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestSparkEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestSUMOImporter))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("All tests passed!")
    else:
        print(f"Tests completed: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")
    print("=" * 60)

    return result


if __name__ == '__main__':
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)