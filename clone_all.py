import os
import urllib.request
import urllib.parse
from html.parser import HTMLParser

# We specify all the menu items to download them maximally so nothing links to the live site!
PAGES = {
    'index.html': 'https://crossparish.ca/',
    'about.html': 'https://crossparish.ca/about/',
    'gallery.html': 'https://crossparish.ca/gallery/',
    'contact.html': 'https://crossparish.ca/contact/',
    'schedule.html': 'https://crossparish.ca/home-cross-parish/divine-liturgical-schedule/',
    'food-sales.html': 'https://crossparish.ca/food-sales/',
    'directory.html': 'https://crossparish.ca/member-directory/',
    'donation.html': 'https://crossparish.ca/donation/',
    'news.html': 'https://crossparish.ca/news/',
    'ucwlc.html': 'https://crossparish.ca/about/ucwlc/',
    'calendar.html': 'https://crossparish.ca/about/parish-calendar/',
    'history.html': 'https://crossparish.ca/about/history-2/',
    'bulletins.html': 'https://crossparish.ca/home-cross-parish/bulletins/'
}

class ResourceParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.modified_html_snippets = []

    def handle_starttag(self, tag, attrs):
        self._process_tag(tag, attrs, is_start_end=False)

    def handle_startendtag(self, tag, attrs):
        self._process_tag(tag, attrs, is_start_end=True)

    def _process_tag(self, tag, attrs, is_start_end):
        modified_attrs = []
        for k, v in attrs:
            if tag == 'a' and k == 'href' and v:
                # Rewrite absolute links to local HTML files if they match our known pages
                rewritten = False
                for local_file, target_url in PAGES.items():
                    if v == target_url or v == target_url.rstrip('/') or v == target_url + '/':
                        v = local_file
                        rewritten = True
                        break
                
                # If it still points to crossparish.ca but we aren't downloading it, 
                # let's just make it a local anchor to prevent escaping the repo.
                if not rewritten and 'crossparish.ca' in v:
                    v = 'index.html'

            modified_attrs.append(f'{k}="{v}"' if v is not None else k)
                    
        attr_str = " ".join(modified_attrs)
        spacing = " " if attr_str else ""
        end_slash = " /" if is_start_end else ""
        self.modified_html_snippets.append(f"<{tag}{spacing}{attr_str}{end_slash}>")

    def handle_endtag(self, tag):
        self.modified_html_snippets.append(f"</{tag}>")

    def handle_data(self, data):
        self.modified_html_snippets.append(data)

    def handle_entityref(self, name):
        self.modified_html_snippets.append(f"&{name};")

    def handle_charref(self, name):
        self.modified_html_snippets.append(f"&#{name};")

    def handle_comment(self, data):
        self.modified_html_snippets.append(f"<!--{data}-->")

    def handle_decl(self, data):
        self.modified_html_snippets.append(f"<!{data}>")

    def get_html(self):
        return "".join(self.modified_html_snippets)

def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    for filename, url in PAGES.items():
        print(f"[{filename}] Downloading {url}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                
                # Parse and rewrite links
                parser = ResourceParser(url)
                parser.feed(html)
                modified_html = parser.get_html()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(modified_html)
                print(f"[{filename}] Saved successfully and internal links rewritten.")
                
        except Exception as e:
            print(f"[{filename}] Error downloading: {e}")

    print("Success! The specified pages have been cloned. You can now browse them locally.")

if __name__ == "__main__":
    main()
