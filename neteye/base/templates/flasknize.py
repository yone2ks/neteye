import sys
from html_flasknize import HtmlFlasknize

filename = sys.argv[1]
hf = HtmlFlasknize(filename)
hf.change_all()
with open(filename, "w") as f:
    f.write(hf.output())
