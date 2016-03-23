import socket, json, sys
import errorCodes, masterConfig

def getType():
    type = input("Are you a host or a guest?")
    if type != "host" or type != "guest":
        print("The only options are host or guest. Try again")
        return getType()
    else:
        return type

def connectToRoom(roomName, roomPort, host = False, numPlayers = 0):
    message = dict()

    return 0


def playAsHost(sock, name):
    message = dict()
    message["user"] = name
    message["type"] = "host"
    sock.send(json.dumps(message))

    data = sock.recv(2048)
    data = json.loads(data)
    roomPort = 0
    roomName = ""
    if data["status"] == "error":
        print("Unknown error")
        sys.exit(-1)
    elif data["status"] == "success":
        roomName = data["roomName"]
        roomPort = data["roomPort"]
        print("Your game room is: " + roomName)
        numOfPlayers = int(input("How many guests do you have (max 4)?\n")) + 1
        print("Give this name to anyone else who wants to connect as a guest")
        sock.close()
        roomSock = connectToRoom(roomName, roomPort, True, numOfPlayers)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((masterConfig.host, masterConfig.hostPort))

data = sock.recv(2048)
try:
    data = json.loads(data)
except ValueError:
    print("Error parsing data")
    sys.exit(-1)
else:
    pass

if data["status"] != "connected":
    print("Error connecting with server. Closing program")
print("Connected to server")

name = input("What's your name?\n")
getType()
if type == "host":
    playAsHost(sock, name)

elif type == "guest":
    #do guest stuff
    pass