from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory

class ChatProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.name = None
        self.state = "REGISTER"

    def connectionMade(self):
        self.sendLine("What's your name?".encode('utf8'))
    
    def connectionLost(self, reason):
        if self.name in self.factory.users:
            del self.factory.users[self.name]
            self.broadcastMessage(f"{self.name} has left the channel.".encode('utf8'))
    
    def lineReceived(self, line):
        line = bytes.decode(line)
        if self.state == "REGISTER":
            self.handle_REGISTER(line)
        else:
            self.handle_CHAT(line)
            self.transport.write(f'<{self.name}> '.encode('utf8'))

    def handle_REGISTER(self, name):
        if name in self.factory.users:
            self.sendLine("Name taken, please choose another.".encode('utf8'))
            return
        self.sendLine(f"Welcome, {name}!".encode('utf8'))
        self.broadcastMessage(f"{name} has joined the channel.".encode('utf8'))
        self.name = name
        self.factory.users[name] = self
        self.state = "CHAT"
        self.transport.write(f'<{self.name}> '.encode('utf8'))

    def handle_CHAT(self, message):
        message = f"<{self.name}> {message}".encode('utf8')
        self.broadcastMessage(message)
    
    def broadcastMessage(self, message):
        for name, protocol in self.factory.users.items():
            if protocol != self:
                protocol.sendLine(message)

class ChatFactory(Factory):
    def __init__(self):
        self.users = {}
    
    def buildProtocol(self, addr):
        return ChatProtocol(self)

reactor.listenTCP(8000, ChatFactory())
reactor.run()