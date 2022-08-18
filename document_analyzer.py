# package for analyze
from konlpy.utils import pprint
from konlpy.tag import Kkma
# There are other options, for example Okt, Komoran, Hannanum
from collections import  Counter

# package for file read /write feat.
import json
import re
import csv
import os, datetime
from git import Repo

"""
NOT USED NOW
"""
# import nltk
# nltk.download('gutenberg')
# # english analyze
# from nltk import regexp_tokenize
# from nltk.corpus import gutenberg

""" data structure preview """
rowRecipe = {
  "FileName":"",
  "Date":"",
  "TotalCharacters": 0,
  "TotalKeyward": [],
  "ChangedCharacters": 0,
  "ChangedKeyward":[],
}

"""
NOT USED NOW
"""
# def analyzeEngDoc(path):
#   myCounter = Counter()
#   with gutenberg.open(path).read() as text:
#     for line in text:
#       line_letters = [
#         char for char in line.lower() if char.isalpha()
#       ]
#       myCounter.update(Counter(line_letters))

#       pattern = r'''(?x) ([A-Z]\.)+ | \w+(-\w+)* | \$?\d+(\.\d+)?%? | \.\.\. | [][.,;"'?():-_`]'''
#       tokens_en = regexp_tokenize(text, pattern)

#       en = nltk.Text(tokens_en)
#       top5 = en.plot(10)

#     # keywords = ""
#     # count = myCounter.most_common(5)
#     # for name, count in sorted(count):
#     #   keywords += name + " "

#     # keywords = keywords[0:-1]
#     # print(keywords,"하이")
#     # return keywords
#     print(top5,"fd3")
#     return top5

def getMostUsedWords(text):
  okt = Kkma()
  noun = okt.nouns(text)
  count = Counter(noun).most_common(KEYWORD_NUMBERS)
  keywords = ""
  for name, count in sorted(count):
    keywords += name + " "
  keywords = keywords[0:-1]
  return keywords

def getFileTextLen(path):
  with open(path,'r',encoding='UTF8') as file:
    text = file.read()
    splitdata = text.split()
    return len(splitdata)

def analyzeWholeText(path):
  with open(path,'r',encoding='UTF8') as file:
    text = file.read()
    return getMostUsedWords(text)

# CONFIG VALUE
pwd = os.path.dirname(os.path.abspath(__file__))
configJsonPath = os.path.join(pwd, "config/config.json")
dataJsonPath = os.path.join(pwd, "config/data.json")
statisticalPath = os.path.join(pwd, "Working/Statiscal_data/publishData.csv")
gitPath = None

# CONSTANT AND INITIALIZE
KEYWORD_NUMBERS = 10
csvQueue = []

if not os.path.isfile(statisticalPath):
  print("App did not found. csv File. App will make initial file.")
  with open(statisticalPath, "w", encoding = 'utf-8', newline='') as dataCsv:
    print(statisticalPath, "is maiden!")

with open(configJsonPath, "r", encoding='utf-8') as configJsonFile:
  configJson = json.load(configJsonFile)
  gitPath = configJson['gitPath']

with open(dataJsonPath, "r", encoding='utf-8') as dataJsonFile:
  writtenFileNameList = json.load(dataJsonFile)['written_file_names']

# Main Logic is Started here.
# TODO: Make Main function
repository = Repo(gitPath, search_parent_directories=True)
target_diff_index_array = []
Hcommit = repository.head.commit
DiffIndex = Hcommit.diff('HEAD~1', create_patch=True, unified=0)

for diff_index_M in DiffIndex.iter_change_type('M'):
  target_diff_index_array.append(diff_index_M)
for diff_index_A in DiffIndex.iter_change_type('A'):
  print("_A:", diff_index_A)
  target_diff_index_array.append(diff_index_A)


if len(target_diff_index_array) == 0:
  print("Nothing todo")

for diff_index in target_diff_index_array:
  file_path = os.path.join(gitPath,diff_index.b_path)
  wholeSendtences = diff_index.diff.decode('utf-8')

  # initialize collecting data
  sentence = ""
  rowRecipe = {}
  newCharacterNumbers = 0
  previouChar = ""
  # iterate git-diff-lines
  for (index, line) in enumerate(wholeSendtences.split("\n")):
    # ignore option line.
    if line[-2:] == "@@":
      headInfoArr = line.split(" ")
      newCharacterNumbers = headInfoArr[2][1:]
      index = newCharacterNumbers.find(",")
      if index != -1:
        newCharacterNumbers = newCharacterNumbers[0:index]
      continue
    
    matchedLine = re.match(r'^\+(.*)', line)
    striptedString = ""
    if previouChar == "-" and line[0:1] == "-":
      matchedLine = re.match(r'^\-(.*)', line)
      
    if matchedLine is not None:
      matchedLine = matchedLine.group(1)
      striptedString = line.lstrip()
      sentence += matchedLine
    previouChar = line[0:1]

  rowRecipe['FileName'] = file_path
  rowRecipe['Date'] =  datetime.datetime.now()
  rowRecipe['TotalCharacters'] = getFileTextLen(file_path)
  rowRecipe['TotalKeyward'] = analyzeWholeText(file_path)
  rowRecipe['ChangedCharacters'] = newCharacterNumbers
  rowRecipe['ChangedKeyward'] = getMostUsedWords(sentence)

  """
  TODO: english word is ignored. in these steps. It could be enhanced.
  # rowRecipe['TotalKeyward'] = analyzeEngDoc(file_path)
  """
  csvQueue.append(rowRecipe)

# Write file
with open(statisticalPath, "a", encoding = 'utf-8') as dataCsv:
wr = csv.writer(dataCsv)
for dict in csvQueue:
  wr.writerow([
  dict['FileName'],
  dict['Date'],
  dict['TotalCharacters'],
  dict['TotalKeyward'],
  dict['ChangedCharacters'],
  dict['ChangedKeyward']
  ])


