import tkinter
import emoji
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
from layout import Layout
from parser import HTMLParser, SrcParser
from url import URL
from globals import VSTEP, SCROLL_STEP, WIDTH, HEIGHT
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.geometry(f"{WIDTH}x{HEIGHT}")
        bi_times = tkinter.font.Font(family="Finlandica Headline",size=16)
        self.font = bi_times

        self.top_frame = tkinter.Frame(self.window, bg = "#aeaca5", height = 40)
        self.top_frame.pack_propagate(False)
        self.search_bar = tkinter.Entry(self.top_frame)
        self.go_button = tkinter.Button(self.top_frame, text="Go", command = self.search)
        
        self.bottom_frame = tkinter.Frame(self.window, bg = "#f9f3de")

        self.canvas = tkinter.Canvas(
            self.bottom_frame, 
            width=WIDTH,
            bg = "#f9f3de"
        )

        self.scroll = 0
        self.scrollbar = tkinter.Scrollbar(self.bottom_frame, orient= "vertical", command = self.scrollMaster, bg = "black")
        self.top_frame.pack(side="top", fill = "x")
        self.bottom_frame.pack(side="top", fill="both", expand=True)
        self.search_bar.pack(side="left", fill = "x", expand = "True", padx = 5)
        self.go_button.pack(side="right")
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll = 0

        self.emojis = []
        self.canvas.bind("<Down>", self.scrolldown)
        self.canvas.bind("<Up>", self.scrollup)
        self.canvas.bind("<Button-4>", self.scrollup)
        self.canvas.bind("<Button-5>", self.scrolldown)
        self.canvas.bind("<Configure>", self.resize)  
        self.search_bar.bind("<Return>", self.search)  
        self.canvas.bind("<End>", self.scrollEnd)
        self.canvas.bind("<Home>", self.scrollTop)

        self.canvas.focus_set()
        self.canvas.bind(
            "<Button-1>",
            lambda e: self.canvas.focus_set()
        )
    
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
        if not hasattr(self, 'nodes'): return
        self.display_list = Layout(self.nodes).display_list
        self.canvas.delete("all")
        self.draw()

    def load(self, url, headers, browser):        
        body = url.request(headers, 0, browser)
        self.canvas.delete("all")
        self.search_bar.delete(0, tkinter.END)
        self.search_bar.insert(0, url.url)
        self.nodes = HTMLParser(body).parse()
        # print_tree(self.nodes)
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    def search(self, e=None):
        url = self.search_bar.get().strip()
        if not url:
            return

        self.load(URL(url), {}, self)

    def srcLoad(self, url, headers, browser):
        body = url.request(headers, 0, browser)
        self.nodes = SrcParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    def dataLoad(self, text):
        # self.tokens = lex(text)
        # self.display_list = Layout(self.tokens).display_list
        # self.draw()
        return

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
        
        for x, y, c, font in self.display_list:
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

# weight = "normal"
# style = "roman"
