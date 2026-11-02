"""A tiny multilingual greeter, used for practising Git with a team."""
import sys

__version__ = "1.0.0"

GREETINGS = {
    "en": "Hello",
    "fr": "Bonjour",
    "es": "Hola",
    "ar": "Ahlan"
}


def greet(name="World", lang="en", shout=False):
    word = GREETINGS.get(lang, GREETINGS["en"])
    message = f"{word}, {name}!"
    if shout:
        return message.upper()
    return message


def main(argv):
    lang = "en"
    shout = False
    names = []
    if "--version" in argv:
        print(__version__)
        return
    for arg in argv:
        if arg.startswith("--lang="):
            lang = arg.split("=", 1)[1]
        elif arg == "--shout":
            shout = True
        else:
            names.append(arg)
    print(greet(names[0] if names else "World", lang=lang, shout=shout))


if __name__ == "__main__":
    main(sys.argv[1:])
