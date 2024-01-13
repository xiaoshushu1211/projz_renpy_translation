# coding=utf8
# Copyright 2004-2021 Tom Rothamel <pytom@bishoujo.us>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This file is modified by https://github.com/abse4411
###########################################################
# ________  ________  ________        ___  ________       #
# |\   __  \|\   __  \|\   __  \      |\  \|\_____  \     #
# \ \  \|\  \ \  \|\  \ \  \|\  \     \ \  \\|___/  /|    #
#  \ \   ____\ \   _  _\ \  \\\  \  __ \ \  \   /  / /    #
#   \ \  \___|\ \  \\  \\ \  \\\  \|\  \\_\  \ /  /_/__   #
#    \ \__\    \ \__\\ _\\ \_______\ \________\\________\ #
#     \|__|     \|__|\|__|\|_______|\|________|\|_______| #
#                                                         #
#  projz_renpy_translation                                #
#  https://github.com/abse4411/projz_renpy_translation)   #
###########################################################
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals

import os
import shutil
import time

from renpy.compat import *

import renpy.translation
import json
import collections
from renpy.translation import quote_unicode
from renpy.parser import elide_filename
from renpy.translation.generation import translate_list_files, translation_filename, shorten_filename, rot13_filter, \
    piglatin_filter, null_filter, open_tl_file, close_tl_files

# new features of RenPy 8
is_empty_extend_impl = None
TranslateSay_ref = None
try:
    TranslateSay_ref = renpy.ast.TranslateSay
except Exception as e:
    pass
try:
    from renpy.translation.generation import is_empty_extend as is_empty_extend_impl_

    is_empty_extend_impl = is_empty_extend_impl_
except Exception as e:
    pass


def is_empty_extend(t):
    """
    Reture true if the translation is an empty extend.
    """
    if TranslateSay_ref is not None and isinstance(t, TranslateSay_ref):
        block = [t]
    else:
        block = t.block
    if is_empty_extend_impl is not None:
        return is_empty_extend_impl(t)
    return False


projz_banner = u'''###########################################################
#  ________  ________  ________        ___  ________      #
# |\   __  \|\   __  \|\   __  \      |\  \|\_____  \     #
# \ \  \|\  \ \  \|\  \ \  \|\  \     \ \  \\\\|___/  /|    #
#  \ \   ____\ \   _  _\ \  \\\\\  \  __ \ \  \   /  / /    #
#   \ \  \___|\ \  \\\\  \\\\ \  \\\\\  \|\  \\\\_\  \ /  /_/__   #
#    \ \__\    \ \__\\\\ _\\\\ \_______\ \________\\\\________\\ #
#     \|__|     \|__|\|__|\|_______|\|________|\|_______| #
#                                                         #
#  This ryp file is generated by the project:             #
#  https://github.com/abse4411/projz_renpy_translation    #
###########################################################'''
def ast_of(
        identifier=None,
        language=None,
        filename=None,
        linenumber=None,
        block=None
):
    return {
        'identifier': identifier,
        'language': language,
        'filename': filename,
        'linenumber': linenumber,
        'block': block if block is not None else [],
    }

def block_of(
        type=None,
        what=None,
        who=None,
        code=None,
        new_code=None,
):
    return {
        'type': type,
        'what': what,
        'who': who,
        'code': code,
        'new_code': new_code,
    }


def get_text(t):
    if t is not None:
        for i in t.block:
            if isinstance(i, renpy.ast.Say):
                return i.what
    return None

def is_say_statement(t):
    if isinstance(t, renpy.ast.Say):
        return True
    return False


def get_dialogues_info(t, filter):
    if is_say_statement(t):
        return t.what, t.who, t.get_code(filter), type(t).__name__
    return None, None, t.get_code(filter), type(t).__name__

def get_string_info(s, filter):
    old = s.text
    new = filter(s.text)
    return old, new, type(s).__name__

written_files = set()
def open_tl_file_wrapper(fn):
    written_files.add(fn)
    return open_tl_file(fn)

def close_tl_files_wrapper():
    global written_files
    global projz_banner
    for f in written_files:
        open_tl_file(f).write(u'\n'+projz_banner+u'\n')
    close_tl_files()



def count_missing(language, filter, min_priority, max_priority, common_only, say_only):
    """
    Prints a count of missing translations for `language`.
    """

    translator = renpy.game.script.translator

    missing_translates = 0

    missing_items = []
    for filename in translate_list_files():
        for _, t in translator.file_translates[filename]:
            if is_empty_extend(t):
                continue
            if (t.identifier, language) not in translator.language_translates and (
                    hasattr(t, "alternate") and (t.alternate, language) not in translator.language_translates):
                missing_translates += 1
                ast = ast_of(
                    identifier=t.identifier.replace('.', '_'),
                    language=language,
                    filename=t.filename,
                    linenumber=t.linenumber,
                )
                for i, n in enumerate(t.block):
                    if say_only and not is_say_statement(n):
                        continue
                    what, who, code, type = get_dialogues_info(n, filter)
                    ast['block'].append(block_of(
                        type=type,
                        what=what,
                        who=who,
                        code=code,
                    ))
                if ast.get('block', False):
                    missing_items.append(ast)

    missing_strings = 0

    stl = renpy.game.script.translator.strings[language]  # @UndefinedVariable

    strings = renpy.translation.scanstrings.scan(min_priority, max_priority, common_only)

    missing_strings_items = []
    for s in strings:

        tlfn = translation_filename(s)

        if tlfn is None:
            continue

        if s.text in stl.translations:
            continue

        missing_strings += 1
        old, new, type = get_string_info(s, filter)
        missing_strings_items.append(ast_of(
            identifier=old,
            language=language,
            block=[block_of(
                type=type,
                what=new,
            )],
            filename=elide_filename(s.filename),
            linenumber=s.line,
        ))

    message = "{}: {} missing dialogue translations, {} missing string translations.".format(
        language,
        missing_translates,
        missing_strings
    )
    return message, {
        'dialogues': missing_items,
        'strings': missing_strings_items,
    }

# def get_ast_code(n, filter, new_t):
#     if new_t is not None:
#         for i in new_t.block:
#             print(i.get_code(filter), i.linenumber, n.linenumber, n.get_code(filter))
#             if not isinstance(i, renpy.ast.Say) and n.linenumber == i.linenumber:
#                 return i.get_code(filter)
#     return None

def get_translation(filename, language, filter, translated_only, say_only):
    fn, common = shorten_filename(filename)

    # The common directory should not have dialogue in it.
    if common:
        return []

    if language == "None":
        language = None

    translator = renpy.game.script.translator

    item_list = []
    for label, t in translator.file_translates[filename]:
        if is_empty_extend(t):
            continue
        origin_identifier = t.identifier
        identifier = origin_identifier.replace('.', '_')
        if translated_only:
            if (t.identifier, language) not in translator.language_translates:
                if hasattr(t, "alternate"):
                    origin_identifier = identifier = t.alternate
                    if (t.alternate, language) not in translator.language_translates:
                        continue
                else:
                    continue
        ast = ast_of(
            identifier=identifier,
            language=language,
            filename=t.filename,
            linenumber=t.linenumber,
        )

        if (origin_identifier, language) in translator.language_translates:
            t = translator.language_translates.get((origin_identifier, language))
            if TranslateSay_ref is not None and isinstance(t, TranslateSay_ref):
                block = [t]
            else:
                block = t.block
            for i, n in enumerate(block):
                if say_only and not is_say_statement(n):
                    continue
                what, who, code, type = get_dialogues_info(n, filter)
                if is_say_statement(n):
                    new_code = what
                else:
                    new_code = code
                ast['block'].append(block_of(
                    type=type,
                    code=code,
                    who=who,
                    new_code=new_code
                ))
        else:
            if TranslateSay_ref is not None and isinstance(t, TranslateSay_ref):
                block = [t]
            else:
                block = t.block
            for i, n in enumerate(block):
                if say_only and not is_say_statement(n):
                    continue
                what, who, code, type = get_dialogues_info(n, filter)
                ast['block'].append(block_of(
                    type=type,
                    what=what,
                    who=who,
                    code=code,
                ))
        if ast.get('block', False):
            item_list.append(ast)
    return item_list


def get_string_translation(language, filter, min_priority, max_priority, common_only, translated_only):
    """
    get strings to a list
    """
    if language == "None":
        stl = renpy.game.script.translator.strings[None]  # @UndefinedVariable
    else:
        stl = renpy.game.script.translator.strings[language]  # @UndefinedVariable

    # If this function changes, count_missing may also need to
    # change.

    strings = renpy.translation.scanstrings.scan(min_priority, max_priority, common_only)

    stringfiles = collections.defaultdict(list)

    for s in strings:

        tlfn = translation_filename(s)

        if tlfn is None:
            continue

        if translated_only:
            # Unseen.
            if s.text not in stl.translations:
                continue

        if language == "None" and tlfn == "common.rpy":
            tlfn = "common.rpym"

        stringfiles[tlfn].append(s)

    item_list = []
    for tlfn, sl in stringfiles.items():
        for s in sl:
            identifier, old, type = get_string_info(s, filter)
            new = stl.translations.get(s.text, None)

            item_list.append(ast_of(
                identifier=identifier,
                language=language,
                block=[block_of(
                    type=type,
                    what=old,
                    new_code=new
                )],
                filename=elide_filename(s.filename),
                linenumber=s.line,
            ))
    return item_list


def get_ast_say(t):
    if t is not None:
        for i in t.block:
            if isinstance(i, renpy.ast.Say):
                return i
    return None

def get_say_text(t):
    if t is not None:
        for i in t['block']:
            if 'Say' in i['type']:
                return i.get('new_code', i.get('what', None))
    return None


def generate_translation(projz_translator, filename, language, filter, translated_only, say_only):
    fn, common = shorten_filename(filename)

    # The common directory should not have dialogue in it.
    if common:
        return { }

    tl_filename = os.path.join(renpy.config.gamedir, renpy.config.tl_directory, language, fn)

    if language == "None":
        language = None

    if tl_filename[-1] == "m":
        tl_filename = tl_filename[:-1]

    translator = renpy.game.script.translator

    missing_count = 0
    usage_count = 0
    for label, t in translator.file_translates[filename]:
        if is_empty_extend(t):
            continue
        # skip translated texts in rpy files
        if (t.identifier, language) in translator.language_translates:
            continue
        identifier = t.identifier.replace('.', '_')
        if (t.identifier, language) not in projz_translator:
            if hasattr(t, "alternate"):
                # skip translated texts in rpy files
                if (t.alternate, language) in translator.language_translates:
                    continue
                identifier = t.alternate
                if (identifier, language) not in projz_translator:
                    missing_count += 1
                    if translated_only:
                        continue
                else:
                    usage_count += 1
        else:
            usage_count += 1
        f = open_tl_file_wrapper(tl_filename)

        f.write(u"# {}:{}\n".format(t.filename, t.linenumber))
        f.write(u"translate {} {}:\n".format(language, t.identifier.replace('.', '_')))
        f.write(u"\n")

        if TranslateSay_ref is not None and isinstance(t, TranslateSay_ref):
            block = [t]
        else:
            block = t.block

        for n in block:
            f.write(u"    # " + n.get_code() + "\n")

        if not say_only and (identifier, language) in projz_translator:
            for i, n in enumerate(projz_translator[(identifier, language)]['block']):
                if 'Say' not in n['type']:
                    new_code = n.get('new_code', n.get('code', None))
                    if new_code is not None:
                        new_code = new_code.strip()
                        f.write(u"    " + new_code + "\n")
                else:
                    new_text = n.get('new_code', n.get('what', None))
                    if new_text is not None:
                        n = get_ast_say(t)
                        if n is not None:
                            n.what = new_text
                            f.write(u"    " + n.get_code(filter) + "\n")
        else:
            for i, n in enumerate(block):
                if is_say_statement(n):
                    new_text = get_say_text(projz_translator.get((identifier, language), None))
                    if new_text is not None:
                        n.what = new_text

                f.write(u"    " + n.get_code(filter) + "\n")

        f.write(u"\n")
    return {
        'missing_count':missing_count,
        'usage_count':usage_count
    }

def get_string_text(t):
    if t is not None:
        for i in t['block']:
            if i['type'] == 'String':
                return i.get('new_code', None)
    return None

def generate_string_translation(projz_translator, language, filter, min_priority, max_priority, common_only, translated_only): # @ReservedAssignment
    """
    Writes strings to the file.
    """

    if language == "None":
        nullable_language = None
        stl = renpy.game.script.translator.strings[None]  # @UndefinedVariable
    else:
        stl = renpy.game.script.translator.strings[language]  # @UndefinedVariable
        nullable_language = language

    # If this function changes, count_missing may also need to
    # change.

    strings = renpy.translation.scanstrings.scan(min_priority, max_priority, common_only)

    stringfiles = collections.defaultdict(list)

    missing_count = 0
    usage_count = 0
    for s in strings:

        tlfn = translation_filename(s)

        if tlfn is None:
            continue

        # Already seen.
        if s.text in stl.translations:
            continue
        # Unseen.
        if (s.text, nullable_language) not in projz_translator:
            missing_count += 1
            if translated_only:
                continue

        if language == "None" and tlfn == "common.rpy":
            tlfn = "common.rpym"

        stringfiles[tlfn].append(s)


    for tlfn, sl in stringfiles.items():
        tlfn = os.path.join(renpy.config.gamedir, renpy.config.tl_directory, language, tlfn)
        f = open_tl_file_wrapper(tlfn)

        f.write(u"translate {} strings:\n".format(language))
        f.write(u"\n")

        for s in sl:
            old, new, _ = get_string_info(s, filter)
            new_text = get_string_text(projz_translator.get((old, nullable_language), None))
            if new_text is not None:
                usage_count += 1
            else:
                new_text = new

            f.write(u"    # {}:{}\n".format(elide_filename(s.filename), s.line))
            f.write(u"    old \"{}\"\n".format(quote_unicode(old)))
            f.write(u"    new \"{}\"\n".format(quote_unicode(new_text)))
            f.write(u"\n")

    return {
        'missing_count': missing_count,
        'usage_count': usage_count
    }

def generate(filter, max_priority):
    global proj_args

    json_data = read_json()
    dialogues_translator = {(i['identifier'], i['language']): i for i in json_data['items']['dialogues']}
    string_translator = {(i['identifier'], i['language']): i for i in json_data['items']['strings']}
    # print(dialogues_translator)
    # print(string_translator)

    dialogues_count = collections.defaultdict(int)
    string_count = collections.defaultdict(int)
    if not proj_args.strings_only:
        for filename in translate_list_files():
            res = generate_translation(dialogues_translator, filename, proj_args.language, filter, proj_args.translated_only, proj_args.say_only)
            for k, v in res.items():
                dialogues_count[k] += v

    res = generate_string_translation(string_translator, proj_args.language, filter, proj_args.min_priority, max_priority, proj_args.common_only, proj_args.translated_only)
    for k, v in res.items():
        string_count[k] += v

    close_tl_files_wrapper()

    if renpy.config.translate_launcher and (not proj_args.strings_only):
        src = os.path.join(renpy.config.renpy_base, "gui", "game", "script.rpy")
        dst = os.path.join(renpy.config.gamedir, "tl", proj_args.language, "script.rpym")

        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy(src, dst)

    return '{}: dialogue translation: using {} and missing {}, string translation: using {} and missing {}'.format(
        proj_args.language, dialogues_count['usage_count'], dialogues_count['missing_count'],
        string_count['usage_count'], string_count['missing_count'])

def read_json():
    global proj_args
    with open(proj_args.file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        if json_data['uuid'] != proj_args.uuid:
            raise ValueError('Expect uuid:{}, got {}'.format(proj_args.uuid, json_data['uuid']))
    return json_data


def write_json(items=None, message=None, ok=None):
    global proj_args
    with open(proj_args.file, 'w', encoding='utf-8') as f:

        f.write(json.dumps({
            'uuid': proj_args.uuid,
            'game_info':{
                'game_name': renpy.config.name,
                'game_version': renpy.config.version,
                'renpy_version': renpy.version,
            },
            'args': str(proj_args),
            'timestamp': time.time(),
            'items': items,
            'message': message,
            'ok': ok
        }, ensure_ascii=False, indent=2))


proj_args = None


def projz_inject_command():
    """
    The injection command. When called from the command line, this
    injects our code for extracting translations.
    """

    ap = renpy.arguments.ArgumentParser(description="Injection for extracting translations.")
    ap.add_argument("file", help="Json file to save")
    ap.add_argument("--uuid", help="The uuid to identify the json file generated by our code", required=True)
    ap.add_argument("--test-only", help="Test this command without doing anything", dest="test_only", action="store_true")
    ap.add_argument("--say-only", help="Only search or write Say statements for dialogues.", dest="say_only", action="store_true")
    ap.add_argument("--translated-only", help="Only search or write translated texts.",
                    dest="translated_only", action="store_true")
    ap.add_argument("--language", help="The language to generate translations for.", default="None")
    ap.add_argument("--rot13", help="Apply rot13 while generating translations.", dest="rot13", action="store_true")
    ap.add_argument("--piglatin", help="Apply pig latin while generating translations.", dest="piglatin",
                    action="store_true")
    ap.add_argument("--count", help="Instead of generating files, print a count of missing translations.", dest="count",
                    action="store_true")
    ap.add_argument("--generate", help="Generate translations with given input file.", dest="generate",
                    action="store_true")
    ap.add_argument("--min-priority", help="Translate strings with more than this priority.", dest="min_priority",
                    default=0, type=int)
    ap.add_argument("--max-priority", help="Translate strings with more than this priority.", dest="max_priority",
                    default=0, type=int)
    ap.add_argument("--strings-only", help="Only translate strings (not dialogue).", dest="strings_only", default=False,
                    action="store_true")
    ap.add_argument("--common-only", help="Only translate string from the common code.", dest="common_only",
                    default=False, action="store_true")

    args = ap.parse_args()

    global proj_args
    proj_args = args

    if args.language == "rot13":
        args.rot13 = True
    elif args.language == "piglatin":
        args.piglatin = True

    if args.test_only:
        write_json(ok=True)
        return False

    if renpy.config.translate_launcher:
        max_priority = args.max_priority or 499
    else:
        max_priority = args.max_priority or 299

    if args.rot13:
        filter = rot13_filter  # @ReservedAssignment
    elif args.piglatin:
        filter = piglatin_filter  # @ReservedAssignment
    else:
        filter = null_filter  # @ReservedAssignment

    if args.count:
        msg, res = count_missing(args.language, filter, args.min_priority, max_priority, args.common_only, args.say_only)
        write_json(res, msg, True)
        return False

    if args.generate:
        msg = generate(filter, max_priority)
        write_json(list(written_files), message=msg, ok=True)
    else:
        dialogues = []
        if not args.strings_only:
            for filename in translate_list_files():
                dialogues += get_translation(filename, args.language, filter, args.translated_only, args.say_only)
        strings = get_string_translation(args.language, filter, args.min_priority, max_priority,
                                         args.common_only, args.translated_only)
        write_json(
            {'dialogues': dialogues, 'strings': strings},
            '{}: {} dialogue translations and {} string translations found'.format(args.language, len(dialogues),
                                                                                      len(strings)),
            True)
    return False


renpy.arguments.register_command('projz_inject_command', projz_inject_command)
