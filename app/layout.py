import tkinter
from globals import rtl, VSTEP, HSTEP, WIDTH
from parser import Text, Element

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
        self.sup = False
        self.store = {}
        self.abbrCnt = 0
        self.abbr = False
        self.pre = False
        self.title = False
        self.fonts = {}
        if not tokens:
            print("No response")
        else:
            self.recurse(tokens)
        self.flush()

    def recurse(self, tree):
        if isinstance(tree, Text):
            if not self.pre:
                for word in tree.text.split():
                    self.processWord(word)
            else:
                for word in tree.text:
                    self.processWord(word)
        else:
            self.open_tag(tree)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree)

    def open_tag(self, token):
        if token.tag == "i":
            self.style = "italic"
        elif token.tag == "b":
            self.weight = "bold"
        elif token.tag == "small":
            self.size -= 2
        elif token.tag == "big":
            self.size += 4
        elif token.tag == 'h1' and token.attributes.get("class") == "title":
            self.size += 6
            self.weight = "bold"
            self.flush()
            self.title = True
        elif "h1" in token.tag:
            self.size += 6
            self.weight = "bold"
        elif token.tag == "sup":
            self.size = int(self.size / 2)
            self.sup = True
        elif token.tag == "abbr":
            self.abbr = True
        elif token.tag == "pre":
            self.pre = True
        elif token.tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        elif token.tag == "br":
            self.flush()



    def close_tag(self, token):
        if token.tag == "i":
            self.style = "roman"
        elif token.tag == "b":
            self.weight = "normal"
        elif token.tag == "small":
            self.size += 2
        elif token.tag == "big":
            self.size -= 4
        elif token.tag == 'h1':
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
                    self.display_list[i] = (x+start, a, b, c)
                self.title = False
            else:
                self.flush()
        elif token.tag == "sup":
            self.size = self.size * 2
            self.sup = False
        elif token.tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        elif token.tag == "abbr":
            self.abbr = False
            num = self.abbrCnt - 1
            self.abbrCnt = 0
            for i in range (-1, (-1 * num) - 1, -1):
                x, a, b, c = self.display_list[i]
                self.display_list[i] = (x-self.last_space, a, b, c)
        elif token.tag == "pre":
                self.pre = False
    
    def processWord(self, word):
        myFont = self.getFont(self.size, self.weight, self.style)
        w = myFont.measure(word)
        space = myFont.measure(" ")
        if self.sup:
            self.store[word] = "sup"

        if self.line and self.line_width + w > WIDTH - HSTEP:
            soft = "\N{soft hyphen}"

            if soft in word:
                rem = WIDTH - HSTEP - self.line_width
                parts = word.split(soft)

                
                prefix = parts[0]
                idx = 1

                # Build the longest prefix that still fits with a visible hyphen
                while idx < len(parts):
                    trial = prefix + parts[idx]
                    if myFont.measure(trial + "-") <= rem:
                        prefix = trial
                        idx += 1
                    else:
                        break

                # If at least the prefix + hyphen fits, emit that part
                if myFont.measure(prefix + "-") <= rem:
                    hyphenated = prefix + "-"
                    self.line.append((hyphenated, myFont, myFont.measure(hyphenated)))
                    self.flush()

                    remainder = soft.join(parts[idx:])
                    if remainder:
                        self.processWord(remainder)
                    return
                
            self.flush()

        soft = "\N{soft hyphen}"
        if soft in word:
            parts = word.split(soft)
            word = "".join(parts)
            w = myFont.measure(word)

        if self.abbr:
            self.abbrProcess(word)
            return

        self.line.append((word, myFont, w))
        self.line_width += w + space
        self.last_space = space

            
    def abbrProcess(self, word):
        temp = ""
        upper = word[0].isupper()
        lower = word[0].islower()

        upperFont = self.getFont(self.size, self.weight, self.style)
        lowerFont = self.getFont(self.size - 4, "bold", self.style)  
        for letter in word:
            if letter.isupper() and upper:
                temp += letter
            if letter.islower() and lower:
                temp += letter
            elif letter.islower(): #lower but prev is upper
                upper = False
                lower = True
                text = temp.upper()
                w = lowerFont.measure(text)
                self.line.append((text, lowerFont,w))
                self.line_width += w
                temp = ""
                self.abbrCnt += 1
            elif letter.isupper(): #lower but prev is upper
                upper = True
                lower = False
                w = upperFont.measure(temp)
                self.line.append((temp, upperFont,w))
                self.line_width += w
                temp = ""
                self.abbrCnt += 1

        if temp:
            if upper:
                w = upperFont.measure(temp)
                self.line.append((temp, upperFont, w))
            else:
                text = temp.upper()
                w = lowerFont.measure(text)
                self.line.append((text, lowerFont, w))
            self.line_width += w
            self.abbrCnt += 1
        
    def flush(self):
        if not self.line:
            return

        metrics = [font.metrics() for word, font, w in self.line]
        max_ascent = max(m["ascent"] for m in metrics)
        max_descent = max(m["descent"] for m in metrics)
        baseline = self.cursor_y + 1.25 * max_ascent

        if rtl:
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
                # print(f"{word} added to display_list")
                x += w + font.measure(" ")
                if self.store.get(word):
                    x = self.fix(word, font, w, x, y, self.store.get(word))

        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = WIDTH - HSTEP if rtl else HSTEP
        self.line = []
        self.line_width = 0

    def fix(self, word, font, width, x, y, operation):
        if(operation == "sup"):
            prevWord = self.display_list[-2] #last word is current word, prev word is behind that
            baseline = y + font.metrics("ascent")
            y = baseline - prevWord[3].metrics("ascent") 
            a, b, c, d = self.display_list[-1]
            self.display_list.pop(-1)
            self.display_list.append((a,y, c, d))
            del self.store[word]
            return x

    def getFont(self,size, weight, style):
        key = (size, weight, style)
        if key not in self.fonts:
            font = tkinter.font.Font(family="Finlandica Headline",size=size, weight=weight,
                slant=style)
            label = tkinter.Label(font=font)   # Dummy widget using the font for improved performance, as per official documentation
            self.fonts[key] = (font, label)
        return self.fonts[key][0]
