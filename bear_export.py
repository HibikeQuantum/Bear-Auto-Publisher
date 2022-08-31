# encoding=utf-8
# python3.6
# bear_export_sync.py
# Developed with Visual Studio Code with MS Python Extension.

'''
# Markdown export from Bear sqlite database
Version 2.0, 2022-08-31
modified by: github/HibikeQuantum, Hibike_Quantum@twitter
original author: github/rovest, rorves@twitter

See also: bear_import.py for auto import MD file to bear Note.

'''
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

p = os.path.abspath('.')
sys.path.insert(1, p)

parser = argparse.ArgumentParser(description="Sync Bear notes")
parser.add_argument("--images", default=None, help="Path where images will be stored")
parser.add_argument("--excludeTag", action="append", default=[], help="Don't export notes with this tag. Can be used multiple times.")
parser.add_argument("--noImage", action="append", default=[], help="Don't export image with this tag. Can be used multiple times.")
parser.add_argument("--allowTag", action="append", default=[], help="Don't export image with this tag. Can be used multiple times.")
parser.add_argument("--devMode", action="store_const", const=True, default=False, help="If devmode, program Print detail operation status. and program only update documents that has #test tag")

parsed_args = vars(parser.parse_args())

set_logging_on = True

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

temp_path = os.path.join(HOME, 'Temp', 'BearExportTemp')  # NOTE! Do not change the "BearExportTemp" folder name!!!
bear_db = os.path.join(HOME, 'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite')
log_file = os.path.join(temp_path, 'bear_export_sync_log.txt')

# Paths used in image exports:
bear_image_path = os.path.join(HOME, 'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Images')
assets_path = parsed_args.get("images") if parsed_args.get("images") else os.path.join(export_path, 'BearImages')
# --images 받은 인자가 있으면 그걸 받고 없으면 default export 디렉토리의 BearImages를 참조하게 한다.

fileLinkRegex = r'\[file\:([0-9A-Z-/]+)\/(.+\.[\w]{3,20})\]'
imageLinkRegex = r'\[image\:([-_+~/\w\d\s]+)\/(.+\.[\w]{3,20})\]$'
markRegex = r'(.*)\:\:([^\s]+.*[^\s]+)\:\:(.*)'
tagRegex1 = r'(?<!\S)\#([.\w\/\-]+)[ \n]?(?!([\/ \w]+\w[#]))'
tagRegex2 = r'(?<![\S])\#([^ \d][.\w\/ ]+?)\#([ \n]|$)'


def main():
    initialize_working_data()
    delete_old_temp_files()
    export_tags()
    note_count = export_markdown()

    # move secret .md to /secret folder
    write_working_data()
    write_log(str(note_count) + ' notes exported to: ' + export_path)
    exit(0)


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
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        message = message.replace(export_path + '/', '')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(time_stamp + ': ' + message + '\n')


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


def make_iamge(md_text):
    matches = re.findall(r'\[image:(.+?)\]', md_text)
    if matches is not None:
        for match in matches:
            image_name = match
            new_name = image_name.replace('/', '_') #여기 언더바를 넣는 로직이 있어서 내가 만든 함수랑 겹쳐서 꼬이는구나
            new_name2 = new_name.replace(' ', '_')
            source = os.path.join(bear_image_path, image_name)
            target = os.path.join(assets_path, new_name2)
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


def process_image_links(sentence_dict, filepath): #this file path is md file name, not image
    '''
    Bear image links converted to MD links
    '''
    # root = filepath.replace(temp_path, '')
    # level = len(root.split('/')) - 2
    # parent = '../' * level
    result_sentence = re.sub(r'\[image:(.+?\/.*)\]', image_replacer, sentence_dict['sentence'])
    # TODO: IF document has copyright tag. Image should not upload github and link fommat should be chnaged to "COPYRIGHT IMAGE"
    if( result_sentence != sentence_dict['sentence']):
        logger(sentence_dict['sentence'], "👉 Changed 👉", result_sentence)
        sentence_dict['sentence'] = result_sentence
        return sentence_dict
    return sentence_dict


def image_replacer(m):
    return "![](/BearImages/" + m.group(1).replace(" ","_").replace("/","_") + ")"


def copy_bear_images():
    # Image files copied to a common image repository
    subprocess.call(['rsync', '-r', '-t', '--delete', bear_image_path + "/", assets_path])
    # rsync -rt --deleeditorconfigte /path/asset. This line mean reculsively copy file with timestamp, if there is no source file then delete backup file.
    # 베어의 이미지 에셋에 접근해서 rsync to dest DIR


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

# NOTE! m.group(n) - index 0 has all strings, index 1,2,3,4 .. has group string splited by regex
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


def logger(*args):
    if (debug_mode_level_middle==True):
        string = ""
        for arg in args:
            string += arg
        print(string)
        write_log(string)

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
