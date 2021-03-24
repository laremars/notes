from argparse import ArgumentParser
from datetime import datetime
from getpass import getuser
from os import makedirs, path, startfile
from re import finditer, match
from shutil import copy2

import colorama

colorama.init(convert=True)  # windows specific?

THIS_DIR = path.dirname(path.abspath(__file__))

INIT_FILE = r"{}\notes_init.ini".format(THIS_DIR)
REDUNDANCY_PATH = r"{}\redundancy.txt".format(THIS_DIR)

version = 0.3


def ensure_redundancy(path_redundant, path_notes):
    if path.isfile(
        path_redundant
    ):  # keep a note archive file in case something happens to main notes file
        with open(path_redundant, "r") as f:
            redundant_lines = f.readlines()
    else:
        redundant_lines = []
    if path.isfile(path_notes):
        with open(path_notes, "r") as f:
            these_lines = f.readlines()
    else:
        these_lines = []
    for this_line in these_lines:
        for redundant_line in redundant_lines:
            if this_line.split("--")[0] in redundant_line:
                break
        else:
            redundant_lines.append(this_line)
    with open(path_redundant, "w") as f:
        f.writelines(redundant_lines)


def get_attr_by_flag(args, d, flag_key):
    for flag in d.get(flag_key, []):
        if flag.strip() in dir(args):
            this_flag = flag.strip()
            break
    else:
        print("attribute note found")
        return None
    return getattr(args, this_flag)


def main():
    # print(path.dirname(path.abspath(__file__)))
    d, args = process_init()

    user_file_path = get_attr_by_flag(args, d, "default_defaultfile_flags")
    default_file_path = get_attr_by_flag(args, d, "default_changefilename_flags")
    open_default_file = get_attr_by_flag(args, d, "default_open_flags")
    initiate_loop = get_attr_by_flag(args, d, "default_loop_flags")
    topics = get_attr_by_flag(
        args, d, "default_topic_flags"
    )  # could be None or list of passed in topics
    # print(dir(args))
    this_version = getattr(args, "version")

    ensure_redundancy(REDUNDANCY_PATH, default_file_path)

    if open_default_file is True:  ##launch default file
        if path.isfile(d.get("default_file")):
            print("Opening {}".format(d.get("default_file")))
            startfile("{}".format(d.get("default_file")))
        else:
            print(f'{d.get("default_file")} not found.')
        return

    if this_version is True:  ##display version for user
        print("Notes > Memory, version:{}".format(version))
        return

    if (user_file_path) != d[
        "default_file"
    ]:  ##user changing defaultfile; update INIT_FILE
        with open(INIT_FILE, "r") as f:
            lines = f.readlines()
        new_INIT_FILE = [
            i
            if "default_file" not in i
            else "default_file={}\n".format((user_file_path))
            for i in lines
        ]

        try:
            copy2(
                INIT_FILE,
                path.join(
                    path.split(INIT_FILE)[0], f"COPY - {path.split(INIT_FILE)[1]}"
                ),
            )
        except FileNotFoundError:
            print(f"Creating {INIT_FILE}")

        with open(INIT_FILE, "w") as f:
            f.writelines(new_INIT_FILE)

        print("Default file changed to {}".format(user_file_path))
        return

    if initiate_loop is True:  ##user entering note-taking loop
        process_loop(args, init_dict=d)
        return

    if (
        getattr(args, d.get("default_note_flags")[-1].strip())
    ) is None:  ##no note means user wants note output
        try:
            with open((default_file_path), "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(
                f"\n\tNo such file or directory: {(default_file_path)}\n\t>>Add notes to file before using topic tag."
            )
            return

        if topics is None:
            output_limiter = 5
            for i, line in enumerate(lines):
                if i != 0 and i % output_limiter == 0:
                    user_input = input(
                        "\nEnter to continue (e to exit loop, b to end run)\n"
                    )
                    if user_input == "e":
                        output_limiter = 1000
                    if user_input == "b":
                        break
                process_line(line, d)
            return
        for topic in topics:
            print(topic)
            if topic in ["ALL", "SHOW", "HELP", "TOPICS"]:
                topics.remove(topic)
                ticker_set = set()
                for i, line in enumerate(lines):
                    mat = match(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}--(.*?):", line)
                    group = mat.group(1)
                    if len(group) > 0:
                        ticker_set.add(group.upper())
                print(
                    "\n  Current Topics in {}".format(default_file_path)
                    + colorama.Fore.MAGENTA
                    + ":\n\t{}".format("\n\t".join(list(ticker_set)))
                )
        # if topics[0] in ['ALL', 'SHOW', 'HELP', 'TOPICS']:
        #     ticker_set = set()
        #     for i, line in enumerate(lines):
        #         mat = match(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}--(.*?):', line)
        #         group = mat.group(1)
        #         if len(group) > 0:
        #             ticker_set.add(group.upper())
        #     print('\n  Current Topics in {}'.format(default_file_path) + colorama.Fore.MAGENTA   + ':\n\t{}'.format("\n\t".join(list(ticker_set))))
        # return

        for i, line in enumerate(lines):
            if sum([1 for t in topics if t in line.split("::")[0]]) > 0:
                process_line(line, d)
        return

    note_str = " ".join(
        (getattr(args, d.get("default_note_flags")[-1].strip()))
    )  ##(getattr(args, d.get("default_note_flags")[-1].strip())) comes in as a list; convert to string

    try:  ##read current notes file content
        with open((default_file_path), "r") as f:
            string = f.read()
    except FileNotFoundError:
        string = ""

    try:  ##redundancy to preserve notes
        copy2((default_file_path), f"COPY - {(default_file_path)}")
    except FileNotFoundError:
        print(f"Creating {(default_file_path)}")
    for topic in topics:
        if topic in ["ALL", "SHOW", "HELP", "TOPICS"]:
            topics.remove(topic)
            ticker_set = set()
            try:
                with open((default_file_path), "r") as f:
                    lines = f.readlines()
            except FileNotFoundError:
                print(
                    f"\n\tNo such file or directory: {(default_file_path)}\n\t>>Add notes to file before using topic tag."
                )
            for i, line in enumerate(lines):
                mat = match(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}--(.*?):", line)
                group = mat.group(1)
                if len(group) > 0:
                    ticker_set.add(group.upper())
            print(
                "\n  Current Topics in {}:".format(default_file_path)
                + colorama.Fore.MAGENTA
                + "\n\t{}".format("\n\t".join(list(ticker_set)))
                + colorama.Fore.WHITE
            )
    with open(
        (default_file_path), "w"
    ) as f:  # if we got this far, we want to write notes to file
        this_note = (
            str(datetime.today())[:19] + "--misc::" + note_str
            if topics is None
            else str(datetime.today())[:19] + "--" + ", ".join(topics) + "::" + note_str
        )
        if topics is None:
            f.write(this_note + "\n" + string)
        else:
            f.write(this_note + "\n" + string)
    process_line(this_note, d)


def process_line(line, d):
    line = line.replace(r"\;", r"~~")
    fmtline1 = "--Categories: ".join(line.strip().split("--"))
    fmtline2 = [fmtline1.split("::")[0].upper()] + [
        i.strip()
        for i in fmtline1.split("::")[1].split(d.get("default_linebreak", ";"))
    ]
    fmtline2 = [i.replace("~~", ";") for i in fmtline2]
    print(colorama.Back.BLACK, end="")  ##print it pretty

    styles_path = path.join(THIS_DIR, "styles.ini")

    if path.isfile(styles_path):
        with open(styles_path, "r") as f:
            contents = f.readlines()
        styles_list = [
            i.split("=")
            for i in contents
            if not i.startswith(";") and len(i.strip()) > 0
        ]  # ; is a comment in ini file
        styles = {i[0].upper(): i[1].strip() for i in styles_list}

    else:
        styles = {}
        contents = []
    for l in fmtline2:
        if "--CATEGORIES" in l:
            print(colorama.Fore.CYAN + f'\n {l.split("--")[0]}' + colorama.Fore.WHITE)
            print(
                colorama.Fore.MAGENTA
                + f'  {l.split("--")[1][:11]}'
                + colorama.Fore.WHITE
            )
            cats = l.split("--")[1][11:].strip()
            split_char = "," if "," in cats else " "
            cats = cats.split(split_char)
            cats = [i.strip().upper() for i in cats]
            for i, cat in enumerate(cats):
                if cat.upper().strip() not in styles.keys():
                    styles[cat.upper().strip()] = "<FORE-fffb00>"
                if i % 4 == 0 and i != 0:
                    nlc = "\n"
                elif i == len(l.split("--")[1][11:].split(",")) - 1:
                    nlc = "\n"
                else:
                    nlc = ","
                print(f"   {cat}", end=nlc)
            print(colorama.Fore.MAGENTA + "  NOTES:" + colorama.Fore.WHITE)
        else:
            if len(l) != 0:  # empty lines not wanted
                line_list = l.lower().split()
                for i, item in enumerate(line_list):
                    if "+" in item and ">" not in item:
                        line_list[i] = f"<FORE-hhhhhh>{item}<RESET>"

                for kw in styles:
                    # indexes = [m.start() for m in finditer(kw.lower(), l.lower())]

                    if kw.lower() in l.lower().split():

                        indexes = [
                            i for i, item in enumerate(line_list) if item == kw.lower()
                        ]  # all occurances in list
                        for index in indexes:
                            line_list[
                                index
                            ] = f"{styles[kw]}{kw}<RESET>"  # replace with formatting
                l = " ".join(line_list)  # now we have our formatted string

                l = (
                    l.replace("<FORE-fffb00>", colorama.Fore.YELLOW)
                    .replace("<FORE-3afa00>", colorama.Fore.GREEN)
                    .replace("<FORE-ff0000>", colorama.Fore.RED)
                    .replace("<FORE-78ddff>", colorama.Fore.CYAN)
                    .replace("<FORE-00bfff>", colorama.Fore.BLUE)
                    .replace("<FORE-8a00b0>", colorama.Fore.MAGENTA)
                    .replace("<FORE-ffffff>", colorama.Fore.WHITE)
                    .replace(">>>", colorama.Fore.GREEN + ">>> ")
                    .replace("ggg", colorama.Fore.GREEN)
                    .replace("yyy", colorama.Fore.YELLOW)
                    .replace("rrr", colorama.Fore.RED)
                    .replace("ccc", colorama.Fore.CYAN)
                    .replace("bbb", colorama.Fore.BLUE)
                    .replace("mmm", colorama.Fore.MAGENTA)
                    .replace(
                        "<FORE-hhhhhh>", colorama.Back.YELLOW + colorama.Fore.MAGENTA
                    )
                    .replace("hhh", colorama.Back.YELLOW + colorama.Fore.MAGENTA)
                    .replace("<<<", colorama.Back.RESET + colorama.Fore.WHITE)
                    .replace("<RESET>", colorama.Back.RESET + colorama.Fore.WHITE)
                )

                print(
                    colorama.Fore.CYAN
                    + "    >>"
                    + colorama.Fore.LIGHTWHITE_EX
                    + f"\t{l}"
                )
    print(colorama.Fore.RESET + colorama.Back.RESET)  ##back to basics

    with open(styles_path, "w") as f:
        for line in contents:
            if line.startswith(";"):
                f.write(line)
                continue
        for kw in styles:
            f.write(f"{kw.strip()}={styles[kw].strip()}\n")


def process_loop(args, init_dict={}):
    # d = init_dict
    print(  ##loop instructions
        'Initiating loop. \n\tType "-e" or "--exit" to break out of loop at any time.\n\t'
        'Type "-s" when specifying topics to keep previous topics.\n\t'
        f'Denote line breaks with "{init_dict.get("default_linebreak", ";")}" when typing notes.\n'
    )
    if path.isfile(
        (getattr(args, init_dict.get("default_changefilename_flags")[-1].strip()))
    ):  ##grab most recent topics on file
        with open(
            (getattr(args, init_dict.get("default_changefilename_flags")[-1].strip())),
            "r",
            encoding="latin1",
        ) as f:
            line = f.readline()
        mat = match(r"^.*--(.*)::", line)
        user_topics = mat.group(1) if mat else "misc"
    else:
        user_topics = "misc"
    while True:  ##enter loop and take notes until user breaks out
        user_input = input(
            f"Enter comma-separated topics. Previous Topics: {user_topics}\n\t"
        )
        if user_input == "-e" or user_input == "--exit":
            break
        if user_input != "-s":
            user_topics = user_input if user_input != "" else "misc"
        user_input = input(
            f'Enter Note (separate thoughts denoted by {init_dict.get("default_linebreak", ";")}):\n\t'
        )
        if user_input == "-e" or user_input == "--exit":
            break
        try:
            with open(
                (
                    getattr(
                        args, init_dict.get("default_changefilename_flags")[-1].strip()
                    )
                ),
                "r",
            ) as f:
                string = f.read()
        except FileNotFoundError:
            string = ""

        try:
            copy2(
                (
                    getattr(
                        args, init_dict.get("default_changefilename_flags")[-1].strip()
                    )
                ),
                f'COPY - {(getattr(args, init_dict.get("default_changefilename_flags")[-1].strip()))}',
            )
        except FileNotFoundError:
            print(
                f'Creating {(getattr(args, init_dict.get("default_changefilename_flags")[-1].strip()))}'
            )

        with open(
            (getattr(args, init_dict.get("default_changefilename_flags")[-1].strip())),
            "w",
        ) as f:
            f.write(
                str(datetime.today())[:19]
                + "--"
                + user_topics
                + "::"
                + user_input
                + "\n"
                + string
            )

        process_line(
            str(datetime.today())[:19] + "--" + user_topics + "::" + user_input,
            init_dict,
        )  # pretty print thoughts as they're typed


def init_args(d):

    parser = ArgumentParser(
        prog="Notes > Memory",
        description="Never rely on memory; type it out!",
        epilog="Now take notes!",
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-v", "--version", action="store_true", help="show software version and exit"
    )
    group.add_argument(
        *[
            f"-{flag.strip()}" if len(flag.strip()) == 1 else f"--{flag.strip()}"
            for flag in d.get("default_open_flags", ["o", "openfile"])
        ],
        action="store_true",
        help="launch notes text file (currently {}) and exit".format(
            d.get("default_file")
        ),
    )
    group.add_argument(
        *[
            f"-{flag.strip()}" if len(flag.strip()) == 1 else f"--{flag.strip()}"
            for flag in d.get(
                "default_defaultfile_flags", ["d", "defaultfile", "default"]
            )
        ],
        help="change default file name where notes should be stored "
        f'(i.e.: {d.get("default_file")}) and exit',
        default=d.get("default_file"),
    )
    group.add_argument(
        *[
            f"-{flag.strip()}" if len(flag.strip()) == 1 else f"--{flag.strip()}"
            for flag in d.get("default_loop_flags", ["l", "loop"])
        ],
        action="store_true",
        help="initiate note-taking loop - - - - - - - - - - - - - - "
        "best for multiple notes back to back - - - - - - - - - "
        'to exit, type and enter "--exit" or "-e" at any time - '
        'when specifying topics, "-s" to keep previous topics',
    )
    parser.add_argument(
        *[
            f"-{flag.strip()}" if len(flag.strip()) == 1 else f"--{flag.strip()}"
            for flag in d.get("default_note_flags", ["a", "n", "note"])
        ],
        nargs="+",
        help="add note to file; "
        f'specify topic with -{str([i for i in d.get("default_topic_flags", ["t"]) if len(i) == 1])} flag(s) '
        f'specify file name with -{str([i for i in d.get("default_changefilename_flags", ["f"]) if len(i) == 1])} flag(s) - - - - - - - - '
        f'(default: ./{d.get("default_file")}) - - - - - - - - - - - - - - - - - - - - - - - - - - - WARNING - - - - - - - - - - - this flag does NOT like the & or > characters; they work just fine in the loop though',
    )
    parser.add_argument(
        *[
            f"-{flag.strip()}" if len(flag.strip()) == 1 else f"--{flag.strip()}"
            for flag in d.get("default_changefilename_flags", ["f", "filename"])
        ],
        help="specify file name where this note should be stored (default file remains {})".format(
            d.get("default_file")
        ),
        default=d.get("default_file"),
    )
    parser.add_argument(
        *[
            f"-{flag.strip()}" if len(flag.strip()) == 1 else f"--{flag.strip()}"
            for flag in d.get("default_topic_flags", ["t", "topic"])
        ],
        nargs="+",
        help=f"specify one or more topics of interest to attached to "
        f"note being added - - - - - - - - - - - - - - - - - - - execute alone to output notes associated with entered "
        f'flag(s); execute flag -{str(d.get("default_topic_flags", "t"))} ALL to see all current topics in {d.get("default_file")}',
    )
    return parser


def process_init():

    d = {}

    d["default_file"] = "mynotes.txt"
    d["default_linebreak"] = ";"
    d["default_open_flags"] = ["o", "openfile"]
    d["default_defaultfile_flags"] = ["d", "defaultfile"]
    d["default_loop_flags"] = ["l", "loop"]
    d["default_note_flags"] = ["n", "a", "note"]
    d["default_changefilename_flags"] = ["f", "filename"]
    d["default_topic_flags"] = ["t", "topic"]

    if path.isfile(INIT_FILE):  ##process INIT_FILE indicated above if exists
        with open(INIT_FILE, "r") as f:
            init_lines = f.readlines()
        for (
            line
        ) in (
            init_lines
        ):  # process data and overwrite dict if data present; o/w goes with defaults
            for k in d:
                if k in line:
                    if "," in line:  # comma means list
                        d[k] = line.strip().split("=")[1].split(",")
                    else:
                        d[k] = line.strip().split("=")[1]
    else:  ##INIT_FILE not existing; create and initialize defaults
        with open(INIT_FILE, "w") as f:  # defaults from dictionary above
            for k, v in d.items():
                if type(v) == list:
                    f.write(f'{k}={",".join(v)}\n')
                else:
                    f.write(f"{k}={v}\n")

    parser = init_args(d)

    args = parser.parse_args()

    return d, args


if __name__ == "__main__":
    main()
