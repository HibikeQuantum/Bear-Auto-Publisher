# Bear-Auto-Publisher
Markdown export from Bear sqlite database and publishing at github repository

## Component
***bear_export_sync.py***   
**Version 0.1, 2022-07-26**

Python script for export and change markdown format for github markdown.

***AutoPublish.sh***
**Version 0.1, 2022-07-26**
Bash Script. Its endpoint of 'bear_export_sync.py'. This script read config and data from 'config' directory. and excecute python scirpt. and commit in your .git workspace and push automatically.

There is no need to worry about the BEAR document. Only read and various changes to the document are made to the copied work. You can still use the bare app as it is. This program does not have the ability to synchronize once extracted data back to the bear. Don't worry.

## install
1. git clone https://github.com/HibikeQuantum/Bear-Auto-Publisher.git
2. insert your environment data at `/config/config.json`
3. Remind, your export destination (`gitPath`) should be managed by `.git` (this program use git command) if u want more detail look this doc (https://github.com/git-guides/git-init)
4. Remind, your shell has permission to git repository 'master' and This program did not support interative case of git. (like input password, email.. )
5. and just command `sh AutoPublish.sh`

## Config
Check `/config/config.json` before running `AutoPublish.sh`
```json
{
  "secretTags": ["secret","secret2"],
  "noIamgeTags": ["copyright","fastcampus"],
  "allowTags": [],
  "githubPath": "https://github.com/HibikeQuantum/PlayGround",
  "gitPath":"/Users/kth/PlayGround/Bear",
  "allowPush": true,
  "allowOpenDiffAtGithub": true,
  "allowOpenSecretDiff": true,
  "automaticApprove": true
}
```

**'AutoPublish.sh' has rm command that working in "BEAR-AUTO-PUBLISHER/Working" directory and "gitPath" directory**
So never place a another file these path. 

Description of each key(config.json) below
- `"secretTags": ["secret","secret2"] ` It is tag setting that tracking but not upload your github.
- `"noIamgeTags": ["copyright","fastcampus"]` It is tag setting that tracking but the documents has these tag will not upload attached image.
- `"allowTags": []` It is tag setting that Upload only files with the tags you entered. By default, all documents are posted except documents that have a screed tag.
- `"githubPath": "https://github.com/HibikeQuantum/PlayGround"` Insert your github remote repository that related `gitPath`
- `"gitPath":"/Users/kth/PlayGround/Bear"` It is intended to operate based on the master branch. We will support more specific movements later.
- `"allowPush": true` If it is false, it did not upload data your github
- `"allowOpenDiffAtGithub": true` If it is false, It does not open browser to show file change information by commit.
- `"allowOpenSecretDiff": true` If it is false, It does not open default texteditor to show file change information by commit. (if you want use other program. https://support.apple.com/en-ke/guide/mac-help/mh35597/mac)
- `"automaticApprove": true` true If it is false, it asks if you want to upload it or not every time you run the program.

*See also: [Bear Power Pack](https://github.com/rovest/Bear-Power-Pack/blob/master/README.md)*

## Usage

```
sh -e AutoPublish.sh
```

See `--help` for more.

## Features

**Don't be confused.**
The 'Bear-Auto-Publisher' is completely different program from the original program before forking. 
It is a program that only cares about document diff checking and uploading document to github and change document format to git-markdown format.
The other features are not considered. So never try other function in original. The depricated code will be deleted after beta release.

## Use Tip
- If necessary, you can register the shell on the Cron tab and see it automatically upload data.

# For developer or Beginner
### devMode running
```bash
sh AutoPublish.sh --devMode
```
App printout each operating command. It Works only for bear notes with '#test' tag.
If you don't know exactly how the program works, I recommend watching it work and applying every documents.

### test Method
```bash
python test/test_export_sync.py
```
if you want function test, try next command at app root directory