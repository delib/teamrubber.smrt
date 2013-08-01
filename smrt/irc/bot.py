from multiprocessing import Process, Pipe
import select, socket, string, sys
from threading import Thread

class IRC(object):

    host = None
    port = 0
    nick = None
    ident = None
    realname= None
    chan = None
    readbuffer = ""
    socket = None
    thread = None
    instance = None
    latest = None
    running = True

    def __init__(self):
        if IRC.instance == None:
            IRC.instance = self
        self.socket = socket.socket()
        self.socket.settimeout(10)
        self.socket.connect((self.host, self.port))
        self.socket.send("USER %s * * :%s\r\n" % (self.ident, self.realname))
        self.socket.send("NICK %s\r\n" % self.nick)
        # Start thread
        self.thread = Thread(target=self.listen)
        self.thread.start()


    def listen(self):
        while self.running:
            try:
                self.readbuffer += self.socket.recv(1024)
                parts = self.readbuffer.split("\n")
                self.readbuffer = parts.pop()
                if len(parts) > 0:
                    for msg in parts:
                        if "PING " in msg:
                            self.send("PONG " + msg.split("PING ")[1])
                        elif "End of message of the day." in msg:
                            self.send("JOIN " + self.chan)
                        else:
                            self.incoming(msg)
            except Exception as e:
                pass

                
    def send(self, message):
        self.socket.send(message + "\r\n")


    def incoming(self, message):
        try:
            if ("@" in message or self.nick in message) and "privmsg" in message.lower():
                if "help" in message or "man" in message:
                    user_str = ":%s!%s@smrt PRIVMSG %s :" % (self.nick, self.ident, self.chan)
                    # Either send me the command 'refresh' or 'view <project> <milestone> <date>, not entering date will just show the latest day.
                    self.send(user_str + "Help:")
                    self.send(user_str + "* 'refresh' to reload the current screen")
                    self.send(user_str + "* 'view <project> <milestone> <date>' to change the current view, exclude the date to show the latest day.")
                    self.send(user_str + "* 'panels add row' to add a new panel row.")
                    self.send(user_str + "* 'panels add col to <row_index> <web_address>' to add a new column to a row with an address")
                    self.send(user_str + "* 'panels set row <row_index> col <col_index> <web_address>' to change the current view in a panel/row")
                    self.send(user_str + "* 'panels clear' to reset back to a single panel")
                else:
                    self.latest = message.split(self.chan + " :" + self.nick)[1]
        except Exception as e:
            print "Oops message error: " + e


    def stop(self):
        self.running = False
        self.socket.close()

