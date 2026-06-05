# Toy Browser

A Python browser built while following *Web Browser Engineering* through chapter 4.

## Features

- Parses `http` and `https` URLs and sends raw HTTP/1.1 GET requests over sockets.
- Supports custom request headers, redirects, gzip-compressed responses, chunked transfer encoding, and `Content-Length` responses.
- Caches cacheable responses in memory using `Cache-Control` and `Age`.
- Builds a DOM-like tree with `Text` and `Element` nodes.
- Handles implicit tags such as `html`, `head`, and `body`.
- Recognizes self-closing tags, sibling tags like `p` and `li`, HTML comments, and basic script handling.
- Supports `view-source:` mode to display source with special formatting.
- Uses a layout engine to render text onto a Tkinter canvas.
- Supports inline formatting such as `b`, `i`, `small`, `big`, `sup`, `abbr`, and `pre`.
- Wraps text, handles simple line layout, and supports Right to Left rendering.
- Includes scrolling, scrollbar interaction, keyboard navigation, and window resize support.

## Implementation Notes

- `URL` handles parsing, networking, headers, redirects, caching, and decoding.
- `HTMLParser` converts HTML into a tree structure.
- `SrcParser` renders source code in a readable way.
- `Layout` converts the tree into positioned drawable text.
- `Browser` owns the Tkinter UI, canvas drawing, scroll state, and event bindings.

## Status

This is an educational browser, not a production browser. It is intentionally incomplete but already demonstrates request handling, parsing, layout, and rendering in one pipeline.