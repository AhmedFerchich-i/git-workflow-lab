import unittest

from greeter import GREETINGS, greet


class GreetTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(greet(), "Hello, World!")

    def test_name(self):
        self.assertEqual(greet("Ahmed"), "Hello, Ahmed!")

    def test_french(self):
        self.assertEqual(greet("Ahmed", lang="fr"), "Bonjour, Ahmed!")

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(greet("Ahmed", lang="xx"), "Hello, Ahmed!")

    def test_shout(self):
        self.assertEqual(greet("Ahmed", shout=True), "HELLO, AHMED!")

    def test_every_greeting_is_filled_in(self):
        for lang, word in GREETINGS.items():
            self.assertTrue(word.strip(), f"empty greeting for {lang}")


if __name__ == "__main__":
    unittest.main()
