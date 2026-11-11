# Greeter

A tiny multilingual greeter. Its real purpose is practising Git with a teammate who never stops working: **Sam**, a bot that pushes changes to this repository on a schedule.

## Usage

    python greeter.py Ahmed
    python greeter.py Ahmed --lang=fr
    python greeter.py Ahmed --shout
    python greeter.py Ahmed --quiet
    python -m unittest

## Languages

- en: Hello
- fr: Bonjour
- es: Hola
- hu: Szia
- nl: Hallo
- fi: Hei

## Rules of this repository

- Never commit directly to `main`. Every change goes through a pull request.
- Run the tests before you push.
- Sam may change anything at any time. Fetch often.

## Changelog

- Project created.
- 2026-11-03: Updated the usage examples.
- 2026-11-06: Thinking about a --repeat flag.
- 2026-11-07: Reviewed open pull requests.
- 2026-11-08: Tidied the README wording.
- 2026-11-10: Added a note about the release process.
