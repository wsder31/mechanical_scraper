import os
import json
import webbrowser
import urllib3
import requests     # pip install requests
from requests_html import HTMLSession   # pip install requests-html
from urllib.parse import urlparse, parse_qs, parse_qsl
from bs4 import BeautifulSoup   # pip install bs4
import autopep8  # pip install autopep8
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ssl


class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_legacy_session():
    # SSL Error (UNSAFE_LEGACY_RENEGOTIATION_DISABLED) 발생시 조치 방법
    # https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session


class MechanicalScraper:
    instance_name = None    # Instance name

    browser = None          # Default browser
    base_url = None         # Base URL

    session = None          # Requests Session
    is_legacy_session = None

    parser_options = ['lxml', 'html.parser']   # Parser Options

    def __init__(self, browser='EDGE', instance_name='ms', is_legacy_session=False):
        self.instance_name = instance_name
        self.is_legacy_session = is_legacy_session

        # Set default browser
        if 'EDGE' == browser.upper():
            browser_path = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
            self.browser = 'edge'
            webbrowser.register(self.browser, None, webbrowser.BackgroundBrowser(browser_path))
        elif 'CHROME' == browser.upper():
            browser_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
            self.browser = 'chrome'
            webbrowser.register(self.browser, None, webbrowser.BackgroundBrowser(browser_path))

        if self.is_legacy_session:
            ssl._create_default_https_context = ssl._create_unverified_context
            self.session = get_legacy_session()
        else:
            self.session = requests.Session()
            # self.session = HTMLSession()    # TODO: response.html.render() 이후에 sa_popup 띄우기 옵션

    def gen_code_request(self, http_message, **kwargs):
        """
        Generate code for HTTP Request
        @param http_message: Raw HTTP Message
        @param kwargs: kwargs['including_headers'] Codes only the header items in the list. However, list elements must be written in lower case form without hyphens.
        @return:
        """
        _ret = ''

        if len(http_message.split('\n')) < 2:
            raise Exception('Invalid HTTP Message.')

        # HTTP messages are divided into start line, headers, and body.
        start_line = http_message.split('\n')[0].strip()
        headers, *body = http_message.split('\n', 1)[1].split('\n\n')

        # Convert headers to a dictionary.
        headers_dict = dict(line.split(': ', 1) for line in headers.split('\n') if line.strip())

        # kwargs['including_headers'] Codes only the header items in the list. However, list elements must be written in lower case form without hyphens.
        headers_dict = {key: value for key, value in headers_dict.items() if key.replace('-', '').lower() in kwargs.get('including_headers', [])}

        # Convert body to dictionary.
        body_dict = {}
        if body:
            body_dict = dict(parse_qsl(body[0].strip()))

            if not body_dict:
                try:
                    body_dict = json.loads(body[0].strip().encode('utf-8'))
                except:
                    body_dict = {}

        method = 'GET' if start_line.startswith('GET') else 'POST' if start_line.startswith('POST') else '?'
        target = start_line.split(' ')[1]

        if 'GET' == method:
            _ret = self.gen_code_get(target, headers_dict, **kwargs)
        elif 'POST' == method:
            _ret = self.gen_code_post(target, headers_dict, body_dict, **kwargs)
        else:
            raise Exception('Only GET and POST methods are supported.')

        return _ret

    def gen_code_get(self, target, headers, **kwargs):
        """
        Generates the request code of the GET method.
        @param target:
        @param headers:
        @param kwargs:
        @return:
        """
        parsed_url = urlparse(target)
        base_url = parsed_url.scheme + "://" + parsed_url.hostname

        _ret = f"""
from bs4 import BeautifulSoup
from mechanical_scraper.mechanical_scraper import MechanicalScraper


{self.instance_name} = MechanicalScraper()
{self.instance_name}.set_base_url('{base_url}')

response = {self.instance_name}.get('{target}', True, headers={json.dumps(headers)})

response.raise_for_status()

bs = BeautifulSoup(response.text, '{kwargs["parser"]}')
                """.strip()

        return _ret

    def gen_code_post(self, target, headers, body, **kwargs):
        """
        Generates POST method request code.
        @param target:
        @param headers:
        @param body:
        @param kwargs:
        @return:
        """

        _ret = ''

        data_str = ''
        files_str = ''

        content_type = headers.get('Content-Type', '')

        if content_type == '':
            data_str = json.dumps(body)
        elif 'application/x-www-form-urlencoded' in content_type:
            data_str = json.dumps(body)
        elif 'application/json' in content_type:
            data_str = f"json.dumps({json.dumps(body)})"
        elif 'application/octet-stream' in content_type:
            data_str = f"b'{body}'"
        elif 'multipart/form-data' in content_type:
            data_str = f"json.dumps({json.dumps(body)})"
            files_str = ", files={'file': open('file.txt', 'rb')}"
        elif 'text' in content_type:
            data_str = body
        else:
            raise Exception('Content-Type not yet supported. Please report the HTTP Message.')

        parsed_url = urlparse(target)
        base_url = parsed_url.scheme + "://" + parsed_url.hostname

        _ret = f"""
from bs4 import BeautifulSoup
from mechanical_scraper.mechanical_scraper import MechanicalScraper


{self.instance_name} = MechanicalScraper()
{self.instance_name}.set_base_url('{base_url}')

response = {self.instance_name}.post('{target}', True, data={data_str}{files_str}, headers={json.dumps(headers)})

response.raise_for_status()

bs = BeautifulSoup(response.text, '{kwargs["parser"]}')
                """.strip()

        return _ret

    def get(self, url, use_sa=False, **kwargs):
        """
        Send HTTP Request in GET method.
        @param url:
        @param use_sa: Whether or not to bring up the Selector Assistant
        @param kwargs:
        @return:
        """
        _response = self.session.get(url, **kwargs)

        if use_sa:
            self.sa_popup(_response.text)

        return _response

    def post(self, url, use_sa=False, **kwargs):
        """
        Send HTTP Request in POST method.
        @param url:
        @param use_sa: Whether or not to bring up the Selector Assistant
        @param kwargs:
        @return:
        """
        _response = self.session.post(url, **kwargs)

        if use_sa:
            self.sa_popup(_response.text)

        return _response

    def sa_hidden_data(self, html, parser):
        ret = []

        #region extract input_hidden data
        bs = BeautifulSoup(html, parser)
        ret.extend(bs.select('input[type="hidden"]'))
        #endregion

        ret = list(map(str, set(ret)))
        return ret

    def sa_popup(self, text, filepath='./_selector_assistant.html'):
        """
        Brings up the Selector Assistant window.
        @param parser:
        @param text: URL or Text/HTML
        @param filepath: File path to save locally
        @return:
        """

        if text.startswith('http'):
            webbrowser.get(self.browser).open(text)
        else:
            if self.is_json_or_json_list(text):
                filename, extension = os.path.splitext(filepath)
                filepath = f"{filename}.json"
            else:
                for parser in self.parser_options:
                    hidden_data = self.sa_hidden_data(text, parser)

                    if hidden_data:
                        msg = f'[Mechanical Scraper] Hidden data found. (parser: {parser})\n\n'
                        msg += '\n\n'.join(hidden_data)

                        # region Append JavaScript code to HTML for alerting
                        text += f'''
                        <script>
                        setTimeout(function () {{
                            alert(`{msg}`);
                        }}, 100);
                        </script>
                        '''
                        # endregion

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.beautify_json(text))

            webbrowser.get(self.browser).open('file://' + os.path.realpath(filepath))

    def set_base_url(self, url):
        """
        Specifies the base URL.
        @param url:
        @return:
        """
        self.base_url = url[:len(url)-1] if url.endswith('/') else url

    def get_full_url(self, url):
        """
        Returns the Full URL.
        ex) /sample.html --> https://sample.com/sample.html
        ex) https://sample.com/sample.html --> https://sample.com/sample.html
        @param url:
        @return:
        """
        _ret = ''

        url = url.strip()

        if url.startswith('/'):
            _ret = self.base_url + url.replace(f"{self.base_url}/", '')
        else:
            _ret = self.base_url + url.replace(f"{self.base_url}", '')

        return _ret

    def is_json_or_json_list(self, text):
        try:
            parsed_json = json.loads(text)
            if isinstance(parsed_json, (list, dict)):
                return True
            else:
                return False
        except ValueError:
            return False

    def beautify_json(self, text, indent=4):
        try:
            if self.is_json_or_json_list(text):
                return json.dumps(json.loads(text), indent=indent)
            else:
                return text
        except ValueError:
            return text


def example_naver_finance():
    ms = MechanicalScraper()
    ms.set_base_url('https://finance.naver.com/')

    url = f'{ms.base_url}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54'
    }
    response = ms.get(url, headers=headers)
    response.raise_for_status()

    bs = BeautifulSoup(response.text, 'lxml')
    elements = bs.select('#container > div.aside > div > div.aside_area.aside_popular > table > tbody > tr')
    for el in elements:
        title = el.select_one('th > a').text.strip()
        price = el.select_one('td:nth-child(2)').text.replace(',', '').strip()
        link = ms.get_full_url(el.select_one('th > a')['href'])

        print(title, price, link)
        print()


def example_google():
    ms = MechanicalScraper()

    response = ms.get(
        'https://google.com',
        True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})

    response.raise_for_status()


def gui():
    ms = MechanicalScraper()

    def gen_code_from_gui():
        http_message = tb_raw_http_message.get(1.0, tk.END)
        including_headers = tb_including_headers.get(1.0, tk.END).replace(' ', '').strip().split(',')

        code = ms.gen_code_request(http_message, including_headers=including_headers, parser=var_parser.get())

        if var_beautify.get():
            code = autopep8.fix_code(code, options={'aggressive': True})

        tb_code_result.delete(1.0, tk.END)
        tb_code_result.insert(tk.INSERT, code)

    def show_about():
        messagebox.showinfo(program_title, "http://silsako.com\nhttps://github.com/wsder31/mechanical_scraper\nsilsako@naver.com\nhttps://open.kakao.com/o/smMmbgV")

    program_title = 'Mechanical Scraper v3.1'

    root = tk.Tk()
    root.geometry('1000x700')
    root.title(program_title)

    tab_parent = ttk.Notebook(root)
    tab1 = ttk.Frame(tab_parent)

    tab_parent.add(tab1, text="Generating Code for HTTP Request")
    tab_parent.pack(expand=1, fill="both")

    lbl_including_headers = tk.Label(tab1, anchor='w', text='Enter the headers to include when generating the code. However, it must be entered in lower case without special symbols.\nIf you want multiple headers, you can enumerate them with commas.')
    lbl_including_headers.pack(side=tk.TOP, fill=tk.X)

    tb_including_headers = tk.Text(tab1, wrap=tk.WORD, height=10)
    tb_including_headers.pack(side=tk.TOP, fill=tk.X)

    tb_including_headers.delete(1.0, tk.END)
    tb_including_headers.insert(tk.INSERT, ', '.join(['referer', 'useragent', 'contenttype', 'acceptlanguage']))

    sb_including_headers = tk.Scrollbar(tb_including_headers)
    sb_including_headers.pack(side=tk.RIGHT, fill=tk.Y)

    lbl_raw_http_message = tk.Label(tab1, anchor='w', text='Enter the raw HTTP Message.')
    lbl_raw_http_message.pack(side=tk.TOP, fill=tk.BOTH)

    tb_raw_http_message = tk.Text(tab1, wrap=tk.WORD)
    tb_raw_http_message.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    sb_raw_http_message = tk.Scrollbar(tb_raw_http_message)
    sb_raw_http_message.pack(side=tk.RIGHT, fill=tk.Y)

    frm_button = tk.Frame(tab1)
    frm_button.pack(side=tk.TOP, pady=5)

    var_beautify = tk.IntVar()
    var_beautify.set(1)
    chk_beautify = tk.Checkbutton(frm_button, text="beautify", variable=var_beautify)
    chk_beautify.pack(side=tk.LEFT, padx=(0, 5))

    parser_options = ms.parser_options
    var_parser = tk.StringVar()
    var_parser.set(parser_options[0])
    drop_parser_options = tk.OptionMenu(frm_button, var_parser, *parser_options)
    drop_parser_options.pack(side=tk.LEFT, padx=(0, 5))

    btn_gen_code_request = tk.Button(frm_button, text="Generate Code for Request", command=gen_code_from_gui)
    btn_gen_code_request.pack(side=tk.LEFT)

    lbl_code_result = tk.Label(tab1, anchor='w', text='The code generated.')
    lbl_code_result.pack(side=tk.TOP, fill=tk.BOTH)

    tb_code_result = tk.Text(tab1, wrap=tk.WORD)
    tb_code_result.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    sb_code_result = tk.Scrollbar(tb_code_result)
    sb_code_result.pack(side=tk.RIGHT, fill=tk.Y)

    tb_including_headers.config(yscrollcommand=sb_including_headers.set)
    sb_including_headers.config(command=tb_including_headers.yview)

    tb_raw_http_message.config(yscrollcommand=sb_raw_http_message.set)
    sb_raw_http_message.config(command=tb_raw_http_message.yview)

    tb_code_result.config(yscrollcommand=sb_code_result.set)
    sb_code_result.config(command=tb_code_result.yview)

    menu = tk.Menu(root)
    root.config(menu=menu)

    help_menu = tk.Menu(menu)
    menu.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=show_about)

    root.mainloop()


if __name__ == '__main__':
    # example_naver_finance()
    # example_google()
    gui()

