import unittest
import os
import sys

p = os.path.abspath('.')
sys.path.insert(1, p)

import document_analyzer as DA

reasonNotUsedFeature = "now app configure did not want these test"
class TestStringMethods(unittest.TestCase):
  def test_analyze_strings(self):
    testText = "안녕하세요 맛있는 운동 맛있는 식사 맛있는 코드 안녕하세요 식당입니다. 운동, 즐거움, 운동! 정말로 당신이 원하는 맛있는 코드가 여기에 있을지도 몰라요. 그럼 안녕하세요! 코드 코드 코드 코드! 닷 코드! 식사 운동 코드의 완벽한 조화"
    mockKeyword = "코드 운동 식사"
    mostUsedWords = DA.getMostUsedWords(testText)
    self.assertEqual(mockKeyword, mostUsedWords)

#TODO: Add new test here  
# phase 1 - underline, strike, checkbox, mark, file link, image link -> DONE
# phase 2 - publish, diff, stactis -> DOING NOW
# phase 3 - tag pattern

if __name__ == '__main__':
  unittest.main(argv=['first-arg-is-ignored'], exit=False)
