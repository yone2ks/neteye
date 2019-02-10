from bs4 import BeautifulSoup

class HtmlFlasknize():
    def __init__(self, filename):
        self.filename = filename
        self.parser = 'html.parser'
        with open(filename, "r") as f:
            self.soup = BeautifulSoup(f.read(), self.parser)

    def change_link(self):
        self.change_common("link", "href")

    def change_script(self):
        self.change_common("script", "src")

    def change_img(self):
        self.change_common("img", "src")

    def change_all(self):
        self.change_link()
        self.change_script()
        self.change_img()

    def change_common(self, tag, attr):
        lines = self.soup.find_all(tag)
        for line in lines:
            if line.has_attr(attr) and (not (line[attr] in 'http://') or (line[attr] in 'https://')):
                data = line[attr]
                flasknize_data =  "{{ url_for('base.static', filename='" + data + "' )}}"
                line[attr] = flasknize_data

    def output(self):
        return self.soup.prettify()
