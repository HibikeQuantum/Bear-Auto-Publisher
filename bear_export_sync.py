# encoding=utf-8
# python3.6
# bear_export_sync.py
# Developed with Visual Studio Code with MS Python Extension.

'''
# Markdown export from Bear sqlite database 
Version 1.4, 2020-01-11
modified by: github/andymatuschak, andy_matuschak@twitter
original author: github/rovest, rorves@twitter

See also: bear_import.py for auto import to bear script.

## Sync external updates:
First checks for changes in external Markdown files (previously exported from Bear)
* Replacing text in original note with callback-url replace command   
  (Keeping original creation date)
  If changes in title it will be added just below original title
* New notes are added to Bear (with x-callback-url command)
* New notes get tags from sub folder names, or `#.inbox` if root
* Backing up original note as file to BearSyncBackup folder  
  (unless a sync conflict, then both notes will be there)

## Export:
Then exporting Markdown from Bear sqlite db.
* check_if_modified() on database.sqlite to see if export is needed
* Uses rsync for copying, so only markdown files of changed sheets will be updated  
  and synced by Dropbox (or other sync services)
* "Hides" tags with `period+space` on beginning of line: `. #tag` not appear as H1 in other apps.   
  (This is removed if sync-back above)
* Or instead hide tags in HTML comment blocks like: `<!-- #mytag -->` if `hide_tags_in_comment_block = True`
* Makes subfolders named with first tag in note if `make_tag_folders = True`
* Files can now be copied to multiple tag-folders if `multi_tags = True`
* Export can now be restricted to a list of spesific tags: `limit_export_to_tags = ['bear/github', 'writings']`  
or leave list empty for all notes: `limit_export_to_tags = []`
* Can export and link to images in common image repository
* Or export as textbundles with images included 
'''

make_tag_folders = False  # Exports to folders using first tag only, if `multi_tag_folders = False`
multi_tag_folders = True  # Copies notes to all 'tag-paths' found in note!
                          # Only active if `make_tag_folders = True`
hide_tags_in_comment_block = True  # Hide tags in HTML comments: `<!-- #mytag -->`

# The following two lists are more or less mutually exclusive, so use only one of them.
# (You can use both if you have some nested tags where that makes sense)
# Also, they only work if `make_tag_folders = True`.
only_export_these_tags = []  # Leave this list empty for all notes! See below for sample
# only_export_these_tags = ['bear/github', 'writings'] 

export_as_textbundles = False  # Exports as Textbundles with images included
export_as_hybrids = True  # Exports as .textbundle only if images included, otherwise as .md
                          # Only used if `export_as_textbundles = True`
export_image_repository = True  # Export all notes as md but link images to 
                                 # a common repository exported to: `assets_path` 
                                 # Only used if `export_as_textbundles = False`

# if U don't want convert each style, change value to False
is_bold_conv_mode = False 
is_sepa_conv_mode = False    # if U don't want insert newline before sparator at github. Change value to False.
is_imageLink_conv_mode = False
is_fileLink_conv_mode = False
is_italic_conv_mode = False
is_underline_conv_mode = True
is_checkbox_conv_mode = False
is_strike_conv_mode = False
is_mark_conv_mode = True    # if U don't want insert newline at marked sentence. Change value to False
is_codeblock_mode = True

debug_mode = False #Print each varaible's value and type. At prod please set false
debug_mode_level_middle = False #Print each varaible's value and type. At prod please set false
allow_only_test = False

codeblock_flager = False
allow_always_parsing = True

import os
HOME = os.getenv('HOME', '')
CWD = os.path.dirname(os.path.abspath(__file__))
export_path = os.path.join(CWD, "Working")
default_backup_folder = os.path.join(HOME, "Work", "BearSyncBackup")


# NOTE! Your user 'HOME' path and '/BearNotes' is added below!
# NOTE! So do not change anything below here!!!
import sys
import sqlite3
import datetime
import re
import subprocess
import urllib.parse
import time
import shutil
import fnmatch
import json
import argparse

parser = argparse.ArgumentParser(description="Sync Bear notes")
parser.add_argument("--backup", default=default_backup_folder, help="Path where conflicts will be backed up (must be outside of --out)")
parser.add_argument("--images", default=None, help="Path where images will be stored")
parser.add_argument("--skipImport", action="store_const", const=True, default=False, help="When present, the script only exports from Bear to Markdown; it skips the import step.")
parser.add_argument("--excludeTag", action="append", default=[], help="Don't export notes with this tag. Can be used multiple times.")
parser.add_argument("--noImage", action="append", default=[], help="Don't export image with this tag. Can be used multiple times.")
parser.add_argument("--allowTag", action="append", default=[], help="Don't export image with this tag. Can be used multiple times.")
parser.add_argument("--devMode", action="store_const", const=True, default=False, help="If devmode, program Print detail operation status. and program only update documents that has #test tag")

parsed_args = vars(parser.parse_args())

set_logging_on = True

# TODO: below variable did not working now. should be change for prevent upload to git hub
no_export_tags = parsed_args.get("excludeTag")  # If a tag in note matches one in this list, it will not be exported.
no_image_tags = parsed_args.get("noImage")  # If a tag in note matches one in this list, it will not has image contents.
allowed_tags = parsed_args.get("allowedTag")  # If a tag in note matches one in this list, it will exported the others did not exported.
is_dev_mode = parsed_args.get("devMode")

path = os.path.dirname(os.path.abspath(__file__))
with open(path + '/config/config.json', 'r') as f:
    config_data = json.load(f)

for tag in config_data['secretTags']:
    no_export_tags.append(tag)
for tag in config_data['noIamgeTags']:
    no_image_tags.append(tag)
for tag in config_data['allowTags']:
    allowed_tags.append(tag)

allowed_export_files = []
secret_file_names = []
no_image_files = []
written_file_names = []

if is_dev_mode is True:
    debug_mode = True 
    debug_mode_level_middle = True
    allow_only_test = True

# NOTE! "export_path" is used for sync-back to Bear, so don't change this variable name!
multi_export = [(export_path, True)]  # only one folder output here. 
# Use if you want export to severa places like: Dropbox and OneDrive, etc. See below
# Sample for multi folder export:
# export_path_aux1 = os.path.join(HOME, 'OneDrive', 'BearNotes')
# export_path_aux2 = os.path.join(HOME, 'Box', 'BearNotes')

# NOTE! All files in export path not in Bear will be deleted if delete flag is "True"!
# Set this flag fo False only for folders to keep old deleted versions of notes
# multi_export = [(export_path, True), (export_path_aux1, False), (export_path_aux2, True)]

temp_path = os.path.join(HOME, 'Temp', 'BearExportTemp')  # NOTE! Do not change the "BearExportTemp" folder name!!!
bear_db = os.path.join(HOME, 'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite')
sync_backup = parsed_args.get("backup") # Backup of original note before sync to Bear.
log_file = os.path.join(sync_backup, 'bear_export_sync_log.txt')

# Paths used in image exports:
bear_image_path = os.path.join(HOME,
    'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Images')
assets_path = parsed_args.get("images") if parsed_args.get("images") else os.path.join(export_path, 'BearImages')
# --images 받은 인자가 있으면 그걸 받고 없으면 default export 디렉토리의 BearImages를 참조하게 한다.

sync_ts = '.sync-time.log'
export_ts = '.export-time.log'

sync_ts_file = os.path.join(export_path, sync_ts)
sync_ts_file_temp = os.path.join(temp_path, sync_ts)
export_ts_file_exp = os.path.join(export_path, export_ts)
export_ts_file = os.path.join(temp_path, export_ts)

gettag_sh = os.path.join(HOME, 'temp/gettag.sh')
gettag_txt = os.path.join(HOME, 'temp/gettag.txt')

fileLinkRegex = r'\[file\:([0-9A-Z-/]+)\/(.+\.[\w]{3,20})\]'
imageLinkRegex = r'\[image\:([-_+~/\w\d\s]+)\/(.+\.[\w]{3,20})\]$'
markRegex = r'(.*)\:\:([^\s]+.*[^\s]+)\:\:(.*)'
tagRegex1 = r'(?<!\S)\#([.\w\/\-]+)[ \n]?(?!([\/ \w]+\w[#]))'
tagRegex2 = r'(?<![\S])\#([^ \d][.\w\/ ]+?)\#([ \n]|$)'


def main():
    init_gettag_script()
    initialize_working_data()
    if not parsed_args.get("skipImport"): # default False. So always  this function will operate.
        sync_md_updates()
    if check_db_modified() or allow_always_parsing :
        delete_old_temp_files()
        export_tags()
        note_count = export_markdown()
        write_time_stamp() #TODO: is this function meaningful?
        # rsync_files_from_temp() #TODO: is this function meaningful?
        # if export_image_repository and not export_as_textbundles: #t/f가 기본이라 항시 실행된다.
        #     copy_bear_images()
            # TODO: delete next functino call At Release. It's not used function. I left it because it might be used.
            # rename_copied_file() 
        notify('Export completed') #TODO: is this function meaningful?
        # make_result_data()
        # remove_secret_document() #TODO: This brach NOW
        
        # move secret .md to /secret folder
        write_working_data()
        write_log(str(note_count) + ' notes exported to: ' + export_path)
        exit(0)
    else:
        print('*** No notes needed exports')
        exit(0)

# def rename_copied_file():
#     for (root, dirnames, filenames) in os.walk(export_path): 
#         for f in filenames:
#             os.rename(os.path.join(root, f), os.path.join(root, f.replace(' ', '_')))

def write_working_data():
    file_path = "./config/data.json"
    json_data = {
        "secret_file_names":secret_file_names,
        "allowed_file_paths":allowed_export_files,
        "no_image_file_paths":no_image_files,
        "written_file_names":written_file_names
    }
    with open(file_path, "w") as outfile:
        json.dump(json_data, outfile)
        logger("data.json is saved")

def initialize_working_data():
    file_path = "./config/data.json"
    json_data = {
        "secret_file_paths":[],
        "allowed_file_paths":[],
        "no_image_file_paths":[],
        "written_file_names":[]
    }
    with open(file_path, 'w') as outfile:
        json.dump(json_data, outfile)
        logger("data.json is initialized")


def write_log(message):
    if set_logging_on == True:
        if not os.path.exists(sync_backup):
            os.makedirs(sync_backup)
        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        message = message.replace(export_path + '/', '')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(time_stamp + ': ' + message + '\n')


def check_db_modified():
    if not os.path.exists(sync_ts_file):
        return True
    db_ts = get_file_date(bear_db)
    last_export_ts = get_file_date(export_ts_file_exp)
    #20220630 KTH
    #return db_ts > last_export_ts
    return True

def export_tags():
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0' AND `ZARCHIVED` LIKE '0'"
        documents = conn.execute(query)

    for document in documents:
        if document['ZTITLE'].find("test") == -1:
            if (allow_only_test is True):
                continue            
        title = document['ZTITLE']
        filename = clean_title(title)
        md_text = document['ZTEXT'].rstrip()
        tag_parser(filename, md_text)

# A large function that retrieves documents, formats them, and saves them.
def export_markdown():
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0' AND `ZARCHIVED` LIKE '0'"
        documents = conn.execute(query)

    note_count = 0
    for document in documents:
        # Make sure that only the test document works.
        if (document['ZTITLE'].find("test") == -1) and (allow_only_test is True):
            print ( document['ZTITLE'], allow_only_test is True, "fd this DOC will be passed")
            continue        

        # Variable for handling block of code(```). The conversion function does not work when it is in the True state.
        global codeblock_flager
        codeblock_flager = False

        title = document['ZTITLE']
        md_text = document['ZTEXT'].rstrip()
        creation_date = document['ZCREATIONDATE']
        modified = document['ZMODIFICATIONDATE']
        filename = clean_title(title)
        file_path = os.path.join(temp_path, filename)
        splited_sentences = md_text.split("\n")
        joined_Sentences = ""
        splitChar= "\n\n"
        logger(document['ZTITLE'] + " document is processing 📀 This doc is created")
        make_iamge(md_text)     
        for (index, sentence) in enumerate(splited_sentences):
            if sentence is None:
                continue

            sentence_dict = {
                "sentence":sentence,
                "underline_conv_flag":False,
                "bold_conv_flag":False,
                "italic_conv_flag":False,
                "strike_conv_flag":False,
            }
            note_count += 1
            mod_dt = dt_conv(modified)
            sentence_dict = hide_tags(sentence_dict)
            sentence_dict = codeblock_tainter(sentence_dict)
            sentence_dict = checkbox_conv(sentence_dict)
            sentence_dict = bold_conv(sentence_dict)        # * -> **
            sentence_dict = separator_conv(sentence_dict)   
            sentence_dict = underline_conv(sentence_dict)   # _ -> ***
            sentence_dict = italic_conv(sentence_dict)      # / -> *
            sentence_dict = strike_conv(sentence_dict)
            sentence_dict = mark_conv(sentence_dict)
            sentence_dict = process_image_links(sentence_dict, file_path) #실제로 이미지링크가 파싱되는 함수
            #TODO: file link
            if index == len(splited_sentences)-1 :
                splitChar = ""
            joined_Sentences += sentence_dict['sentence'] + splitChar

        for (index, secret_file_name) in enumerate(secret_file_names):
            if (filename +".md") == (secret_file_name): # 비밀케이스의 경우
                secret_file_path = os.path.join(path,"Working/secrets", filename)
                write_file(secret_file_path + '.md', joined_Sentences, mod_dt)
                break
            elif index == (len(secret_file_names) -1) : # 일반적인 경우 마지막까지 탐색하고 일반으로 쓴다.
                none_secret_file_path = os.path.join(export_path, filename)
                write_file(none_secret_file_path + '.md', joined_Sentences, mod_dt)
                written_file_names.append(filename + '.md')
    return note_count


def check_image_hybrid(md_text): #not used
    if export_as_hybrids:
        if re.search(r'\[image:(.+?)\]', md_text):
            return True
        else:
            return False
    else:
        return True


def make_iamge(md_text): # 더 이상 호출 되지 않는다.
    matches = re.findall(r'\[image:(.+?)\]', md_text)
    if matches is not None:
        for match in matches:
            image_name = match
            new_name = image_name.replace('/', '_') #여기 언더바를 넣는 로직이 있어서 내가 만든 함수랑 겹쳐서 꼬이는구나
            new_name2 = new_name.replace(' ', '_')
            source = os.path.join(bear_image_path, image_name)
            target = os.path.join(assets_path, new_name2)
            print(new_name, "기존뉴네임", new_name2, "파이널네임")
            shutil.copy2(source, target)

# Feat: Analyze file and extract tag information. After determining the tag, end process
def tag_parser(filename, md_text):
    # Files copied to all tag-folders found in note
    tags = []
    for matches in re.findall(tagRegex1, md_text):
        tag = matches[0]
        tags.append(tag)
    for matches2 in re.findall(tagRegex2, md_text):
        tag2 = matches2[0]
        tags.append(tag2)
    # if len(tags) == 0:
        # No tags found, copy to root level only
    
    # tags = every tag in file
    for tag in tags:
        if tag == '/':
            continue
        if allowed_tags: 
            # EXPORT가 되지 않으면 계속 순회하기 위해 있는 플래그
            export = False
            for export_tag in only_export_these_tags:
                if tag.lower().startswith(export_tag.lower()):
                    path = os.path.join(export_path, filename)
                    allowed_export_files.append(path)
                    written_file_names.append(filename)
                    export = True
                    return
            if not export:
                continue 
        # 'no_export_tags' is global var that from config.json
        for no_tag in no_export_tags:
            if tag.lower() == no_tag.lower():
                secret_file_names.append(filename+".md")
                return
    for tag in tags:
        for no_image_tag in no_image_tags:
            if tag.lower() == no_image_tag.lower():
                no_image_file_path = os.path.join(export_path, filename)
                no_image_files.append(no_image_file_path + '.md')
                return 

def sub_path_from_tag(temp_path, filename, md_text):
    # Get tags in note:
    pattern1 = r'(?<!\S)\#([.\w\/\-]+)[ \n]?(?!([\/ \w]+\w[#]))'
    pattern2 = r'(?<![\S])\#([^ \d][.\w\/ ]+?)\#([ \n]|$)'
    # @multi_tag_folders=False
    if multi_tag_folders: 
        # Files copied to all tag-folders found in note
        tags = []
        for matches in re.findall(pattern1, md_text):
            tag = matches[0]
            tags.append(tag)
        for matches2 in re.findall(pattern2, md_text):
            tag2 = matches2[0]
            tags.append(tag2)
        if len(tags) == 0:
            # No tags found, copy to root level only
            return [os.path.join(temp_path, filename)]
    else:
        # Only folder for first tag
        match1 =  re.search(pattern1, md_text)
        match2 =  re.search(pattern2, md_text)
        if match1 and match2:
            if match1.start(1) < match2.start(1):
                tag = match1.group(1)
            else:
                tag = match2.group(1)
        elif match1:
            tag = match1.group(1)
        elif match2:
            tag = match2.group(1)
        else:
            # No tags found, copy to root level only
            return [os.path.join(temp_path, filename)]
        tags = [tag]
    paths = [os.path.join(temp_path, filename)]
    for tag in tags:
        if tag == '/':
            continue
        if only_export_these_tags:
            export = False
            for export_tag in only_export_these_tags:
                if tag.lower().startswith(export_tag.lower()):
                    export = True
                    break
            if not export:
                continue
        for no_tag in no_export_tags:
            if tag.lower().startswith(no_tag.lower()):
                return []
        if tag.startswith('.'):
            # Avoid hidden path if it starts with a '.'
            sub_path = '_' + tag[1:]     
        else:
            sub_path = tag    
        tag_path = os.path.join(temp_path, sub_path)
        if not os.path.exists(tag_path):
            os.makedirs(tag_path)
        paths.append(os.path.join(tag_path, filename))      
    return paths


def process_image_links(sentence_dict, filepath): #this file path is md file name, not image
    '''
    Bear image links converted to MD links
    '''
    # root = filepath.replace(temp_path, '')
    # level = len(root.split('/')) - 2
    # parent = '../' * level
    result_sentence = re.sub(r'\[image:(.+?\/.*)\]', image_replacer, sentence_dict['sentence'])
    # TODO: copyright tag operation + operate by iamge name
    if( result_sentence != sentence_dict['sentence']):
        logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
        sentence_dict['sentence'] = result_sentence
        return sentence_dict
    return sentence_dict


def image_replacer(m):
    return "![](/BearImages/" + m.group(1).replace(" ","_").replace("/","_") + ")"

def restore_image_links(md_text):
    '''
    MD image links restored back to Bear links
    '''
    #if not re.search(r'!\[.*?\]\(assets/.+?\)', md_text):
        # No image links in note, return unchanged:
    #    return md_text
    if export_as_textbundles:
        md_text = re.sub(r'!\[(.*?)\]\(assets/(.+?)_(.+?)( ".+?")?\) ?', r'[image:\2/\3]\4 \1', md_text)
    elif export_image_repository :
        # md_text = re.sub(r'\[image:(.+?)\]', r'![](../assets/\1)', md_text)
        md_text = re.sub(r'!\[\]\((\.\./)*BearImages/(.+?)\)', r'[image:\2]', md_text)
    return md_text


def copy_bear_images():
    # Image files copied to a common image repository
    subprocess.call(['rsync', '-r', '-t', '--delete', bear_image_path + "/", assets_path])
    # rsync -rt --deleeditorconfigte /path/asset. This line mean reculsively copy file with timestamp, if there is no source file then delete backup file.
    # 베어의 이미지 에셋에 접근해서 rsync to dest DIR

def write_time_stamp():
    # write to time-stamp.txt file (used during sync)
    write_file(export_ts_file, "Markdown from Bear written at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)
    write_file(sync_ts_file_temp, "Markdown from Bear written at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)


def hide_tags(sentence_dict):
    # Hide tags from being seen as H1, by placing `period+space` at start of line:
    if hide_tags_in_comment_block:
        sentence_dict['sentence'] =  re.sub(r'(\n)[ \t]*(\#[^\s#].*)', r'\1<!-- \2 -->', sentence_dict['sentence'])
    else:
        sentence_dict['sentence'] =  re.sub(r'(\n)[ \t]*(\#[^\s#]+)', r'\1. \2', sentence_dict['sentence'])
    return sentence_dict

def codeblock_tainter(sentence_dict):
    global codeblock_flager
    if is_codeblock_mode:
        is_codeblock =  re.search(r'^\`\`\`.*', sentence_dict['sentence'])
        if( is_codeblock is not None):
            if(codeblock_flager == True):
                codeblock_flager = False
                logger(sentence_dict['sentence'], f" 🎧 CODE block END")
            else :
                codeblock_flager = True
                logger(sentence_dict['sentence'], f" 🧫 CODE block START")
            return sentence_dict
    return sentence_dict

def bold_conv(sentence_dict):
    # replace md *text* to **text**
    if sentence_dict['bold_conv_flag'] == False:
        if is_bold_conv_mode:
            if checkAllowedPattern(sentence_dict):
                result_sentence =  re.sub(r'\*{1}([^\s]?[^\*\n]+[^\s]?)\*{1}', bold_replacer, sentence_dict['sentence'])
                if( result_sentence != sentence_dict['sentence']):
                    logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                    sentence_dict['sentence'] = result_sentence
                    sentence_dict['bold_conv_flag'] = True
                    return sentence_dict
    return sentence_dict


def bold_replacer(m):
    return "**" + m.group(1).strip() + "**"

def separator_conv(sentence_dict):
    # replace md --- to \n---
    if is_sepa_conv_mode:
        result_sentence =  re.sub(r'(\n---|^---)', r'\n\1', sentence_dict['sentence'])
        if( result_sentence != sentence_dict['sentence']):
            logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
            sentence_dict['sentence'] = result_sentence
            return sentence_dict
    return sentence_dict

def italic_conv(sentence_dict):
    # replace md /text/ to *text* 
    if is_italic_conv_mode:
        if checkAllowedPattern(sentence_dict):
            result_sentence =  re.sub(r'\/{1}([^\s*]+)([^/\n]+)([^\s*]+)\/{1}', r'*\1\2\3*', sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
                sentence_dict['italic_conv_flag'] = True
                return sentence_dict
    return sentence_dict

def underline_conv(sentence_dict):
    # replace md
    if is_underline_conv_mode:
        if checkAllowedPattern(sentence_dict):
            result_sentence =  re.sub(r'\_{1}([^\n\_]+)\_{1}', underline_replacer, sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
                sentence_dict['underline_conv_flag'] = True
                return sentence_dict
    return sentence_dict


def underline_replacer(m):
    return "***" +  m.group(1).strip() + "***"

def strike_conv(sentence_dict):
    # replace md
    if is_strike_conv_mode:
        if checkAllowedPattern(sentence_dict):
            result_sentence =  re.sub(r'\-{1}([^\s]+)([^-\n]+)([^\s]+)\-{1}', strike_replacer, sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
                sentence_dict['strike_conv_flag'] = True
                return sentence_dict
    return sentence_dict

def strike_replacer(m):
    return "~~" + m.group(1) + m.group(2) + m.group(3) + "~~"

def checkbox_conv(sentence_dict):
    # replace md
    if checkAllowedPattern(sentence_dict):
        if is_checkbox_conv_mode:
            result_sentence = re.sub(r'^(\+|\-)\s(.*)', checkbox_replacer, sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
                return sentence_dict
    return sentence_dict

def checkbox_replacer(m):
    if m.group(1) == '+':
        return '+\t[x] ' + m.group(2)
    if m.group(1) == '-':
        return '-\t[ ] ' + m.group(2)
    return  m.group(0)

def mark_conv(sentence_dict):
    # replace md
    if is_mark_conv_mode:
        if checkAllowedPattern(sentence_dict):
            result_sentence = re.sub(markRegex, mark_replacer, sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
    return sentence_dict

def mark_replacer(m):
    prefix = ""
    suffix = ""
    if m.group(1) == "":
        prefix = m.group(1)
    else:
        prefix = m.group(1) + "\n"
    if m.group(2) == "":
        print("m.group(2) is empty, unexpected situation")
    if m.group(3) != "":
        suffix = m.group(3) + "\n"
    return prefix + "```diff\n+ " + m.group(2) + "\n```\n" + suffix

#타입 0은 전체문장 1은 공백 또는 메인 문장

def fileLink_conv(sentence_dict):
    # replace md
    if checkAllowedPattern(sentence_dict,"fileLink"):
        if is_fileLink_conv_mode:
            result_sentence =  re.sub(r'\[file\:([0-9A-Z-/]+)\/([\w\d\s]*\.[\w]{3,4})\]', r'[💾\2](https://github.com/HibikeQuantum/PlayGround/blob/master/Bear/files/\1/\2)', sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
                return sentence_dict
    return sentence_dict

def imageLink_conv(sentence_dict):
    # BearImages/C9BC8F82-6A30-4165-B911-55C63AC4718E-76434-0000075928935A8B/Screen Shot 2022-07-03 at 7.47.50.png
    # ![](../BearImages/89C5883A-B535-4FB6-907A-3B29FF56E088-82667-0000032FC3D87CF3/Bear 3 columns.png)
    if checkAllowedPattern(sentence_dict,"imageLink"):
        if is_imageLink_conv_mode:
            result_sentence =  re.sub(imageLinkRegex, r'![\2](images/\1/\2)', sentence_dict['sentence'])
            if( result_sentence != sentence_dict['sentence']):
                logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
                sentence_dict['sentence'] = result_sentence
                return sentence_dict
    return sentence_dict

def checkAllowedPattern(sentence_dict, type="normal"):
    global codeblock_flager
    if codeblock_flager:
        return False
    elif(type == "normal"):
            if re.search(imageLinkRegex, sentence_dict['sentence']) is not None: 
                return False
            if re.search(fileLinkRegex, sentence_dict['sentence']) is not None:
                return False
    return True

#TODO: Add convert function here
# phase 1 - underline, strike, checkbox, mark, file link, image link

def restore_tags(md_text):
    # Tags back to normal Bear tags, stripping the `period+space` at start of line:
    # if hide_tags_in_comment_block:
    md_text =  re.sub(r'(\n)<!--[ \t]*(\#[^\s#].*?) -->', r'\1\2', md_text)
    # else:
    md_text =  re.sub(r'(\n)\.[ \t]*(\#[^\s#]+)', r'\1\2', md_text)
    return md_text


def clean_title(title):
    title = title[:256].strip()
    if title == "":
        title = "Untitled"
    title = re.sub(r'[/\\*?$@!^&\|~:\.]', r'-', title)
    title = re.sub(r'-$', r'', title)    
    return title.strip()


def write_file(filename, file_content, modified):
    with open(filename, "w", encoding='utf-8') as f:
        f.write(file_content)
        logger("[INFO] ",filename, " has been recorded successfully.")
    if modified > 0:
        os.utime(filename, (-1, modified))


def read_file(file_name):
    with open(file_name, "r", encoding='utf-8') as f:
        file_content = f.read()
    return file_content


def get_file_date(filename):
    try:
        t = os.path.getmtime(filename)
        return t
    except:
        return 0


def dt_conv(dtnum):
    # Formula for date offset based on trial and error:
    hour = 3600 # seconds
    year = 365.25 * 24 * hour
    offset = year * 31 + hour * 6
    return dtnum + offset


def date_time_conv(dtnum):
    newnum = dt_conv(dtnum) 
    dtdate = datetime.datetime.fromtimestamp(newnum)
    return dtdate.strftime(' - %Y-%m-%d_%H%M')


def time_stamp_ts(ts):
    dtdate = datetime.datetime.fromtimestamp(ts)
    return dtdate.strftime('%Y-%m-%d at %H:%M') 


def date_conv(dtnum):
    dtdate = datetime.datetime.fromtimestamp(dtnum)
    return dtdate.strftime('%Y-%m-%d')


def delete_old_temp_files():
    # Deletes all files in temp folder before new export using "shutil.rmtree()":
    # NOTE! CAUTION! Do not change this function unless you really know shutil.rmtree() well!
    if os.path.exists(temp_path) and "BearExportTemp" in temp_path:
        # *** NOTE! Double checking that temp_path folder actually contains "BearExportTemp"
        # *** Because if temp_path is accidentally empty or root,
        # *** shutil.rmtree() will delete all files on your complete Hard Drive ;(
        shutil.rmtree(temp_path)
        # *** NOTE: USE rmtree() WITH EXTREME CAUTION!
    os.makedirs(temp_path)


def rsync_files_from_temp():
    # Moves markdown files to new folder using rsync:
    # This is a very important step! 
    # By first exporting all Bear notes to an emptied temp folder,
    # rsync will only update destination if modified or size have changed.
    # So only changed notes will be synced by Dropbox or OneDrive destinations.
    # Rsync will also delete notes on destination if deleted in Bear.
    # So doing it this way saves a lot of otherwise very complex programing.
    # Thank you very much, Rsync! ;)
    for (dest_path, delete) in multi_export:
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        if delete:
            subprocess.call(['rsync', '-r', '-t', '-E', '--delete',
                             '--exclude', 'BearImages/',
                             '--exclude', '.Ulysses*',
                             '--exclude', '*.Ulysses_Public_Filter',
                             temp_path + "/", dest_path])
        else:
            subprocess.call(['rsync', '-r', '-t', '-E',
                            temp_path + "/", dest_path])


def sync_md_updates():
    updates_found = False
    if not os.path.exists(sync_ts_file) or not os.path.exists(export_ts_file):
        return False
    ts_last_sync = os.path.getmtime(sync_ts_file)
    ts_last_export = os.path.getmtime(export_ts_file)
    # Update synced timestamp file:
    update_sync_time_file(0)
    file_types = ('*.md', '*.txt', '*.markdown')
    for (root, dirnames, filenames) in os.walk(export_path): 
        '''
        This step walks down into all sub folders, if any.
        '''
        for pattern in file_types:
            for filename in fnmatch.filter(filenames, pattern):
                md_file = os.path.join(root, filename)
                ts = os.path.getmtime(md_file)
                if ts > ts_last_sync:
                    if not updates_found:  # Yet
                        # Wait 5 sec at first for external files to finish downloading from dropbox.
                        # Otherwise images in textbundles might be missing in import:
                        time.sleep(5)
                    updates_found = True
                    md_text = read_file(md_file)
                    backup_ext_note(md_file)
                    if check_if_image_added(md_text, md_file):
                        textbundle_to_bear(md_text, md_file, ts)
                        write_log('Imported to Bear: ' + md_file)
                    else:
                        update_bear_note(md_text, md_file, ts, ts_last_export)
                        write_log('Bear Note Updated: ' + md_file)
    if updates_found:
        # Give Bear time to process updates:
        time.sleep(3)
        # Check again, just in case new updates synced from remote (OneDrive/Dropbox) 
        # during this process!
        # The logic is not 100% fool proof, but should be close to 99.99%
        sync_md_updates() # Recursive call
    return updates_found


def check_if_image_added(md_text, md_file):
    if not '.textbundle/' in md_file:
        return False
    matches = re.findall(r'!\[.*?\]\(assets/(.+?_).+?\)', md_text)
    for image_match in matches:
        'F89CDA3D-3FCC-4E92-88C1-CC4AF46FA733-10097-00002BBE9F7FF804_IMG_2280.JPG'
        if not re.match(r'[0-9A-F]{8}-([0-9A-F]{4}-){3}[0-9A-F]{12}-[0-9A-F]{3,5}-[0-9A-F]{16}_', image_match):
            return True
    return False        


def textbundle_to_bear(md_text, md_file, mod_dt):
    md_text = restore_tags(md_text)
    bundle = os.path.split(md_file)[0]
    match = re.search(r'\{BearID:(.+?)\}', md_text)
    if match:
        uuid = match.group(1)
        # Remove old BearID: from new note
        md_text = re.sub(r'\<\!-- ?\{BearID\:' + uuid + r'\} ?--\>', '', md_text).rstrip() + '\n'
        md_text = insert_link_top_note(md_text, 'Images added! Link to original note: ', uuid)
    else:
        # New textbundle (with images), add path as tag: 
        md_text = get_tag_from_path(md_text, bundle, export_path)
    write_file(md_file, md_text, mod_dt)
    os.utime(bundle, (-1, mod_dt))
    subprocess.call(['open', '-a', '/applications/bear.app', bundle])
    time.sleep(0.5)


def backup_ext_note(md_file):
    if '.textbundle' in md_file:
        bundle_path = os.path.split(md_file)[0]
        bundle_name = os.path.split(bundle_path)[1]
        target = os.path.join(sync_backup, bundle_name)
        bundle_raw = os.path.splitext(target)[0]
        count = 2
        while os.path.exists(target):
            # Adding sequence number to identical filenames, preventing overwrite:
            target = bundle_raw + " - " + str(count).zfill(2) + ".textbundle"
            count += 1
        shutil.copytree(bundle_path, target)
    else:
        # Overwrite former bacups of incoming changes, only keeps last one:
        shutil.copy2(md_file, sync_backup + '/')


def update_sync_time_file(ts):
    write_file(sync_ts_file,
        "Checked for Markdown updates to sync at: " +
        datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), ts)


def update_bear_note(md_text, md_file, ts, ts_last_export):
    md_text = restore_tags(md_text)
    md_text = restore_image_links(md_text)
    uuid = ''
    match = re.search(r'\{BearID:(.+?)\}', md_text)
    sync_conflict = False
    if match:
        uuid = match.group(1)
        # Remove old BearID: from new note
        md_text = re.sub(r'\<\!-- ?\{BearID\:' + uuid + r'\} ?--\>', '', md_text).rstrip() + '\n'

        sync_conflict = check_sync_conflict(uuid, ts_last_export)
        if sync_conflict:
            link_original = 'bear://x-callback-url/open-note?id=' + uuid
            message = '::Sync conflict! External update: ' + time_stamp_ts(ts) + '::'
            message += '\n[Click here to see original Bear note](' + link_original + ')'
            x_create = 'bear://x-callback-url/create?show_window=no&open_note=no' 
            bear_x_callback(x_create, md_text, message, '')   
        else:
            # Regular external update
            orig_title = backup_bear_note(uuid)
            # message = '::External update: ' + time_stamp_ts(ts) + '::'   
            x_replace = 'bear://x-callback-url/add-text?show_window=no&open_note=no&mode=replace&id=' + uuid
            bear_x_callback(x_replace, md_text, '', orig_title)
            # # Trash old original note:
            # x_trash = 'bear://x-callback-url/trash?show_window=no&id=' + uuid
            # subprocess.call(["open", x_trash])
            # time.sleep(.2)
    else:
        # New external md Note, since no Bear uuid found in text: 
        # message = '::New external Note - ' + time_stamp_ts(ts) + '::' 
        md_text = get_tag_from_path(md_text, md_file, export_path)
        x_create = 'bear://x-callback-url/create?show_window=no' 
        bear_x_callback(x_create, md_text, '', '')
    return


def get_tag_from_path(md_text, md_file, root_path, inbox_for_root=True, extra_tag=''):
    # extra_tag should be passed as '#tag' or '#space tag#'
    path = md_file.replace(root_path, '')[1:]
    sub_path = os.path.split(path)[0]
    tags = []
    if '.textbundle' in sub_path:
        sub_path = os.path.split(sub_path)[0]
    if sub_path == '': 
        if inbox_for_root:
            tag = '#.inbox'
        else:
            tag = ''
    elif sub_path.startswith('_'):
        tag = '#.' + sub_path[1:].strip()
    else:
        tag = '#' + sub_path.strip()
    if ' ' in tag: 
        tag += "#"               
    if tag != '': 
        tags.append(tag)
    if extra_tag != '':
        tags.append(extra_tag)
    for tag in get_file_tags(md_file):
        tag = '#' + tag.strip()
        if ' ' in tag: tag += "#"                   
        tags.append(tag)
    return md_text.strip() + '\n\n' + ' '.join(tags) + '\n'


def get_file_tags(md_file):
    try:
        subprocess.call([gettag_sh, md_file, gettag_txt])
        text = re.sub(r'\\n\d{1,2}', r'', read_file(gettag_txt))
        tag_list = json.loads(text)
        return tag_list
    except:
        return []


def bear_x_callback(x_command, md_text, message, orig_title):
    if message != '':
        lines = md_text.splitlines()
        lines.insert(1, message)
        md_text = '\n'.join(lines)
    if orig_title != '':
        lines = md_text.splitlines()
        title = re.sub(r'^#+ ', r'', lines[0])
        if title != orig_title:
            md_text = '\n'.join(lines)
        else:
            md_text = '\n'.join(lines[1:])        
    x_command_text = x_command + '&text=' + urllib.parse.quote(md_text)
    subprocess.call(["open", "-g", x_command_text])
    time.sleep(.2)


def check_sync_conflict(uuid, ts_last_export):
    conflict = False
    # Check modified date of original note in Bear sqlite db!
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0' AND `ZUNIQUEIDENTIFIER` LIKE '" + uuid + "'"
        c = conn.execute(query)
    for row in c:
        modified = row['ZMODIFICATIONDATE']
        uuid = row['ZUNIQUEIDENTIFIER']
        mod_dt = dt_conv(modified)
        conflict = mod_dt > ts_last_export
    return conflict


def backup_bear_note(uuid):
    # Get single note from Bear sqlite db!
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM `ZSFNOTE` WHERE `ZUNIQUEIDENTIFIER` LIKE '" + uuid + "'"
        c = conn.execute(query)
    title = ''
    for row in c:  # Will only get one row if uuid is found!
        title = row['ZTITLE']
        md_text = row['ZTEXT'].rstrip()
        modified = row['ZMODIFICATIONDATE']
        mod_dt = dt_conv(modified)
        created = row['ZCREATIONDATE']
        cre_dt = dt_conv(created)
        md_text = insert_link_top_note(md_text, 'Link to updated note: ', uuid)
        dtdate = datetime.datetime.fromtimestamp(cre_dt)
        filename = clean_title(title) + dtdate.strftime(' - %Y-%m-%d_%H%M')
        if not os.path.exists(sync_backup):
            os.makedirs(sync_backup)
        file_part = os.path.join(sync_backup, filename) 
        # This is a Bear text file, not exactly markdown.
        backup_file = file_part + ".txt"
        count = 2
        while os.path.exists(backup_file):
            # Adding sequence number to identical filenames, preventing overwrite:
            backup_file = file_part + " - " + str(count).zfill(2) + ".txt"
            count += 1
        write_file(backup_file, md_text, mod_dt)
        filename2 = os.path.split(backup_file)[1]
        write_log('Original to sync_backup: ' + filename2)
    return title


def insert_link_top_note(md_text, message, uuid):
    lines = md_text.split('\n')
    title = re.sub(r'^#{1,6} ', r'', lines[0])
    link = '::' + message + '[' + title + '](bear://x-callback-url/open-note?id=' + uuid + ')::'        
    lines.insert(1, link) 
    return '\n'.join(lines)


def init_gettag_script():
    gettag_script = \
    '''#!/bin/bash
    if [[ ! -e $1 ]] ; then
    echo 'file missing or not specified'
    exit 0
    fi
    JSON="$(xattr -p com.apple.metadata:_kMDItemUserTags "$1" | xxd -r -p | plutil -convert json - -o -)"
    echo $JSON > "$2"
    '''
    temp = os.path.join(HOME, 'temp')
    if not os.path.exists(temp):
        os.makedirs(temp)
    write_file(gettag_sh, gettag_script, 0)
    subprocess.call(['chmod', '777', gettag_sh])
    

def notify(message):
    title = "ul_sync_md.py"
    try:
        # Uses "terminal-notifier", download at:
        # https://github.com/julienXX/terminal-notifier/releases/download/2.0.0/terminal-notifier-2.0.0.zip
        # Only works with MacOS 10.11+
        subprocess.call(['/Applications/terminal-notifier.app/Contents/MacOS/terminal-notifier',
                         '-message', message, "-title", title, '-sound', 'default'])
    except:
        write_log('"terminal-notifier.app" is missing!')        
    return


def logger(*args):
    if (debug_mode_level_middle==True):
        string = ""
        for arg in args:
            string += arg
        print(string)

    if (debug_mode==True):
        for arg in args:
            print("TYPE: ",type(arg),"VALUE:", arg, sys._getframe(2).f_code.co_name)

def logger2(*args):
    if (debug_mode_level_middle==False):
        string = ""
        for arg in args:
            string += arg
        print(string)

    if (debug_mode==True):
        for arg in args:
            print("TYPE: ",type(arg),"VALUE:", arg, sys._getframe(2).f_code.co_name)

if __name__ == '__main__':
    main()
