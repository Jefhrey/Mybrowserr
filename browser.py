import socket
import ssl
import os
import sys

sockets = {}

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
    
    def request(self, headers, attempt):

        if(attempt > 5):
            print("Too many redirects...")
            return 0
        key = self.host + ":" + str(self.port)
        s = sockets.get(key)
        if not s:
            s = socket.socket(
                family = socket.AF_INET,
                type = socket.SOCK_STREAM,
                proto = socket.IPPROTO_TCP)
            s.connect((self.host, self.port))
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)  
            sockets[key] = s      

        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\nConnection: keep-alive\r\n"
        request += f"User-Agent: Jef\r\n"
        # Adding headers
        request = self.addHeaders(request, headers)
        request += "\r\n"
        print("The final request:\n", request)
        s.send(request.encode("utf8"))
        
        response = s.makefile('rb', newline = "\r\n")
        statusline = response.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        statusCode = int(status)
        if statusCode >= 300 and statusCode < 400 and attempt < 5:
            path = response_headers["location"]
            # redirect until success
            # Destination can be absolute or relative
            if path.startswith("http://") or path.startswith("https://"):
                # send it over
                nextHop = response_headers["location"]
                return URL(nextHop).request({}, attempt + 1)  # pass attempt count down
            else:
                # relative path.
                self.path = path
                return self.request({}, attempt + 1)

        content = ""
        msgLen = response_headers.get("content-length")
        if not msgLen:
            content = response.read().decode("utf8")
        else:
            content = response.read(int(msgLen)).decode("utf8")
        # s.close()
        return content

def show(body):
    in_tag = False
    body = body.replace("&lt;", "<")
    body = body.replace("&gt;", ">")
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url, headers):
    body = url.request(headers, 0)
    show(body)

def viewLoad(url, headers):
    body = url.request(headers, 0)
    print(body)

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

def loadFile(url):
    path = ""
    scheme = ""

    if(len(sys.argv) < 2):
        # open default
        f = open("default.txt", "r")
        txt = f.read()
        print(txt)
        f.close()
    elif "://" not in url:
        path = sys.argv[1]
        try:
            # try relative path
            root = os.getcwd()
            root = os.path.join(root, path)
            print(f"Root: {root} \tPath: {path}")
            f = open(root, "r")
            txt = f.read()
            print(txt)
            f.close()
        except FileNotFoundError:
            print("File not found...")
    else:
        scheme, path = url.split("://", 1)
        if scheme != "file":
            f = open("error.txt", "r")
            txt = f.read()
            print(txt)
            f.close()
            return
        try:
            f = open(path, "r")
            txt = f.read()
            print(txt)
            f.close()
        except FileNotFoundError:
            print("File does not exist...")
                
def isDataURI(arg):
    return arg.startswith("data:")
    # if "data:" not in arg:
    #     return False
    
    # scheme, text = arg.split(":", 1)
    # if(scheme == "data"): 
    #     return True
    

def isViewSource(arg):
    if "view-source:" not in arg: return False
    else: return True

if __name__ == "__main__":
    import sys
    import os
    if(len(sys.argv) < 2):
        loadFile("")
    else:
        link = sys.argv[1]
        if isURL(link):
            print("Link detected")
            url = URL(sys.argv[1])
            headers = loadHeaders(sys.argv)
            load(url, headers)

        elif isDataURI(link):
            print("Data URI detected")
            scheme, link = link.split(":", 1)
            fileType, content = link.split(",", 1)
            if(fileType == "text/html"):
                print(content)
        elif isViewSource(link):
            scheme, viewUrl = link.split(":", 1)
            url = URL(viewUrl)
            headers = loadHeaders(sys.argv)
            viewLoad(url, headers)
        else:
            print("File detected")
            loadFile(link)