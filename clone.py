import os
import urllib.request
import urllib.parse
from html.parser import HTMLParser

BASE_URL = 'https://crossparish.ca/'
TARGET_DIR = '.'

class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.modified_html_snippets = []

    def handle_starttag(self, tag, attrs):
        self._process_tag(tag, attrs, is_start_end=False)

    def handle_startendtag(self, tag, attrs):
        self._process_tag(tag, attrs, is_start_end=True)

    def _process_tag(self, tag, attrs, is_start_end):
        attr_dict = dict(attrs)
        link_attr = None
        
        if tag == 'link' and attr_dict.get('rel') == 'stylesheet':
            link_attr = 'href'
        elif tag in ['script', 'img', 'source']:
            link_attr = 'src'
            
        modified_attrs = []
        for k, v in attrs:
            if k == link_attr and v and not v.startswith('data:'):
                parsed_url = urllib.parse.urlparse(v)
                if not parsed_url.netloc or parsed_url.netloc == urllib.parse.urlparse(BASE_URL).netloc:
                    ext = os.path.splitext(parsed_url.path)[1]
                    filename = os.path.basename(parsed_url.path)
                    if filename:
                        asset_type = 'assets'
                        if tag == 'link': asset_type = 'css'
                        elif tag == 'script': asset_type = 'js'
                        elif tag == 'img' or tag == 'source': asset_type = 'img'
                        
                        local_path = os.path.join(TARGET_DIR, asset_type, filename)
                        relative_link = os.path.join(asset_type, filename)
                        
                        self.assets.append((urllib.parse.urljoin(BASE_URL, v), local_path))
                        v = relative_link
            
            if v is None:
                modified_attrs.append(f'{k}')
            else:
                modified_attrs.append(f'{k}="{v}"')
                    
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
    print(f"Fetching {BASE_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    req = urllib.request.Request(BASE_URL, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching base URL: {e}")
        return

    parser = AssetParser()
    parser.feed(html)
    
    modified_html = parser.get_html()
    
    with open(os.path.join(TARGET_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(modified_html)
        
    total_assets = len(set(parser.assets))
    print(f"Found {total_assets} internal assets. Starting download...")
    
    success_count = 0
    for asset_url, local_path in set(parser.assets):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if not os.path.exists(local_path):
            try:
                asset_req = urllib.request.Request(asset_url, headers=headers)
                with urllib.request.urlopen(asset_req, timeout=10) as response, open(local_path, 'wb') as f:
                    f.write(response.read())
                success_count += 1
            except Exception as e:
                print(f"Failed to download {asset_url}: {e}")
        else:
            success_count += 1

    print(f"Cloning complete! Successfully downloaded {success_count}/{total_assets} assets.")

if __name__ == "__main__":
    main()
