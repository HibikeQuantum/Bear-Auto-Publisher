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

def getContents(m):
  return m.group(1)

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
    return

def analyzeDiff(text):
  return getMostUsedWords(text)

def returnOnlyGroup(m):
  return m.group(1)



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
repository = Repo(gitPath, search_parent_directories=True)
target_diff_index_array = []
Hcommit = repository.head.commit
diff_index_list = Hcommit.diff('HEAD~1', create_patch=True, unified=0)

for diff_index in diff_index_list.iter_change_type('M'):
    target_diff_index_array.append(diff_index)
for diff_index in diff_index_list.iter_change_type('A'):
    target_diff_index_array.append(diff_index)



if target_diff_index_array:
  for diff_index in target_diff_index_array:
    file_path = os.path.join(gitPath,diff_index.b_path)
    wholeSendtences = diff_index.diff.decode('utf-8')
    sentence = ""
    rowRecipe = {}

    for (index, line) in enumerate(wholeSendtences.split("\n")):
      matchedLine = re.match(r'^\+(.*)', line)
      striptedString = ""
      if matchedLine is None:
        print("Nothing to do")
      else:
        matchedLine = matchedLine.group(1)
        striptedString = line.lstrip()
        if striptedString[0:2] != "@@":
          sentence += matchedLine + "\n"

    rowRecipe['FileName'] = file_path
    rowRecipe['Date'] =  datetime.datetime.now()
    rowRecipe['TotalCharacters'] = getFileTextLen(file_path)
    rowRecipe['TotalKeyward'] = analyzeWholeText(file_path)

    """ TODO: english word is ignored. in these steps. enhance it! """
    # rowRecipe['TotalKeyward'] = analyzeEngDoc(file_path)

    rowRecipe['ChangedCharacters'] = len(sentence)
    rowRecipe['ChangedKeyward'] = getMostUsedWords(sentence)
    csvQueue.append(rowRecipe)
    # print("END___: ", data)

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


