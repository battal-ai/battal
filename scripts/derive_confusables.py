"""Derive the confusable folding table used by normalization (spec S2, section 5.2).

Usage: python scripts/derive_confusables.py <confusables.txt 15.1.0> <output.json>
Source: https://www.unicode.org/Public/security/15.1.0/confusables.txt
"""
import sys, json, hashlib, regex, unicodedata
src_path, out_path = sys.argv[1], sys.argv[2]
raw = open(src_path, "rb").read()
table = {}
for line in raw.decode("utf-8-sig").splitlines():
    line = line.split("#")[0].strip()
    if not line: continue
    s, t, _ = [x.strip() for x in line.split(";")]
    s = [chr(int(x, 16)) for x in s.split()]; t = "".join(chr(int(x, 16)) for x in t.split())
    if len(s) != 1 or not regex.match(r"\p{Script=Cyrillic}|\p{Script=Greek}", s[0]): continue
    if not regex.fullmatch(r"[A-Za-z]+", t): continue
    if t == "l" and unicodedata.category(s[0]) == "Lu": t = "I"
    table["U+%04X" % ord(s[0])] = t
out = {"source": "https://www.unicode.org/Public/security/15.1.0/confusables.txt",
       "source_sha256": hashlib.sha256(raw).hexdigest(), "unicode_version": "15.1.0",
       "rule": "S2 section 5.2", "mappings": dict(sorted(table.items(), key=lambda kv: int(kv[0][2:], 16)))}
open(out_path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=True, indent=1) + "\n")
print(len(table))
