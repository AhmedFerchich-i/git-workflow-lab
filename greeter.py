"""Multilingual greetings from the command line (a Git practice project)."""
import sys

__version__ = "1.0.4"

GREETINGS = {
    "en": "Hello",
    "fr": "Bonjour",
    "es": "Hola",
    "hu": "Szia",
    "nl": "Hallo",
    "fi": "Hei",
    "it": "Ciao",
}


def greet(name="World", lang="en", shout=False, quiet=False):
    word = GREETINGS.get(lang, GREETINGS["en"])
    message = f"{word}, {name}!"
    if shout:
        return message.upper()
    if quiet:
        return message.lower()
    return message


def main(argv):
    lang = "en"
    shout = False
    quiet = False
    names = []
    if "--version" in argv:
        print(__version__)
        return
    for arg in argv:
        if arg.startswith("--lang="):
            lang = arg.split("=", 1)[1]
        elif arg == "--shout":
            shout = True
        elif arg == "--quiet":
            quiet = True
        else:
            names.append(arg)
    print(greet(names[0] if names else "World", lang=lang, shout=shout, quiet=quiet))


if __name__ == "__main__":
    main(sys.argv[1:])
