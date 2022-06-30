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
            item['output'] = bear_export_sync.italic_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_underline_conv(self):
        testItem = [
            {'input': "_Underline_", 'expected': "***Underline***"},
            {'input': "_ Not Underline_", 'expected': "_ Not Underline_"},
            {'input': "_Not Underline _", 'expected': "_Not Underline _"},
            {'input': "_Not Underline \n After CR_",
                'expected': "_Not Underline \n After CR_"},
            {'input': "_Underline_\n After", 'expected': "***Underline***\n After"}, ]

        for item in testItem:
            item['output'] = bear_export_sync.underline_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_strike_conv(self):
        testItem = [
            {'input': "-Strike-", 'expected': "~~Strike~~"},
            {'input': "- Not Strike-", 'expected': "- Not Strike-"},
            {'input': "-Not Strike -", 'expected': "-Not Strike -"},
            {'input': "-Not Strike \n After CR-",
                'expected': "-Not Strike \n After CR-"},
            {'input': "-Strike-\n After", 'expected': "~~Strike~~\n After"}, ]

        for item in testItem:
            item['output'] = bear_export_sync.strike_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_mark_conv(self):
        testItem = [
            {'input': "::Mark::", 'expected': "```diff\n\+ Mark\n```\n"},
            {'input': ":: Not Mark::", 'expected': ":: Not Mark::"},
            {'input': "::Not Mark ::", 'expected': "::Not Mark ::"},
            {'input': "::Not Mark \n After CR::",
                'expected': "::Not Mark \n After CR::"},
            {'input': "::Mark::\n After", 'expected': "```diff\n\+ Mark\n```\n\n After"}, ]

        for item in testItem:
            item['output'] = bear_export_sync.mark_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_checkbox_conv(self):
        testItem = [
            {'input': "+ Checked", 'expected': "+\tChecked"},
            {'input': "+Not Checked", 'expected': "+Not Checked"},
            {'input': "- Empty", 'expected': "-\tEmpty"},
            {'input': "-Not Empty", 'expected': "-Not Empty"},
            {'input': "hello + Not Checked hello",
                'expected': "hello + Not Checked hello"},
            {'input': "hello - Not Empty hello",
                'expected': "hello - Not Empty hello"},]

        for item in testItem:
            item['output'] = bear_export_sync.checkbox_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_fileLink_conv(self):
        testItem = [
            {'input': "[file:5C01D883-4077-4954-8E28-B7C91ED285B7-67965-000005BA6002A679/myimsi.txt]",
             'expected': "[💾myimsi.txt](https://github.com/HibikeQuantum/PlayGround/blob/master/Bear/files/5C01D883-4077-4954-8E28-B7C91ED285B7-67965-000005BA6002A679/myimsi.txt)"},
            {'input': "[none:5C01D883-4077-4954-8E28-B7C91ED285B7-67965-000005BA6002A679/myimsi.txt]", 'expected': "[none:5C01D883-4077-4954-8E28-B7C91ED285B7-67965-000005BA6002A679/myimsi.txt]"},
        ]

        for item in testItem:
            item['output'] = bear_export_sync.fileLink_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

    def test_imageLink_conv(self):
        testItem = [
            {'input': "[image:SFNoteIntro0_File1/Bear 3 columns.png]", 'expected': "![Bear 3 columns.png](images/SFNoteIntro0_File1/Bear 3 columns.png)"},
            {'input': "[ image:SFNoteIntro0_File1/Bear 3 columns.png]", 'expected': "[ image:SFNoteIntro0_File1/Bear 3 columns.png]"},
            {'input': "[ image:SFNoteIntro0_File1/\wBear 3 columns.png]", 'expected': "[ image:SFNoteIntro0_File1/\wBear 3 columns.png]"}]

        for item in testItem:
            item['output'] = bear_export_sync.imageLink_conv(item['input'])
            self.assertEqual(item['expected'], item['output'])

#TODO: Add new test here
# phase 1 - underline, strike, checkbox, mark, file link, image link
# phase 2 - publish, diff, stactis
# phase 3 - tag pattern

if __name__ == '__main__':
    unittest.main()
