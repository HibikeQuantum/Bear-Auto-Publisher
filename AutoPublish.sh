#!/bin/bash -ex

#FOR DEBUG
if [ "${1}" == "deubug" ]; then
  clear
  set -o xtrace
fi

# Catch terminate cmd from Sub Shell
trap "exit 1" 10
PROC="$$"

CWD=`pwd`
[ CWD == "/" ] && echo "[ERROR] It is not recommanded running these this program on filesystem root." && exit 1

WORKING_PATH="$CWD/Working"
[ -z "$WORKING_PATH" ] && echo "[ERROR] App could not find Working directory. Please reinstall 'BEAR-AUTO-PUBLISHER'" && exit 1

EXPORT_OUTPUT_PATH=`jq -r .exportPath config/config.json`
[ -z "$EXPORT_OUTPUT_PATH" ] && echo "[ERROR] App could not find 'export destination(.git path) directory. Config correct information at ./config/config.json'" && exit 1

GITHUB_URL=`jq -r .githubPath config/config.json`
[ -z "$GITHUB_URL" ] && echo "[ERROR] App could not find your github repository. Config correct information at ./config/config.json'" && exit 1

allowPush=`jq -r .allowPush config/config.json`
[ -z "$allowPush" ] && echo "[ERROR] App could not find allowPush value. Config correct information at ./config/config.json'" && exit 1

allowOpenSecretDiff=`jq -r .allowOpenSecretDiff config/config.json`
[ -z "$allowOpenSecretDiff" ] && echo "[ERROR] App could not find allowOpenSecretDiff value. Config correct information at ./config/config.json'" && exit 1

allowOpenDiffAtGithub=`jq -r .allowOpenDiffAtGithub config/config.json`
[ -z "$allowOpenDiffAtGithub" ] && echo "[ERROR] App could not find allowOpenDiffAtGithub value. Config correct information at ./config/config.json'" && exit 1

#config.json
automaticApprove=`jq -r .automaticApprove config/config.json`
[ -z "$automaticApprove" ] && echo "[ERROR] App could not find automaticApprove. Config correct information at ./config/config.json'" && exit 1

targetBranch=`jq -r .targetBranch config/config.json`
[ -z "$targetBranch" ] && echo "[ERROR] App could not find targetBranch. Config correct information at ./config/config.json'" && exit 1

executeAnalyzing=`jq -r .executeAnalyzing config/config.json`
[ -z "$executeAnalyzing" ] && echo "[ERROR] App could not find targetBranch. Config correct information at ./config/config.json'" && exit 1

timeNow=`date`
timeNowSimple=`date "+%Y%m%d"`
timestamp=`date "+%Y%m%d%s"`
commitMessage="${timeNow} Update Bear notes content automatically by BEAR_AUTO_PUBLISH App"
responseCode=`curl -o /dev/null --silent --head --write-out '%{http_code}\n' ${GITHUB_URL};`
secretDiffPath="${WORKING_PATH}/secret_${timestamp}.diff"
echo "init" > "${WORKING_PATH}/commit_hash"
commitHashPath="${WORKING_PATH}/commit_hash"
# tmpAddStrings="${WORKING_PATH}/filename.tmp"

if [ ! -d "${WORKING_PATH}/secrets/" ]; then
  mkdir "${WORKING_PATH}/secrets" && echo "[INFO] Complete - ${WORKING_PATH}/secrets DIR was created successfully" || echo "Failed to create ${WORKING_PATH}/secrets DIR"
fi

if [ ! -d "${WORKING_PATH}/BearImages/" ]; then
  mkdir "${WORKING_PATH}/BearImages" && echo "[INFO] Complete - ${WORKING_PATH}/BearImages DIR was created successfully" || echo "Failed to create ${WORKING_PATH}/BearImages DIR"
fi

if [ ! -d "${WORKING_PATH}/Statiscal_data" ]; then
  mkdir "${WORKING_PATH}/Statiscal_data" && echo "[INFO] Complete - ${WORKING_PATH}/Statiscal_data DIR was created successfully" || echo "Failed to create ${WORKING_PATH}/Statiscal_data DIR"
fi

if [ -d "$EXPORT_OUTPUT_PATH" ]; then
  rm -rf ${EXPORT_OUTPUT_PATH}/* && echo "[INFO] Complete - cleaning export space" || echo "failed to cleaning epxport space"
  mkdir ${EXPORT_OUTPUT_PATH}/BearImages/ && echo "[INFO] Complete - make image export DIR" || echo "failed to make epxport DIR"
else
  echo "Failed to initialize export space"
  exit 1
fi

rm -rf $WORKING_PATH/*.md && echo "[INFO] Complete - remove current working space '*.md'" || echo "failed to cleaning working space"
rm -rf $WORKING_PATH/*.log && echo "[INFO] Complete - remove current working space '*.log'"  || echo "failed to cleaning working space"
find $WORKING_PATH/secrets/ \! -name 'old_*.md' -delete && echo "[INFO] Complete - remove current working space '/secrets/*.md'"  || echo "[ERROR] failed to cleaning working space"
rm -rf $WORKING_PATH/BearImages/* echo "[INFO] Complete - remove current working space '/BearImages/*'"  || echo "failed to cleaning working space"

if [ "${responseCode}" -eq "200" ]; then
  echo "[INFO] github URL is valid. export script is start."
else
  echo "[ERROR] App can't find your github page. It seems github URL is not valid or Your computer may not connected to the Internet"
  exit 1
fi

# Check output dest .git Status and Set working Branch
(
  cd ${EXPORT_OUTPUT_PATH};

  # Change CW git brach
  currentBranch=$(git branch | sed -n -e 's/^\* \(.*\)/\1/p')
  if [ "${currentBranch}" == ${targetBranch} ]; then
    echo "nothing to do " > /dev/null
  else
    if [ `git branch --list $targetBranch` ]; then
      echo "Branch name "${targetBranch}" already exists. Change working branch to ${targetBranch}"
      git checkout "${targetBranch}"
    else
      echo "Branch name "${targetBranch}" is not exists. App will Create the branch and change working branch yuor book"
      git checkout -b "${targetBranch}"
    fi
  fi

  # Check git status
  if [[ `git status --porcelain` ]]; then
    echo "[INFO] It is tidy to Add new commit. App will process to publish your data to github"
  else
    echo "[WARNING] It is not tity status to add new commit. App process is end. 😓"
    kill -10 $PROC
  fi
)

echo "-----------------------------------------py-------------------------------------------"
python3 ${CWD}/bear_export.py
if [ "$?" -eq 0 ]; then
  echo "[INFO] export process is completed"
else
  echo "[ERROR] Failed to running export process code"
  exit 1
fi
echo "-----------------------------------------py-------------------------------------------"



#serilalize data.json
secret_file_names=`jq -c .secret_file_names config/data.json | jq -c '.[]'`
eval "secret_path_array=($secret_file_names)"
written_file_names=`jq -r .written_file_names config/data.json`

if [ -z "$written_file_names" ] && [ -z "$secret_file_names" ]; then
  echo "[INFO] there is nothing todo in this progmram. exit!"
  exit 0
fi

echo "\n\n" ${written_file_names} "\n[WARNING] 👉 These notes are will be uploaded to your git hub. Please check it. Are you sure you want to upload below documents to GitHub?' PRESS 'yY'"

if [ ${automaticApprove} == "true" ]; then
  echo "[INFO] App works in automatically approve mode"
else
  read -n 1;
  if [ $REPLY == [yYㅛ]]; then
    echo "[INFO] Accept OK sign"
  else
    echo $REPLY "[INFO] program will be terminated"
    exit 1
  fi
fi

if [ "$secret_file_names" == "null" ]; then
  echo "[WARNING] There is no secret tag. Upload every documents is very dangerous. Are you sure you want to upload below documents to GitHub?' PRESS 'yY'"
  if [ ${automaticApprove} == "true" ]; then
    echo "[INFO] App works in automatically approve mode"
  else
    read -n 1;
    if [ $REPLY == [yYㅛ]]; then
      echo "[INFO] Accept OK sign"
    else
      echo $REPLY "[INFO] program will be terminated"
      exit 1
    fi
  fi
else
  echo "\n\n" ${secret_file_names} "\n[INFO] 👉 These notes are tainted by secret. Diff result will be produced but it will not uploaded to github"
fi

#file initialize
echo "secret_diff_result_${timeNowSimple}" > ${secretDiffPath}
echo "empty" > ${commitHashPath}
echo "secretDiffPath:" ${secretDiffPath}

if [ "${secret_path_array}" != "null" ]; then
  for secret_file_name in "${secret_path_array[@]}"; do
    if [ -e "${WORKING_PATH}/secrets/old_${secret_file_name}" ]; then
      diff -ui "${WORKING_PATH}/secrets/old_${secret_file_name}" "${WORKING_PATH}/secrets/${secret_file_name}" >> ${secretDiffPath}
      # echo "${secret_file_name} document's diff data is added to ${secretDiffPath}"

      mv -f "${WORKING_PATH}/secrets/${secret_file_name}" "${WORKING_PATH}/secrets/old_${secret_file_name}"
      # echo "${secret_file_name} file name is changed to old_${secret_file_name}"

    elif [ -e "${WORKING_PATH}/secrets/${secret_file_name}" ]; then
      echo "______new_secret_md_added_title_${secret_file_name}____" >> ${secretDiffPath} 
      cat "${WORKING_PATH}/secrets/${secret_file_name}" >> ${secretDiffPath}
      # echo "${secret_file_name} secret diff data is added to ${secretDiffPath}"

      mv -f "${WORKING_PATH}/secrets/${secret_file_name}" "${WORKING_PATH}/secrets/old_${secret_file_name}"
      # echo "${secret_file_name} file name is changed to old_${secret_file_name}"
    else
      echo "[ERROR] ${secret_file_name} this is not proper value. call developer"
    fi
  done
  echo "[INFO] secret tainted documents diff data is added to ${secretDiffPath}"
else
  echo "[INFO] there is no secret tags in documents"
fi

mv -f ${secretDiffPath} ${WORKING_PATH}/Statiscal_data/ && echo "[INFO] data is moved to Statiscal DIR" || "[ERROR] failed to move"
secretDiffPath="${WORKING_PATH}/Statiscal_data/secret_${timestamp}.diff"

cp -r ${WORKING_PATH}/*.md ${EXPORT_OUTPUT_PATH}/ && echo "[INFO] complete - copy working result to export DIR (part 1) " || echo "fail to copy phase 1"
cp -r ${WORKING_PATH}/BearImages/ ${EXPORT_OUTPUT_PATH}/BearImages && echo "[INFO] complete - copy working result to export DIR (part 2) "|| echo "fail to copy phase 2"

if [ "$?" -eq 0 ]; then
  echo "$commitMessage" > "${EXPORT_OUTPUT_PATH}/last_commit_message.txt"
  echo "[INFO] Copy to git Path is completed"
else
  echo "[ERROR] Failed to copy to git Path"
  exit 1
fi

if [ "${allowPush}" == "true" ]; then
  (
  set -e
  cd ${EXPORT_OUTPUT_PATH};
  git gc --aggressive --prune=now
  git add -A;
  git add last_commit_message.txt;
  set +e
  )
  # python execute
  if [ "${executeAnalyzing}" == "true" ]; then
    echo "-----------------------------------------py-------------------------------------------"
    python3 ${CWD}/document_analyzer.py
    if [ "$?" -eq 0 ]; then
      echo "[INFO] document_analyzer process is completed"
      cp ${WORKING_PATH}/changeSTAT.svg ${EXPORT_OUTPUT_PATH}/
    else
      echo "[ERROR] Failed to running document_analyzer process. Program will be terminated"
    exit 1
fi
    echo "-----------------------------------------py-------------------------------------------"
  fi
  (
  set -e
  cd ${EXPORT_OUTPUT_PATH};
  git commit -m "${commitMessage}";
  git push -f origin "${targetBranch}";
  git log -n 1 --pretty=format:"%H" > "${commitHashPath}";
  set +e
  )

  if [ -n "${commitHashPath}" ]; then
    echo "[INFO] Push '.md' files to Github is completed"
  else
    echo "[ERROR] Failed to push data to github"
    exit 1
  fi
else
  echo "[INFO] Configration did not allow push to your github repository. Check /config/config.json"
fi

commitHash=`cat $commitHashPath`

if [ "${allowOpenDiffAtGithub}" == "true" ]; then
  open "${GITHUB_URL}/commit/${commitHash}"
  echo "[INFO] Github commit tab is opened. Check diffence between old document and current document"
else
  echo "[INFO] Configration did not allow open your github repository. Check /config/config.json"
fi

if [ "${allowOpenSecretDiff}" == "true" ]; then
  open ${secretDiffPath}
  echo "[INFO] Every process is clear. Program will be terminated."
  exit 0
else
  echo "[INFO] Configration did not allow open text view tool. Check /config/config.json"
  exit 0
fi