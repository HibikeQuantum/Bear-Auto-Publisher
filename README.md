# Bear-Auto-Publisher
Markdown export from Bear SQLite database and publishing at GitHub repository  
[한국어 소개 블로그](https://hibikequantum.github.io/devlog/SideProject-1)

## recommend environment for running
- MacOS
- global python command should be linked with python3 (python 3.9.6 is confirmed to have been executed)
- bash 3.2.57, 5.1.57 are confirmed to have been executed

## install and execute
1. Download app by git clone or zip
```
git clone https://GitHub.com/HibikeQuantum/Bear-Auto-Publisher.git
```
2. Install jq command at your shell. (jq is CLI tool to operate json file)
```
brew install jq
```
3. Install python package (At Bear-Auto-Publisher Directory)
```
pip install -r requirements.txt
```
4. insert your environment data
```
vi Bear-Auto-Publisher/config/config.json
```
5. Remind, your export destination (`gitPath`) should be managed by `.git`. Because this program use git command. If you want more detail about git. please check the next document [link](https://GitHub.com/git-guides/git-init)
6. Remind, your shell has permission to git repository 'master'. This program did not support an interactive case of git. (like input password, email.. ). So an automatic authentication process is required.
7. Exceute end point program 'AutoPublish.sh 
```
sh AutoPublish.sh
```

###### WARNING
```diff
- 'AutoPublish.sh' has rm command that works in "BEAR-AUTO-PUBLISHER/Working" directory and "exportPath" directory
- So never place a another file at these paths
```

## Configuration Guide
Check `/config/config.json` before running `AutoPublish.sh`
```json
{
  "secretTags": ["secret","temporary", "private"],
  "noIamgeTags": ["copyright","fastcampus"],
  "allowTags": [],
  "githubPath": "https://github.com/HibikeQuantum/PlayGround",
  "gitPath":"/Users/kth/Code/PlayGround",
  "exportPath": "/Users/kth/Code/PlayGround/Bear",
  "targetBranch" : "master",
  "allowPush": true,
  "allowOpenDiffAtGithub": true,
  "allowOpenSecretDiff": true,
  "automaticApprove": true,
  "executeAnalyzing": true
}
```
#### Description of each key(config.json) below
- `"secretTags": ["secret","secret2"] ` It is tag setting that tracking but not upload your GitHub.
- `"noIamgeTags": ["copyright", "fastcampus"]` It is tag setting that tracking but the documents has these tag will not upload an attached image.
- `"allowTags": []` It is tag setting that Upload only files with the tags you entered. By default, all documents are posted except documents that have a screed tag.
- `"GitHubPath": "https://GitHub.com/HibikeQuantum/PlayGround"` Insert your GitHub remote repository that is related `gitPath`
- `"gitPath":"/Users/kth/Code/PlayGround"` Place of .git file
- `"exportPath": "/Users/kth/Code/PlayGround/Bear"`, Place of md exported file. It should subdirectory or same directory of gitPath
- `"targetBranch" : "master"` origin github upstream branch name. Basically, 'main' is latest dafault value.
- `"allowPush": true` If it is false, it did not upload data to your GitHub
- `"allowOpenDiffAtGitHub": true` If it is false, It does not open browser to show file change information by commit.
- `"allowOpenSecretDiff": true` If it is false, It does not open default texteditor to show file change information by commit. (if you want use other program.  Read next link https://support.apple.com/en-ke/guide/mac-help/mh35597/mac)
- `"automaticApprove": true` If it is false, it asks if you want to upload it or not every time you run the program.
- `"executeAnalyzing": true` If it is false, App should not analyze documents data and did not generate csv file

**Caution**
The 'Bear-Auto-Publisher' is a completely different program from the original program before forking. 
It is a program that only cares about document diff checking and uploading documents to GitHub and changing document format to git-markdown format.
The other features are not considered.

## Component description
***bear_export.py***   
Version 1.01 (Release. 2022-09-01)  
Python script for export and change markdown format for GitHub markdown.

***document_analyzer.py***   
Version 1.01 (Release. 2022-09-01)  
Python script for analyzing string data and visualizing document's changing information.

***AutoPublish.sh***
Version 1.01 (Release. 2022-09-01)
Bash Script. Its endpoint of 'bear_export.py' and 'document_analyzer.py' can read configuration and data from 'config' directory. And execute the python script after then command commit at your .git workspace and push GitHub upstream automatically.

There is no need to worry about the BEAR document. This app only read data from bear SQLite and various change works occurred at exported files. You can still use the Bare app as it is. This program cannot synchronize once extracted data to the BEAR app. Don't worry!

## Use Tip
- If necessary, you can register the shell on the Cron tab and see it automatically upload data.
- At Bear APP, Search with the following keywords(it's default keyword that I used) to see which documents are uploaded. Check the risk of unwanted files being uploaded.
- Analyzed data graph is saved by `/Working/changeSTAT.html`, `/Working/changeSTAT.svg`
- Analyzed original data is save by `/Working/Statiscal_data/publishData.csv`
```
-#private -#secret -#temporary
```
# For developers or Beginner
## Developer mode running
```bash
sh AutoPublish.sh --devMode
```
with this argument, App will printout each operating command. And exporting only for bear notes with `#test`' tag.  

If you don't know exactly how the program works or are worring about program working, I recommend it to running with the devMode argument and then execute program without `--devMode`



## Running unittest
if you want unit test, try below command at app root directory
```bash
python -m unittest
```
