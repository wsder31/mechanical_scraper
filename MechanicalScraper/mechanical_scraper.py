import os
import json
import webbrowser
import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


class MechanicalScraper:
    instance_name = None    # Instance name

    browser = None          # Default browser
    base_url = None         # Base URL

    session = None          # Requests Session

    def __init__(self, browser='EDGE', instance_name='ms'):
        self.instance_name = instance_name

        # Set default browser
        if 'EDGE' == browser.upper():
            browser_path = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
            self.browser = 'edge'
            webbrowser.register(self.browser, None, webbrowser.BackgroundBrowser(browser_path))
        elif 'CHROME' == browser.upper():
            browser_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
            self.browser = 'chrome'
            webbrowser.register(self.browser, None, webbrowser.BackgroundBrowser(browser_path))

        self.session = requests.Session()

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
            body_dict = parse_qs(body[0].strip())

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

        _ret = f"""
from mechanical_scraper import MechanicalScraper


{self.instance_name} = MechanicalScraper()

response = {self.instance_name}.get('{target}', headers={json.dumps(headers)})

response.raise_for_status()
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

        _ret = f"""
from mechanical_scraper import MechanicalScraper


{self.instance_name} = MechanicalScraper()

response = {self.instance_name}.post('{target}', data={data_str}{files_str}, headers={json.dumps(headers)})

response.raise_for_status()
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

    def sa_popup(self, input, filepath='./_selector_assistant.html'):
        """
        Brings up the Selector Assistant window.
        @param input: URL or Text/HTML
        @param filepath: File path to save locally
        @return:
        """
        if input.startswith('http'):
            webbrowser.get(self.browser).open(input)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(input)

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


def example_naver_finance():
    ms = MechanicalScraper()
    ms.set_base_url('https://finance.naver.com/')

    url = f'{ms.base_url}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54'
    }
    response = ms.get(url, headers=headers)
    response.raise_for_status()

    bs = BeautifulSoup(response.text, 'html.parser')
    elements = bs.select('#container > div.aside > div > div.aside_area.aside_popular > table > tbody > tr')
    for el in elements:
        title = el.select_one('th > a').text.strip()
        price = el.select_one('td:nth-child(2)').text.replace(',', '').strip()
        link = ms.get_full_url(el.select_one('th > a')['href'])

        print(title, price, link)
        print()


if __name__ == '__main__':
    # example_naver_finance()

    import black

    def gen_code_from_gui():
        http_message = tb_raw_http_message.get(1.0, tk.END)
        including_headers = tb_including_headers.get(1.0, tk.END).replace(' ', '').strip().split(',')

        ms = MechanicalScraper()
        code = ms.gen_code_request(http_message, including_headers=including_headers)

        if var_beautify.get():
            code = black.format_str(code, mode=black.FileMode())

        tb_code_result.delete(1.0, tk.END)
        tb_code_result.insert(tk.INSERT, code)


    def show_about():
        messagebox.showinfo(program_title, "http://silsako.com\nhttps://github.com/wsder31/mechanical_scraper\nsilsako@naver.com\nhttps://open.kakao.com/o/smMmbgV")


    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox

    program_title = 'Mechanical Scraper v1.1'

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
    tb_including_headers.insert(tk.INSERT, ', '.join(['referer', 'useragent', 'contenttype']))

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

    btn_gen_code_request = tk.Button(frm_button, text="Generate Code for Request", command=gen_code_from_gui)
    btn_gen_code_request.pack(side=tk.LEFT)

    lbl_code_result = tk.Label(tab1, anchor='w', text='The code generated.')
    lbl_code_result.pack(side=tk.TOP, fill=tk.BOTH)

    tb_code_result = tk.Text(tab1, wrap=tk.WORD)
    tb_code_result.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    sb_code_result = tk.Scrollbar(tb_code_result)
    sb_code_result.pack(side=tk.RIGHT, fill=tk.Y)

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

