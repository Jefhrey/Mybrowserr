import socket

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = socket.socket(
                        family = socket.AF_INET,
                        type = socket.SOCK_STREAM,
                        proto = socket.IPPROTO_TCP)
        self.server.bind(("localhost", 9000))
        self.server.listen()
        self.clients = []

        while True:
            client, address = self.server.accept()
            print("Client Address:", address)
            self.handle_client(client)

    def handle_client(self, client):
        """
        Example Request:
            GET /wiki/List_of_days_of_the_year HTTP/1.1
            Host: en.wikipedia.org
            Connection: keep-alive
            User-Agent: Jef
            Accept-Encoding: gzip
        """
        request = client.makefile('rb', newline = "\r\n")

        statusLine = request.readline().decode("utf8")
        method, target, protocol = statusLine.split()
        headers = {}
        while True:
            line = request.readline().decode("utf8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            headers[header.casefold()] = value.strip()

        if method == "GET": self.get(client, target, headers)
        return

    def get(self, client, target, headers):

        # prepare response
        _, path = target.split("/", 1) 
        path += ".html"
        body = ""
        with open(path, "rb") as f:
            body = f.read()
        
        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Length: {len(body)}\r\n"
        response += "Content-Type: text/html; charset=utf-8\r\n"
        response += "\r\n"
        client.send(response.encode("utf8") + body)
        return



if __name__ == "__main__":
    print("Starting server...")
    server = Server("localhost", 9000)

