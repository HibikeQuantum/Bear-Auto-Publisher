import unittest
import datetime
import os, sys

p = os.path.abspath('.')
sys.path.insert(1, p)

import bear_export_sync

class TestStringMethods(unittest.TestCase):
    test_string = ""

    def test_date_conv(self):
        unix_timestamp = datetime.datetime.now().timestamp()
        #print(now)                                                  #2022-06-16 13:32:21.202822
        #print(unix_timestamp)                                       #1655354188.590179
        convertedDate = bear_export_sync.date_conv(unix_timestamp)  #2022-06-16
        targetedFormatDate = datetime.date.today()                  #2022-06-16
        self.assertEqual(str(convertedDate), str(targetedFormatDate))

if __name__ == '__main__':
    unittest.main()