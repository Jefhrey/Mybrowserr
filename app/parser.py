class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
        self.SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",]
        self.HEAD_TAGS =  [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",]
        self.SIBILINGS = ["p", "li"]
        self.js = False
        self.in_tag = False
        self.comment = False
        self.TEXT_FORMAT = ["b", "i", "/b", "/i"]
        self.txt_track = []
    def parse(self):
        self.text = ""
        for c in self.body:
            # print(self.text)
            if self.is_ignore(c):
                continue
            elif c == "<":
                self.in_tag = True
                if self.text: self.add_text(self.text)
                self.text = ""
            elif c == ">":
                self.in_tag = False
                if self.handle_txt_format():
                    continue
                self.add_tag(self.text)
                self.text = ""
            else:
                self.text += c
        if not self.in_tag and self.text:
            self.add_text(self.text)
        return self.finish()
                

    def handle_txt_format(self):
        # Check if txt tag
        if self.text not in self.TEXT_FORMAT:
            return False
        if not self.text.startswith("/"):
            self.txt_track.append(self.text)
            return False
        if not self.txt_track:
            return False
        # We have a closing tag, with a non empty track
        dad = self.txt_track[-1]
        if ("/" + dad) == self.text:
            return False
        else:
            # Close the dad tag, open the curr tag and then reopen the dad tag
            self.add_tag("/" + dad)
            self.add_tag(self.text)
            self.add_tag(dad)
            self.text = ""
            return True
        
    def is_ignore(self, c):
        if c == "<":
            # is already comment or script
            if self.comment or self.js:
                self.text += c
                return True
        
        if c == ">":
            # does it end a comment?
            if self.comment and self.text.endswith("--"):
                self.comment = False
                # TODO: handle comment node
                self.text = ""
                return True
            # does it end a script?
            elif self.js and self.text.endswith("</script"):
                self.js = False
                script = self.text[:-7]
                # Add the script tag
                tag = script.split(">", 1)[0]
                self.add_tag(tag)
                self.text = ""
                return True
            # Is a script starting?
            if self.in_tag and self.text.startswith("script"):
                self.js = True
                self.add_tag(self.text)
                self.in_tag = False
                self.text = ""
                return True
            
        if self.comment or self.js:
            self.text += c
            return True
        # Is a comment starting?
        if self.in_tag and self.text.startswith("!--"):
            self.comment = True
            self.text += c
            return True
        return False
                
    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)   # adds any missing implicts tags
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()     #the opening tag of the current node
            parent = self.unfinished[-1]  
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes,parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            if (tag in self.SIBILINGS and parent.tag == tag):
                # Close the preivous tag, make it a sibiling
                parent = self.unfinished[-2]
                node = self.unfinished.pop()
                parent.children.append(node)
            node = Element(tag,attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] \
                and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and \
                tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def get_attributes(self, text):
        temp = text
        tag = temp.split()[0]
        temp = temp[len(tag):].strip()

        attributes = {}
        i = 0
        n = len(temp)

        while i < n:
            while i < n and temp[i].isspace():
                i += 1
            if i >= n:
                break

            # read attribute name
            start = i
            while i < n and temp[i] not in ["=", " "]:
                i += 1
            key = temp[start:i].strip()

            while i < n and temp[i].isspace():
                i += 1

            # boolean attribute: no value
            if i >= n or temp[i] != "=":
                if key:
                    attributes[key] = ""
                continue

            i += 1  # skip '='
            while i < n and temp[i].isspace():
                i += 1

            if i >= n:
                attributes[key] = ""
                break

            # quoted value
            if temp[i] in ['"', "'"]:
                quote = temp[i]
                i += 1
                start = i
                while i < n and temp[i] != quote:
                    i += 1
                value = temp[start:i]
                i += 1  # skip closing quote
            else:
                # unquoted value
                start = i
                while i < n and not temp[i].isspace():
                    i += 1
                value = temp[start:i]

            attributes[key] = value

        return tag, attributes
          
class SrcParser(HTMLParser):
    def parse(self):
        self.text = ""
        for c in self.body:
            if self.is_ignore(c):
                continue
            elif c == "<":
                self.in_tag = True
                if self.text:
                    self.add_tag("pre") 
                    self.add_tag("b")
                    self.add_text(self.text)
                    self.add_tag("/b")
                    self.add_tag("/pre") 
                self.text = ""
            elif c == ">":
                self.in_tag = False
                self.add_tag("br")
                self.add_text("<" + self.text + ">")
                self.add_tag("br")
                self.text = ""
            else:
                self.text += c
        if not self.in_tag and self.text:
            self.add_text(self.text)
        return self.finish()
    
    def is_ignore(self, c):
        if c == "<":
            # is already comment or script
            if self.comment or self.js:
                self.text += c
                return True
        
        if c == ">":
            # does it end a comment?
            if self.comment and self.text.endswith("--"):
                self.comment = False
                # TODO: handle comment node
                self.add_tag("br")
                self.add_text( "<" + self.text + ">")
                self.text = ""
                return True
            # does it end a script?
            elif self.js and self.text.endswith("</script"):
                self.js = False
                script = self.text.split("</script", 1)[0]
                self.add_tag("b")
                self.add_tag("pre")
                self.add_text(script)
                self.add_tag("/b")
                self.add_tag("/pre")
                self.add_tag("br")
                self.add_text("</script>")
                self.add_tag("br")
                self.text = ""
                # Add the script tag

                return True
            # Is a script starting?
            if self.in_tag and self.text.startswith("script"):
                self.js = True
                self.add_tag("br")
                self.add_text("<" + self.text + ">")
                self.add_tag("br")
                self.in_tag = False
                self.text = ""
                return True
            
        if self.comment or self.js:
            self.text += c
            return True
        # Is a comment starting?
        if self.in_tag and self.text.startswith("!--"):
            self.comment = True
            self.text += c
            return True

        return False

class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes,parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "<" + self.tag + ">"