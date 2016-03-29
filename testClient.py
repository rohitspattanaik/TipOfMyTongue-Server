import socket, json, sys, time
import errorCodes, masterConfig


def getType():
    type = raw_input("Are you a host or a guest?")
    if type != "host" and type != "guest":
        print("The only options are host or guest. Try again")
        return getType()
    else:
        return type


def connectToRoom(roomName, roomPort, name, host=False, numPlayers=1):
    print("trying to connect on port: " + str(roomPort))
    roomSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    roomSock.connect((masterConfig.host, roomPort))

    data = roomSock.recv(2048)
    try:
        data = json.loads(data)
    except ValueError:
        print("Error parsing data")
        sys.exit(-1)
    else:
        pass

    if data["status"] == "connected":
        message = dict()
        message["user"] = name
        message["numberOfPlayers"] = numPlayers
        roomSock.send(json.dumps(message))
    else:
        return None

    data = roomSock.recv(2048)
    data = json.loads(data)
    if data["status"] == "success":
        return roomSock
    else:
        return None


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

    roomName = data["name"]
    roomPort = data["port"]
    print("Your game room is: " + roomName)
    numOfPlayers = int(input("How many guests do you have?(max 4)?\n")) + 1
    print("Give the room name to anyone else who wants to connect as a guest")
    sock.close()
    roomSock = connectToRoom(roomName, roomPort, name, True, numOfPlayers)
    if roomSock == None:
        print("Could not connect to room. Exiting")
        sys.exit(-1)
    return roomSock


def playAsGuest(sock, name):
    roomName = raw_input("Which room do you want to connect to?\n")
    message = dict()
    message["user"] = name
    message["type"] = "guest"
    message["name"] = roomName
    sock.send(json.dumps(message))

    data = sock.recv(2048)
    data = json.loads(data)
    roomPort = 0
    if data["status"] == "error":
        if data["error"] == errorCodes.roomNotFound:
            print("Server could not find this room")
        else:
            print("Unknown error")
        sys.exit(-1)

    roomPort = data["port"]
    sock.close()
    roomSock = connectToRoom(roomName, roomPort, name)
    if roomSock == None:
        print("Could not connect to room. Exiting")
        sys.exit(-1)
    return roomSock


def playGame(roomSocket, name, type):
    continueGame = True
    returnMessage = dict()
    while continueGame:
        data = roomSocket.recv(2048)
        try:
            data = json.loads(data)
        except ValueError:
            print("Error parsing data")
            sys.exit(-1)
        else:
            pass

        if data["status"] == "error":
            if data["error"] == errorCodes.roomShutdown:
                print("Success")
                return

        # if data["status"] == "game":
        #     prompt = raw_input("Enter a message\n")
        #     returnMessage = dict()
        #     returnMessage["user"] = name
        #     returnMessage["data"] = prompt
        #     roomSocket.send(json.dumps(returnMessage))
        #     continue

        if data["status"] == "end":
            print("Game ended by server")
            roomSocket.close()
            continueGame = False
            continue

        if data["status"] == "begin":
            print("Game starting!\n\n")
            print("Here are the rules:\n")
            print("Each round will have one judge.\n")
            print("Everyone else will get a word  or group of words.\n")
            print("They have to write down what they think the word(s) mean.\n")
            print("You only get one shot! You can't write down multiple answers, so pick your best one.")
            print("Once everyone has entered an answer, the judge will pick what they like the best.\n")
            print("Then we choose another judge and go again! The game ends after %d cycles.\n" % data["rounds"])
            print("The player who was the most chosen wins!\n\n")
            continue

        if data["status"] == "word:":
            if data["judge"] == name:
                print("\nPsst! You're the judge this round!\n")
                print("You can't enter an answer so sit tight until everyone is done.\n")
                print("Here's what everyone is thinking about right now: \n")
                print(data["word"] + "\n\n")
                returnMessage.clear()
                returnMessage["user"] = name
                returnMessage["data"] = "NULL"
                roomSocket.send(json.dumps(returnMessage))
            else:
                print("What do you think this is?\n")
                print(data["word"] + "\n")
                time.sleep(2)
                answer = raw_input("Enter your answer now:\n")
                returnMessage.clear()
                returnMessage["user"] = name
                returnMessage["data"] = answer
                roomSocket.send(json.dumps(returnMessage))
            continue

        if data["status"] == "judge":
            defPairs = data["definitions"]
            if data["judge"] != name:
                print("The judge is going through the answers!\n")
                print("Here's what everyone wrote:\n")
                for i in range(0, len(defPairs)):
                    print(("\t%d" % i + 1) + defPairs[i][1] + "\n\n")
                returnMessage.clear()
                returnMessage["user"] = name
                returnMessage["data"] = "NULL"
                roomSocket.send(json.dumps())
            else:
                print("Now it's your turn!\n")
                print("Here's what everyone else wrote. Pick the one that you like best.\n")
                for i in range(0, len(defPairs)):
                    print(("\t%d" % i + 1) + defPairs[i][1] + "\n\n")
                answer = raw_input("Pick an answer by typing in the number in front of it.\n")
                goodAnswer = (answer > 0 and answer <= len(defPairs)) and answer.isdigit()
                while not goodAnswer:
                    answer = raw_input("That's not a valid option. Choose again.\n")
                    goodAnswer = (answer > 0 and answer <= len(defPairs)) and answer.isdigit()
                returnMessage.clear()
                returnMessage["user"] = name
                returnMessage["data"] = defPairs[answer - 1]
                roomSocket.send(json.dumps(returnMessage))


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

try:
    name = raw_input("What's your name?\n")
except:
    print("Error with input. Exiting")
    e = sys.exc_info()[0]
    print(e)
    sys.exit(-1)
type = getType()
if type == "host":
    sock = playAsHost(sock, name)

elif type == "guest":
    # do guest stuff
    sock = playAsGuest(sock, name)
print("playing game")
playGame(sock, name, type)
