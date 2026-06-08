from browser import Browser
from globals import rtl
from url import URL
import tkinter
import sys
import os
def main():
    # browser = Browser()
    # body = URL(sys.argv[1]).request({}, 1, browser)
    # nodes = HTMLParser(body).parse()
    # print_tree(nodes)
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
            browser = Browser()
            browser.srcLoad(url, headers,browser)
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
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
    
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


if __name__ == "__main__":
    main()