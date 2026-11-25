import re
import sys

TOKEN_SPEC = [
    ('b', r'#b[01]+'),
    ('p', r'#p[0-4]+'),
    ('n', r'[0-9]+'),
    ('i', r'[A-Za-z]{1,2}(?![A-Za-z])'),
    ('op', r'[&^|~()=;]'),
    ('ws', r'[ \t\r]+'),
]
TOKEN_RE = [(kind, re.compile(pat)) for kind, pat in TOKEN_SPEC]


class ParseError(Exception):
    pass


def normalize(text):
    """Перевод строки работает как разделитель ';'. Пустые строки пропускаются."""
    lines = [ln.strip() for ln in text.splitlines()]
    return ';'.join(ln for ln in lines if ln)


def tokenize(text):
    tokens, pos = [], 0
    while pos < len(text):
        for kind, rx in TOKEN_RE:
            m = rx.match(text, pos)
            if m:
                break
        else:
            raise ParseError(f"недопустимый символ {text[pos]!r} (позиция {pos})")
        if kind == 'op':
            tokens.append((m.group(), m.group()))
        elif kind != 'ws':
            tokens.append((kind, m.group()))
        pos = m.end()
    tokens.append(('$', ''))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def look(self):
        return self.tokens[self.pos][0]

    def take(self, expected):
        kind, text = self.tokens[self.pos]
        if kind != expected:
            found = text if text else 'конец цепочки'
            raise ParseError(f"ожидалось '{expected}', найдено '{found}'")
        self.pos += 1

    def parse(self):
        self.parse_P()
        self.take('$')

    def parse_P(self):  # P -> S L
        self.parse_S()
        self.parse_L()

    def parse_L(self):  # L -> ; S L | ε
        if self.look() == ';':
            self.take(';')
            self.parse_S()
            self.parse_L()

    def parse_S(self):  # S -> i = E
        self.take('i')
        self.take('=')
        self.parse_E()

    def parse_E(self):  # E -> U R
        self.parse_U()
        self.parse_R()

    def parse_R(self):  # R -> O U R | ε
        if self.look() in ('&', '^', '|'):
            self.parse_O()
            self.parse_U()
            self.parse_R()

    def parse_O(self):  # O -> & | ^ | |
        if self.look() not in ('&', '^', '|'):
            raise ParseError("ожидалась бинарная операция & ^ |")
        self.take(self.look())

    def parse_U(self):  # U -> ~ U | A
        if self.look() == '~':
            self.take('~')
            self.parse_U()
        else:
            self.parse_A()

    def parse_A(self):  # A -> n | b | p | i | ( E )
        if self.look() in ('n', 'b', 'p', 'i'):
            self.take(self.look())
        elif self.look() == '(':
            self.take('(')
            self.parse_E()
            self.take(')')
        else:
            raise ParseError("ожидался операнд: константа, имя или '('")


def analyze(text):
    try:
        Parser(tokenize(normalize(text))).parse()
    except ParseError:
        return 'Rejected'
    return 'Accepted'


TESTS = [
    ("a = 5", "Accepted"),
    ("x = ~a ^ (b | #p1342)", "Accepted"),
    ("ab = #b1011 & 7", "Accepted"),
    ("a = 1; b = a & c; d = ~~e", "Accepted"),
    ("a = 1\nb = 2", "Accepted"),
    ("a = (b & c) | ~(d ^ #b0)", "Accepted"),
    ("a = #b1012", "Rejected"),
    ("a = #p15", "Rejected"),
    ("abc = 1", "Rejected"),
    ("a = 1 &", "Rejected"),
    ("a = (b | c", "Rejected"),
    ("a == 1", "Rejected"),
    ("a = 1;", "Rejected"),
    ("1 = a", "Rejected"),
    ("a = b c", "Rejected"),
    ("a = ()", "Rejected"),
]


def run_tests():
    failed = 0
    for i, (src, expected) in enumerate(TESTS, 1):
        got = analyze(src)
        ok = got == expected
        failed += not ok
        print(f"#{i:>2} {'OK ' if ok else 'ERR'} {got:<8} {src!r}")
    print(f"\nИтого: {len(TESTS) - failed} из {len(TESTS)} верно")
    return failed


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding='utf-8') as f:
            print(analyze(f.read()))
    else:

        run_tests()

        print("\n" + "=" * 40)
        print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("Введите строку для проверки (или 'exit' для выхода).")
        print("Для разделения операторов используйте ';' или Enter.")
        print("=" * 40)

        while True:
            try:
                user_input = input("\n> ")
                if user_input.strip().lower() == 'exit':
                    break
                if not user_input.strip():
                    continue



                result = analyze(user_input)
                print(f"Результат: {result}")
            except KeyboardInterrupt:
                break