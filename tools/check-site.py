"""Structural checks for the static dishd site (stdlib only)."""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(".")
PAGES = ["index.html", "privacy.html", "terms.html", "gdpr.html"]
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

problems = []


class Checker(HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.name = name
        self.stack = []
        self.ids = {}
        self.refs = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.setdefault(d["id"], 0)
            self.ids[d["id"]] += 1
        for key in ("src", "href"):
            if d.get(key):
                self.refs.append((key, d[key], self.getpos()))
        self.attrs.append((tag, d, self.getpos()))
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            problems.append(f"{self.name}: stray </{tag}> at {self.getpos()}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        names = [t for t, _ in self.stack]
        if tag in names:
            while self.stack and self.stack[-1][0] != tag:
                inner, pos = self.stack.pop()
                problems.append(
                    f"{self.name}: <{inner}> opened at {pos} still open when </{tag}> at {self.getpos()}"
                )
            self.stack.pop()
        else:
            problems.append(f"{self.name}: unexpected </{tag}> at {self.getpos()}")


def tags_in(value):
    return sorted(re.findall(r"<\s*/?\s*([a-zA-Z0-9]+)", value))


checkers = {}
for page in PAGES:
    path = ROOT / page
    if not path.exists():
        problems.append(f"{page}: missing file")
        continue
    checker = Checker(page)
    checker.feed(path.read_text(encoding="utf-8"))
    checker.close()
    checkers[page] = checker

    for tag, pos in checker.stack:
        problems.append(f"{page}: <{tag}> opened at {pos} never closed")

    dupes = [i for i, count in checker.ids.items() if count > 1]
    for d in dupes:
        problems.append(f"{page}: duplicate id={d}")

    for tag, attrs, pos in checker.attrs:
        has_en = "data-en" in attrs
        has_pl = "data-pl" in attrs
        if has_en != has_pl:
            problems.append(f"{page}:{pos[0]} <{tag}> has only one of data-en / data-pl")
        if has_en and has_pl:
            if tags_in(attrs["data-en"]) != tags_in(attrs["data-pl"]):
                problems.append(
                    f"{page}:{pos[0]} <{tag}> tag structure differs between EN and PL"
                )
        a_en, a_pl = "data-aria-en" in attrs, "data-aria-pl" in attrs
        if a_en != a_pl:
            problems.append(f"{page}:{pos[0]} <{tag}> has only one of data-aria-en / data-aria-pl")

    for key, value, pos in checker.refs:
        if value.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
            continue
        target, _, fragment = value.partition("#")
        target_file = ROOT / (target or page)
        if not target_file.exists():
            problems.append(f"{page}:{pos[0]} broken {key}={value!r}")
            continue
        if fragment:
            if not target.endswith(".html") and target:
                continue
            html = target_file.read_text(encoding="utf-8")
            if f'id="{fragment}"' not in html:
                problems.append(f"{page}:{pos[0]} missing anchor id={fragment} in {target_file}")

# CSS classes that no page uses (state classes are added by JS).
css = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
css_classes = set(re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", css))
markup = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in PAGES if (ROOT / p).exists())
used = set(re.findall(r'class="([^"]*)"', markup))
used_classes = {c for group in used for c in group.split()}
js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
js_classes = set(re.findall(r"classList\.(?:add|remove|toggle|contains)\('([a-zA-Z0-9_-]+)'", js))
js_classes |= set(re.findall(r"class=\"([a-zA-Z0-9_-]+)\"", js))
orphans = sorted(c for c in css_classes - used_classes - js_classes if not c.endswith(")"))

# image files referenced but missing
for page in PAGES:
    if not (ROOT / page).exists():
        continue
    for src in re.findall(r'<img[^>]*src="([^"]+)"', (ROOT / page).read_text(encoding="utf-8")):
        if not (ROOT / src).exists():
            problems.append(f"{page}: missing image {src}")

print("PAGES:", ", ".join(checkers))
print("CSS classes not used in markup:", ", ".join(orphans) if orphans else "none")
if problems:
    print("\nPROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("\nOK: structure, links, anchors, translation pairs and assets all check out.")
