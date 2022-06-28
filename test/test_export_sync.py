import unittest
import datetime
import os
import sys

p = os.path.abspath('.')
sys.path.insert(1, p)

import bear_export_sync

class TestStringMethods(unittest.TestCase):
    test_string = ""

    def test_date_conv(self):
        unix_timestamp = datetime.datetime.now().timestamp()
        #print(now)              #2022-06-16 13:32:21.202822
        #print(unix_timestamp)   #1655354188.590179
        convertedDate = bear_export_sync.date_conv(
            unix_timestamp)  # 2022-06-16
        targetedFormatDate = datetime.date.today()  # 2022-06-16
        self.assertEqual(str(convertedDate), str(targetedFormatDate))

    def test_bold_conv(self):
        testItem = [
            {'input': "*Bold*", 'expected': "**Bold**"},
            {'input': "* Not bold*", 'expected': "* Not bold*"},
            {'input': "*Not bold *", 'expected': "*Not bold *"},
            {'input': "*Not Bold \n After CR*",
                'expected': "*Not Bold \n After CR*"},
            {'input': "*Bold*\n After", 'expected': "**Bold**\n After"}, ]

        for item in testItem:
            item['output'] = bear_export_sync.bold_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_separator_conv(self):
        seq = 1
        testItem = [
            {'input': "---",'expected': "\n---"},
            {'input': "- --", 'expected': "- --"},
            {'input': "hi---world", 'expected': "hi---world"},
            {'input': "hello\n---\nhello", 'expected': "hello\n\n---\nhello"}]

        for item in testItem:
            item['output'] = bear_export_sync.separator_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_italic_conv(self):
        testItem = [
            {'input': "/Italic/", 'expected': "*Italic*"},
            {'input': "/ Not Italic/", 'expected': "/ Not Italic/"},
            {'input': "/Not Italic /", 'expected': "/Not Italic /"},
            {'input': "/Not Italic \n After CR/",
                'expected': "/Not Italic \n After CR/"},
            {'input': "/Italic/\n After", 'expected': "*Italic*\n After"}, ]

        for item in testItem:
            item['output'] = bear_export_sync.separator_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

#TODO: Add new test here

if __name__ == '__main__':
    unittest.main()
