# package for analyze
from konlpy.tag import Kkma
# inlcude Kkma, There are other options, ex. Okt, Komoran, Hannanum
from collections import  Counter

# package for file read /write feat.
import json, re, csv, os, datetime, sys
from git import Repo


"""
NOT USED NOW
"""
# import nltk
# nltk.download('gutenberg')
# # english analyze
# from nltk import regexp_tokenize
# from nltk.corpus import gutenberg

""" 
# recipe data structure preview 

rowRecipe = {
  "FileName":"",
  "Date":"", 
  "TotalCharacters": 0,
  "TotalKeyward": [],
  "ChangedCharacters": 0,
  "ChangedKeyward":[],
}
"""

""" CONST DEFINE AND INITIALIZE """
PWD = os.path.dirname(os.path.abspath(__file__))
CONFIG_JSON_PATH = os.path.join(PWD, "config/config.json")
DATA_JSON_PATH = os.path.join(PWD, "config/data.json")
STATS_CSV_PATH = os.path.join(PWD, "Working/Statiscal_data/publishData.csv")
KEYWORD_NUMBERS = 10

""" Global Variables"""


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


def initializeData():
  if not os.path.isfile(STATS_CSV_PATH):
    print("[WANRNING] App did not found. csv File. App will make empty file.")
    with open(STATS_CSV_PATH, "w", encoding = 'utf-8', newline='') as dataCsv:
      print("[INFO]", STATS_CSV_PATH, " is maiden!")

  with open(CONFIG_JSON_PATH, "r", encoding='utf-8') as configJsonFile:
    global GIT_PATH
    configJson = json.load(configJsonFile)
    GIT_PATH = configJson['gitPath']

  #### Not used NOW
  # with open(DATA_JSON_PATH, "r", encoding='utf-8') as dataJsonFile:
  #   writtenFileNameList = json.load(dataJsonFile)['written_file_names']


def getChangedDiffIndexArray():
  resultArr = []

  repository = Repo(GIT_PATH, search_parent_directories=True)
  headCommit = repository.head.commit
  Diffs = headCommit.diff('HEAD~1', create_patch=True, unified=0)

  for diff_index_M in Diffs.iter_change_type('M'):
    print("TYPE _M:", diff_index_M)
    resultArr.append(diff_index_M)
  for diff_index_A in Diffs.iter_change_type('A'):
    print("TYPE _A:", diff_index_A)
    resultArr.append(diff_index_A)
  
  if len(resultArr) == 0:
    print("[INFO] In git diff index, There is no change that worthy of reference. So nothing todo.")
    sys.exit(0)
  else:
    return resultArr


def anlayzeDiffIndex(diff_index_array):
  recipeArray = []

  for diff_index in diff_index_array:
    filePath = os.path.join(GIT_PATH, diff_index.b_path)
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
      
      # if line is not meta data, find vaild line.
      # In code block. git print '-' each line. These formatting policy makes a mess of logic. So 'previouChar' is used to avoid the malfunctioning.
      matchedLine = re.match(r'^\+(.*)', line)
      if previouChar == "-" and line[0:1] == "-":
        matchedLine = re.match(r'^\-(.*)', line)

      if matchedLine is not None:
        matchedLine = matchedLine.group(1)
        sentence += matchedLine
      previouChar = line[0:1]

    #end one diff index.
    rowRecipe['FileName'] = filePath
    rowRecipe['Date'] =  datetime.datetime.now()
    rowRecipe['TotalCharacters'] = getFileTextLen(filePath)
    rowRecipe['TotalKeyward'] = analyzeWholeText(filePath)
    rowRecipe['ChangedCharacters'] = newCharacterNumbers
    rowRecipe['ChangedKeyward'] = getMostUsedWords(sentence)
    
    recipeArray.append(rowRecipe)

    """
    TODO: english word is ignored. in these steps. It could be enhanced.
    # rowRecipe['TotalKeyward'] = analyzeEngDoc(filePath)
    """

  #end every diff indexes.
  print("[DONE] analyze process is done")
  return recipeArray


def appendDataToCSV(recipeArr):
  with open(STATS_CSV_PATH, "a", encoding = 'utf-8') as dataFile:
    writerObj = csv.writer(dataFile)
    for dict in recipeArr:
      writerObj.writerow([
      dict['FileName'],
      dict['Date'],
      dict['TotalCharacters'],
      dict['TotalKeyward'],
      dict['ChangedCharacters'],
      dict['ChangedKeyward']
      ])
      
  print("_______________________________________________________")
  print("[INFO] Write is over! ", len(recipeArr), " rows are inserted at CSV")


def main():
  initializeData()
  diff_index_array = getChangedDiffIndexArray()
  csvQueue = anlayzeDiffIndex(diff_index_array)
  appendDataToCSV(csvQueue)


if __name__ == '__main__':
  main()