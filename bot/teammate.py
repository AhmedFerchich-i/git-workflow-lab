#!/usr/bin/env python3
"""Sam, the bot teammate.

Runs inside GitHub Actions (see .github/workflows/teammate.yml). Each run does
one piece of "work" on the repository, the way a busy colleague would:

  land     - make a small change on a branch, open a pull request, merge it
  review   - open a pull request that needs your review and a fix (not merged)
  shared   - push a commit to the shared branch feature/shared-notes
  conflict - land a change that touches the busiest parts of the code at once
  bughunt  - land six pull requests in a row; one of them quietly breaks a test
  auto     - pick one of land / review / shared at random (or do nothing)

Set BOT_LOCAL=1 to run without GitHub (pull requests are simulated by squash
merging locally). That mode exists for testing the bot itself.
"""
import datetime
import os
import random
import re
import subprocess
import sys
import time

BASE = "main"
SHARED = "feature/shared-notes"
LOCAL = os.environ.get("BOT_LOCAL") == "1"
MODE = os.environ.get("MODE", "auto") or "auto"
if os.environ.get("BOT_SEED"):
    random.seed(os.environ["BOT_SEED"])

LANGUAGES = {
    "de": ("German", "Hallo"), "it": ("Italian", "Ciao"), "pt": ("Portuguese", "Ola"),
    "nl": ("Dutch", "Hallo"), "sv": ("Swedish", "Hej"), "tr": ("Turkish", "Merhaba"),
    "ar": ("Arabic", "Marhaba"), "sw": ("Swahili", "Habari"), "pl": ("Polish", "Czesc"),
    "ja": ("Japanese", "Konnichiwa"), "hi": ("Hindi", "Namaste"), "fi": ("Finnish", "Hei"),
    "da": ("Danish", "Hej"), "id": ("Indonesian", "Halo"), "ro": ("Romanian", "Salut"),
    "cs": ("Czech", "Ahoj"), "hu": ("Hungarian", "Szia"), "ga": ("Irish", "Dia duit"),
    "haw": ("Hawaiian", "Aloha"), "zu": ("Zulu", "Sawubona"),
}
NOTES = [
    "Tidied the README wording.", "Checked the tests on a fresh clone.",
    "Reviewed open pull requests.", "Updated the usage examples.",
    "Thinking about a --repeat flag.", "Should we support regional variants like fr-CA?",
    "Remember: fetch before you start work.", "Added a note about the release process.",
    "We could print the greeting in colour.", "Someone should write a CONTRIBUTING guide.",
]
DOCSTRINGS = [
    '"""A tiny multilingual greeter, used for practising Git with a team."""',
    '"""Greet people in several languages. Built for Git practice."""',
    '"""A small command-line greeter that knows a few languages."""',
    '"""Multilingual greetings from the command line (a Git practice project)."""',
]


# ---------------------------------------------------------------- helpers
def sh(*args, check=True):
    result = subprocess.run(args, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stdout}{result.stderr}")
    return result


def git(*args, check=True):
    return sh("git", *args, check=check).stdout.strip()


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%m%d-%H%M%S")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:30]


def tests_pass():
    return sh(sys.executable, "-m", "unittest", "-q", check=False).returncode == 0


def apply_edits(edits):
    """edits = [(path, old, new), ...]. Apply all or nothing."""
    contents = {}
    for path, old, _ in edits:
        if path not in contents:
            contents[path] = read(path) if os.path.exists(path) else ""
        if old not in contents[path]:
            return False
    for path, old, new in edits:
        contents[path] = contents[path].replace(old, new, 1)
    for path, text in contents.items():
        write(path, text)
    return True


def remote_branch_exists(name):
    return bool(git("ls-remote", "--heads", "origin", name))


def start_branch(name, base=BASE):
    git("fetch", "--prune", "origin")
    git("checkout", "-B", name, f"origin/{base}")


def commit_all(message):
    git("add", "-A")
    if sh("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    git("commit", "-m", message)
    return True


# ---------------------------------------------------------------- changes
def change_add_language(code=None, typo=False, readme=True):
    text = read("greeter.py")
    block = re.search(r"GREETINGS = \{\n(.*?)\n\}", text, re.S)
    if not block:
        return None
    present = set(re.findall(r'"([a-z]+)":', block.group(1)))
    choices = [c for c in LANGUAGES if c not in present]
    if code is None:
        if not choices:
            return None
        code = random.choice(choices)
    elif code in present:
        return None
    name, word = LANGUAGES[code]
    if typo and len(word) > 3:
        word = word[0] + word[2] + word[1] + word[3:]
    line = f'    "{code}": "{word}",'
    new_block = block.group(1) + "\n" + line
    write("greeter.py", text[:block.start(1)] + new_block + text[block.end(1):])
    if readme and os.path.exists("README.md"):
        lines = read("README.md").split("\n")
        if "## Languages" in lines:
            i = lines.index("## Languages") + 1
            last = None
            while i < len(lines) and not lines[i].startswith("## "):
                if lines[i].startswith("- "):
                    last = i
                i += 1
            if last is not None:
                lines.insert(last + 1, f"- {code}: {word}")
                write("README.md", "\n".join(lines))
    article = "an" if name[0] in "AEIOU" else "a"
    return f"Add {article} {name} greeting", code


def change_changelog():
    if not os.path.exists("README.md") or "## Changelog" not in read("README.md"):
        return None
    text = read("README.md").rstrip("\n")
    note = random.choice(NOTES)
    write("README.md", text + f"\n- {today()}: {note}\n")
    return "Update the changelog", None


def change_docstring():
    text = read("greeter.py")
    first = text.split("\n", 1)[0]
    if not first.startswith('"""'):
        return None
    options = [d for d in DOCSTRINGS if d != first]
    write("greeter.py", random.choice(options) + "\n" + text.split("\n", 1)[1])
    return "Reword the module docstring", None


def change_feature_quiet():
    if "quiet" in read("greeter.py"):
        return None
    ok = apply_edits([
        ("greeter.py", 'def greet(name="World", lang="en", shout=False):',
         'def greet(name="World", lang="en", shout=False, quiet=False):'),
        ("greeter.py", "    if shout:\n        return message.upper()\n",
         "    if shout:\n        return message.upper()\n    if quiet:\n        return message.lower()\n"),
        ("greeter.py", "    shout = False\n", "    shout = False\n    quiet = False\n"),
        ("greeter.py", '        elif arg == "--shout":\n            shout = True\n',
         '        elif arg == "--shout":\n            shout = True\n'
         '        elif arg == "--quiet":\n            quiet = True\n'),
        ("greeter.py", "lang=lang, shout=shout))", "lang=lang, shout=shout, quiet=quiet))"),
        ("test_greeter.py", "\n    def test_every_greeting_is_filled_in(self):",
         '\n    def test_quiet(self):\n        self.assertEqual(greet("Ahmed", quiet=True), "hello, ahmed!")\n'
         "\n    def test_every_greeting_is_filled_in(self):"),
    ])
    if not ok:
        return None
    apply_edits([("README.md", "    python greeter.py Ahmed --shout\n",
                  "    python greeter.py Ahmed --shout\n    python greeter.py Ahmed --quiet\n")])
    return "Add a --quiet flag", None


def change_feature_version():
    if "__version__" in read("greeter.py"):
        return None
    ok = apply_edits([
        ("greeter.py", "import sys\n", 'import sys\n\n__version__ = "1.0.0"\n'),
        ("greeter.py", "    for arg in argv:\n",
         '    if "--version" in argv:\n        print(__version__)\n        return\n    for arg in argv:\n'),
        ("test_greeter.py", "from greeter import GREETINGS, greet",
         "from greeter import GREETINGS, __version__, greet"),
        ("test_greeter.py", "\n    def test_every_greeting_is_filled_in(self):",
         "\n    def test_version_looks_like_semver(self):\n"
         '        self.assertRegex(__version__, r"^\\d+\\.\\d+\\.\\d+$")\n'
         "\n    def test_every_greeting_is_filled_in(self):"),
    ])
    return ("Add a --version flag", None) if ok else None


def change_bump_version():
    text = read("greeter.py")
    match = re.search(r'__version__ = "(\d+)\.(\d+)\.(\d+)"', text)
    if not match:
        return None
    major, minor, patch = (int(x) for x in match.groups())
    new = f'__version__ = "{major}.{minor}.{patch + 1}"'
    write("greeter.py", text.replace(match.group(0), new, 1))
    return f"Bump version to {major}.{minor}.{patch + 1}", None


def change_bug():
    """A plausible-looking edit that breaks a test."""
    if apply_edits([("greeter.py", '    "en": "Hello",', '    "en": "Helo",')]):
        return "Tidy up the greeting table", None
    if apply_edits([("greeter.py", "return message.upper()", 'return message.upper().rstrip("!")')]):
        return "Tidy up greet()", None
    return None


def pick_land_change():
    options = [
        (change_add_language, 35), (change_changelog, 25), (change_docstring, 10),
        (change_feature_quiet, 8), (change_feature_version, 7), (change_bump_version, 15),
    ]
    funcs = [f for f, _ in options]
    weights = [w for _, w in options]
    return random.choices(funcs, weights)[0]


# ---------------------------------------------------------------- pull requests
def open_pr(branch, title, body):
    if LOCAL:
        return
    sh("gh", "pr", "create", "--base", BASE, "--head", branch, "--title", title, "--body", body)


def merge_pr(branch, title):
    if LOCAL:
        git("checkout", "-B", BASE, f"origin/{BASE}")
        git("merge", "--squash", branch)
        git("commit", "-m", title)
        git("push", "origin", BASE)
        git("push", "origin", "--delete", branch)
        return
    for attempt in range(6):
        result = sh("gh", "pr", "merge", branch, "--squash", "--delete-branch", check=False)
        if result.returncode == 0:
            return
        print(f"merge attempt {attempt + 1} failed, retrying: {result.stderr.strip()}")
        time.sleep(5)
    raise RuntimeError(f"could not merge {branch}")


def land(change, require_tests=True, body=None):
    branch = f"sam/{stamp()}"
    start_branch(branch)
    outcome = change()
    if not outcome:
        print(f"skip: {change.__name__} has nothing to do")
        return False
    title, _ = outcome
    if require_tests and not tests_pass():
        print(f"skip: {title} would break the tests")
        git("reset", "--hard")
        return False
    if not commit_all(title):
        return False
    git("push", "-u", "origin", branch)
    open_pr(branch, title, body or "Small change from Sam. Merged straight away (Sam doesn't wait for review).")
    merge_pr(branch, title)
    print(f"landed: {title}")
    return True


def open_review_pr():
    if not LOCAL:
        listing = sh("gh", "pr", "list", "--state", "open", "--json", "headRefName",
                     "--jq", ".[].headRefName").stdout.split()
        if sum(1 for b in listing if b.startswith("sam/review-")) >= 2:
            print("skip: two review requests are already waiting")
            return False
    start_branch(f"sam/review-{stamp()}")
    outcome = change_add_language(typo=True, readme=False)
    if not outcome:
        print("skip: no languages left to add")
        return False
    title, code = outcome
    branch = f"sam/review-{code}-{stamp()}"
    git("checkout", "-b", branch)
    commit_all(title)
    git("push", "-u", "origin", branch)
    body = (
        f"Hi! I added a greeting for `{code}`, but I'm not sure I spelled it right, and I didn't have "
        "time to add it to the README or write a test.\n\n"
        "Could you check out this branch locally, fix what's needed, push your fixes **to this branch**, "
        "and merge it once CI is green? Thanks!\n\n- Sam"
    )
    open_pr(branch, title, body)
    print(f"opened review request: {title} on {branch}")
    return True


def push_shared():
    git("fetch", "--prune", "origin")
    path = "docs/NOTES.md"
    if not remote_branch_exists(SHARED):
        git("checkout", "-B", SHARED, f"origin/{BASE}")
        write(path, "# Team notes\n\n"
              "## Sam's notes\n\n"
              f"- Sam: {random.choice(NOTES)}\n\n"
              "## Your notes\n\n"
              "Add your lines below. If you edit Sam's section, expect conflicts.\n\n")
        commit_all("Start the shared team notes")
        git("push", "-u", "origin", SHARED)
        print(f"created {SHARED}")
        return True
    git("checkout", "-B", SHARED, f"origin/{SHARED}")
    lines = read(path).split("\n") if os.path.exists(path) else ["# Team notes", ""]
    sam_lines = [i for i, line in enumerate(lines) if line.startswith("- Sam:")]
    note = f"- Sam: {random.choice(NOTES)}"
    if sam_lines:
        lines.insert(sam_lines[-1] + 1, note)
    else:
        lines.append(note)
    write(path, "\n".join(lines))
    commit_all("Add a team note")
    for _ in range(3):
        if sh("git", "push", "origin", SHARED, check=False).returncode == 0:
            print(f"pushed a note to {SHARED}")
            return True
        if sh("git", "pull", "--rebase", "origin", SHARED, check=False).returncode != 0:
            git("rebase", "--abort", check=False)
            print("skip: my note conflicts with yours, giving up this time")
            return False
    return False


def busy_afternoon():
    def change():
        results = [change_add_language(), change_changelog(), change_docstring()]
        return ("Sam's busy afternoon: language, changelog, docstring", None) if any(results) else None
    return land(change)


def bughunt():
    plan = [change_changelog, change_add_language, change_bug, change_changelog,
            change_docstring, change_add_language]
    landed = 0
    for step in plan:
        # Sam "forgets" to run the tests all afternoon, so the bug gets buried.
        landed += bool(land(step, require_tests=False))
    print(f"bughunt: {landed} pull requests merged; one of them broke the tests")
    return True


def main():
    mode = MODE
    if mode == "auto":
        mode = random.choices(["land", "shared", "review", "idle"], [55, 20, 15, 10])[0]
    print(f"Sam is doing: {mode}")
    if mode == "land":
        change = pick_land_change()
        if not land(change):
            land(change_changelog)
    elif mode == "review":
        open_review_pr()
    elif mode == "shared":
        push_shared()
    elif mode == "conflict":
        busy_afternoon()
    elif mode == "bughunt":
        bughunt()
    elif mode == "idle":
        print("Sam is in a meeting.")
    else:
        sys.exit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
