import socket
import ssl
import os
import sys
import time
import gzip
import tkinter
import emoji
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
sockets = {}

# Cache is in the form {"label": ["expiryTime", "content"]}
browserCache = {}
HSTEP = 13
VSTEP = 18
SCROLL_STEP = 100
rtl = False
FONTS = {}

class URL:
    def __init__(self, URL):
        self.scheme, URL = URL.split("://", 1)
        assert self.scheme in ["http", "https"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        if "/" not in URL:
            URL = URL + "/"
        self.host, URL = URL.split("/", 1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        self.path = "/" + URL

    def addHeaders(self, req, headers):
        for header in headers:
            name = header
            value = headers[header]
            req += f"{name}: {value}\r\n"
        return req
    
    def request(self, headers, attempt, browser):

        if(attempt > 5):
            print("Too many redirects...")
            return 0
        
        # Check if response already cached
        ans = browserCache.get(self.host + self.path)
        if ans: 
            expiryTime = ans[0]
            if time.time() < expiryTime:
                return ans[1]
            else:
                # Delete stale cache
                del browserCache[self.host + self.path]

        key = self.host + ":" + str(self.port)
        s = sockets.get(key)
        if not s:
            s = socket.socket(
                family = socket.AF_INET,
                type = socket.SOCK_STREAM,
                proto = socket.IPPROTO_TCP)
            try:
                s.connect((self.host, self.port))
            except socket.timeout:
                browser.dataLoad("Connection timed out")
                return 
            except ConnectionRefusedError:
                browser.dataLoad("Connection refused")
                return
            except socket.gaierror:
                browser.aboutBlank()
                return
            except OSError as e:
                browser.dataLoad(f"Socket error: {e}")
                return

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)  
            sockets[key] = s      


        request = f"GET {self.path} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\nConnection: keep-alive\r\n"
        request += f"User-Agent: Jef\r\n"
        request += "Accept-Encoding: gzip\r\n"
        # Adding headers
        request = self.addHeaders(request, headers)
        request += "\r\n"
        print("The final request:\n", request)
        s.send(request.encode("utf8"))
        
        response = s.makefile('rb', newline = "\r\n")
        arrTime = time.time()
        statusline = response.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        statusCode = int(status)
        # Redirect Handling
        if statusCode >= 300 and statusCode < 400 and attempt < 5:
            path = response_headers["location"]
            if path.startswith("http://") or path.startswith("https://"):
                nextHop = response_headers["location"]
                return URL(nextHop).request({}, attempt + 1)  # pass attempt count down
            else:
                # relative path.
                self.path = path
                return self.request({}, attempt + 1)

        #Encoding Handling
        raw = b""
        if response_headers.get("transfer-encoding") == "chunked":
            while True:
                size_line = response.readline().decode("utf8").strip()
                size = int(size_line, 16)
                if size == 0: break
                raw += response.read(size)
                response.readline()
        else:
            msgLen = response_headers.get("content-length")
            if not msgLen:
                raw = response.read()
            else:
                raw = response.read(int(msgLen))

        if isGzip(response_headers):
            raw = gzip.decompress(raw)

        content = raw.decode("utf8")  # works for all four cases
        if statusCode in [200, 301, 404]: self.cache(response_headers, content, arrTime)
        return content
    
    def cache(self, headers, content, time):

        cache_control = headers.get("cache-control")
        if not cache_control: return
        directives = [d.strip() for d in cache_control.split(",")]
        accepted = ["max-age", "no-store"]

        for directive in directives:
            success = 0
            for entry in accepted:
                if directive.startswith(entry): success = 1
            if success == 0: return

        # All un-cacheable responses have been sent away
        for directive in directives:
            if(directive.startswith("no-store")): return
            if directive.startswith("max-age"):
                # Store the header
                attr, val = directive.split("=", 1)
                age = headers.get("age")
                if not age: age = 0
                expiryTime = time + (int(val) - int(age))
                browserCache[self.host + self.path] = [expiryTime, content]
                return

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag

def isGzip(headers):
    if headers.get("content-encoding") == "gzip": return True
    else: return False

def lex(body):
    buffer = ""
    out = []
    in_tag = False
    if not body: return
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out

def loadHeaders(args):

    headers = {}
    n = len(args)
    key = ""
    value = ""
    if(n < 2):
        return headers
    
    for i in range (2, n):
        if(i % 2 == 0):
            key = args[i]
        else:
            value = args[i]
            headers[key] = value
    
    return headers


def isURL(arg):
    if "://" not in arg:
        return False
    scheme, arg = arg.split("://", 1)
    return scheme in ["http", "https"]
                
def isDataURI(arg):
    return arg.startswith("data:")


def isViewSource(arg):
    if "view-source:" not in arg: return False
    else: return True

WIDTH, HEIGHT = 800, 600
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        bi_times = tkinter.font.Font(family="Finlandica Headline",size=16)
        self.font = bi_times
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT,
            bg = "#f9f3de"
        )
        self.scroll = 0
        self.scrollbar = tkinter.Scrollbar(self.window, orient= "vertical", command = self.scrollMaster, bg = "black")
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=1)
        self.emojis = []
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<Configure>", self.resize)    
        self.window.bind("<End>", self.scrollEnd)
        self.window.bind("<Home>", self.scrollTop)
        self.print = 1

    def scrollEnd(self, e):
        font = self.display_list[-1][3]
        m = font.metrics()
        bonus = m["linespace"]  
        # self.scroll = (self.display_list[-1][1] - HEIGHT + VSTEP) * 1.1
        self.scroll = self.display_list[-1][1] - HEIGHT + VSTEP + bonus
        self.canvas.delete("all")
        self.draw()

    def scrollTop(self, e):
        self.scroll = 0
        self.canvas.delete("all")
        self.draw()

    def scrollMaster(self, action, *args):
        if action == "scroll":
            direction = int(args[0])  # 1 = down, -1 = up
            if direction > 0:
                self.scrolldown(None)
            else:
                self.scrollup(None)
        elif action == "moveto":
            # print("hi")
            fraction = float(args[0])  # 0.0 to 1.0 position
            # print("fraction: ", fraction)
            if(fraction < 0):
                # print(fraction,"Too high")
                return
            if fraction > (1 + (VSTEP/self.display_list[-1][1])*2):
                maxScroll = self.display_list[-1][1] - HEIGHT
                self.scroll = min(int(fraction * maxScroll), 1 + (VSTEP/self.display_list[-1][1])*5)
                # print(fraction, "too low")
                return
            maxScroll = self.display_list[-1][1] - HEIGHT
            self.scroll = int(fraction * maxScroll)
            self.canvas.delete("all")
            self.draw()

    def resize(self, e):
        global WIDTH, HEIGHT
        # if(resizeCount >= 1): return
        # print("Resize fired")
        WIDTH = e.width
        HEIGHT = e.height
        # print(f"New width and height: {WIDTH} & {HEIGHT}")
        if not hasattr(self, 'tokens'): return 
        self.display_list = Layout(self.tokens).display_list
        self.canvas.delete("all")
        self.draw()

    def load(self, url, headers, browser):
        body = url.request(headers, 0, browser)
        print("Recieved response body. sart lexing...")
        tokens = lex(body)
        self.tokens = tokens
        print("Lexing over. Layout")
        # if(rtl): self.display_list = altLayout(self.text)
        self.display_list = Layout(tokens).display_list
        print("Layout set")
        self.draw()

    def srcLoad(self, url, headers):
        tokens = url.request(headers, 0)
        self.tokens = lex(tokens)
        self.display_list = Layout(self.tokens).display_list
        self.draw()

    def dataLoad(self, text):
        self.tokens = lex(text)
        self.display_list = Layout(self.tokens).display_list
        self.draw()

    def draw(self):
        # print("Drawing to the screen...")
        self.emojis = []
        pgLen = 1
        num = 5
        if len(self.display_list) > 0 : pgLen = self.display_list[-1][1]
        scrollUnit = (SCROLL_STEP / pgLen) 
        thumbLen = (HEIGHT/pgLen)
        num = scrollUnit * (self.scroll/100)
        self.scrollbar.set(num, num + thumbLen)
        if num + thumbLen >= 1 and num == 0:
            self.scrollbar.pack_forget()
        if len(self.display_list) == 0: return
        # for i in range(0, 5):
        #     if self.print == 1:print(self.display_list[i])
        #     self.print = 0
        
        for x, y, c, font in self.display_list:
            # if num > 0:
            # print(f"x: {x} y: {y} c: {c}")
                # num -= 1
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            if emoji.is_emoji(c):
                self.drawEmoji(c, x , y)
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor = "nw", font = font)


    def drawEmoji(self, emoji, x, y):
        fileName = "./assets/emojis/" + hex(ord(emoji))[2:].upper() + ".png"
        img = Image.open(fileName)
        img = img.resize((16, 16))
        photo = ImageTk.PhotoImage(img)
        self.emojis.append(photo)
        self.canvas.create_image(x, y - self.scroll, image= photo)

    def scrolldown(self, e):
        maxScroll = self.display_list[-1][1] - HEIGHT + VSTEP
        if self.scroll < maxScroll:
            self.scroll = min(self.scroll + SCROLL_STEP, maxScroll * 1.1)
        self.canvas.delete("all")
        self.draw()

    def scrollup(self, e):
        self.canvas.delete("all")
        if self.scroll >= 1: self.scroll -= SCROLL_STEP
        self.draw()
    
    def aboutBlank(self):
        self.dataLoad("")

weight = "normal"
style = "roman"

class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.line = []
        self.line_width = 0
        self.last_space = 0

        if not tokens:
            print("No response")
        else:
            for token in tokens:
                self.tokenize(token)
        self.flush()

    def tokenize(self, token):
        if isinstance(token, Text):
            for word in token.text.split():
                self.processWord(word)

        elif token.tag == "i":
            self.style = "italic"
        elif token.tag == "/i":
            self.style = "roman"
        elif token.tag == "b":
            self.weight = "bold"
        elif token.tag == "/b":
            self.weight = "normal"
        elif token.tag == "small":
            self.size -= 2
        elif token.tag == "/small":
            self.size += 2
        elif token.tag == "big":
            self.size += 4
        elif token.tag == "/big":
            self.size -= 4
        elif token.tag == 'h1 class="title"':
            # print("h1 detected")
            self.size += 6
            self.weight = "bold"
            self.flush()
            self.title = True
            # self.cursor_y += VSTEP
            # self.cursor_x = WIDTH/2
        elif token.tag == '/h1':
            # print("Closing h1...")
            self.size -= 6
            self.weight = "normal"
            if self.title:
                n = len(self.line)
                lineWidth = self.line_width
                start = (WIDTH - lineWidth) / 2
                self.flush()
                for i in range (-1, (-1 * n) - 1, -1):
                    x, a, b, c = self.display_list[i]
                    print("Centering ", b)
                    self.display_list[i] = (x+start, a, b, c)
                self.title = False
            else:
                self.flush()
        elif "h1" in token.tag:
            print("hey, I'm normal")
            self.size += 6
            self.weight = "bold"
        elif token.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
    
    def processWord(self, word):
        myFont = self.getFont(self.size, self.weight, self.style)
        w = myFont.measure(word)
        space = myFont.measure(" ")

        if self.line and self.line_width + w > WIDTH - HSTEP:
            # print("Width: ",WIDTH)
            self.flush()
        self.line.append((word, myFont, w))
        self.line_width += w + space
        self.last_space = space
        
    def flush(self):
        if not self.line:
            return

        metrics = [font.metrics() for word, font, w in self.line]
        max_ascent = max(m["ascent"] for m in metrics)
        max_descent = max(m["descent"] for m in metrics)
        baseline = self.cursor_y + 1.25 * max_ascent

        if rtl:
            # total_width = sum(w for _, _, w in self.line) + self.last_space * (len(self.line) - 1)
            x = WIDTH - HSTEP - self.line_width
            for word, font, w in self.line:
                y = baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))
                x += w + self.last_space
        else:
            x = HSTEP
            for word, font, w in self.line:
                y = baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))
                x += w + font.measure(" ")

        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = WIDTH - HSTEP if rtl else HSTEP
        self.line = []
        self.line_width = 0

    def getFont(self,size, weight, style):
        key = (size, weight, style)
        if key not in FONTS:
            font = tkinter.font.Font(family="Finlandica Headline",size=size, weight=weight,
                slant=style)
            label = tkinter.Label(font=font)   # Dummy widget using the font for improved performance, as per official documentation
            FONTS[key] = (font, label)
        return FONTS[key][0]

def altLayout(text):
    display_list = []
    cursor_x, cursor_y = WIDTH - HSTEP, VSTEP
    print("hello from alt")
    if not text: return display_list
    for c in reversed(text):
        display_list.append((cursor_x, cursor_y, c))
        cursor_x -= HSTEP
        if cursor_x <= HSTEP:
            cursor_y += VSTEP
            cursor_x = WIDTH - HSTEP
    return display_list




if __name__ == "__main__":
    import sys
    import os
    if "-rtl" in sys.argv: rtl = True
    if len(sys.argv) < 2:
        Browser().dataLoad("Welcome to homepage")
    else:
        link = sys.argv[1]
        if isURL(link):
            headers = loadHeaders(sys.argv)
            browser = Browser()
            print("Loading url...")
            browser.load(URL(sys.argv[1]), headers, browser)
        elif isDataURI(link):   #done
            scheme, link = link.split(":", 1)
            fileType, content = link.split(",", 1)
            if fileType == "text/html":
                Browser().dataLoad(content)
                
        elif isViewSource(link):    #done
            scheme, viewUrl = link.split(":", 1)
            url = URL(viewUrl)
            headers = loadHeaders(sys.argv)
            Browser().srcLoad(url, headers)
        else:
            path = ""
            scheme = ""

            if(len(sys.argv) < 2):
                # open default
                f = open("default.txt", "r")
                txt = f.read()
                # print(txt)
                Browser().dataLoad(txt)
                f.close()
            elif "://" not in link:
                path = sys.argv[1]
                try:
                    # try relative path
                    root = os.getcwd()
                    root = os.path.join(root, path)
                    print(f"Root: {root} \tPath: {path}")
                    f = open(root, "r")
                    txt = f.read()
                    Browser().dataLoad(txt)
                    f.close()
                except FileNotFoundError:
                    Browser().dataLoad("File not found...")
            else:
                scheme, path = link.split("://", 1)
                if scheme != "file":
                    f = open("error.txt", "r")
                    txt = f.read()
                    Browser().dataLoad(txt)
                    f.close()
                try:
                    f = open(path, "r")
                    txt = f.read()
                    Browser().dataLoad(txt)
                    f.close()
                except FileNotFoundError:
                    Browser().dataLoad("File does not exist...")
    tkinter.mainloop()
