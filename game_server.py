import sys, socket, signal, json, MySQLdb
import masterConfig, errorCodes, dbConfig
from random import randint
from setup import setup
from thread import *

set = raw_input("Run Server Setup? \n")
if set in ["Yes", "yes", "Y", "y"]:
    setup()

roomToPort = dict()
usedPorts = []


# Intercept ^C to shut server down
def signalHandler(signal, frame):
    print("Closing server")
    sock.close()
    print("Socket closed")
    sys.exit(0)


signal.signal(signal.SIGINT, signalHandler)

def generateRoomName():
    roomNum = randint(0, 9999)
    if roomToPort.has_key(roomNum):
        return generateRoomName()
    else:
        return str(roomNum)

def generatePortNumber():
    port = randint(masterConfig.hostPort+1, masterConfig.hostPort+100)
    if port in usedPorts:
        return generatePortNumber()
    else:
        print("Generated: " + str(port))
        usedPorts.append(port)
        return port

def checkFields(message):
    return message.has_key("user") \
           and message.has_key("type")


def handleError(conn, returnMessage, errorCode, close=True):
    returnMessage.clear()
    returnMessage["status"] = "error"
    returnMessage["error"] = errorCode
    conn.send(json.dumps(returnMessage))
    if close:
        conn.close()


# Function for handling connections.
def handleInbound(conn):
    returnMessage = dict()
    returnMessage["status"] = "connected"
    conn.send(json.dumps(returnMessage))  # send only takes string

    data = conn.recv(2048)

    try:
        data = json.loads(data)
    except ValueError:
        print("Error parsing data")
        handleError(conn, returnMessage, errorCodes.jsonError)
        return
    else:
        pass

    if not checkFields(data):
        handleError(conn, returnMessage, errorCodes.missingDataField)
        return

    if data["user"] == "":
        handleError(conn, returnMessage, errorCodes.invalidUser)
        return

    type = data["type"]
    if type == "host":
        # TODO: Find new port, create session and send port back to host
        roomName = generateRoomName()
        roomPort = generatePortNumber()
        roomToPort[roomName] = roomPort
        ret = gameRoom(conn, roomPort, roomName, data["user"])

    elif type == "guest":
        # TODO: Get room code, find matching port and send back
        roomName = data["name"]
        try:
            roomPort = roomToPort[roomName]
        except KeyError as e:
            print("Room not found")
            handleError(conn, returnMessage, errorCodes.roomNotFound)
            return
        returnMessage.clear()
        returnMessage["status"] = "success"
        returnMessage["name"] = roomName
        returnMessage["port"] = roomPort
        conn.send(json.dumps(returnMessage))
    else:
        handleError(conn, returnMessage, errorCodes.invalidType)

def closeRoom(roomSocket, connectionList):
    for conn in connectionList:
        conn[0].close()
    roomSocket.close()

def gameRoom(conn, roomPort, roomName, hostName):
    # initial room setup
    returnMessage = dict()

    roomSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("binding with: " + str((masterConfig.host, str(roomPort))))
        roomSocket.bind((masterConfig.host, roomPort))
    except socket.error as e:
        print("Failed to bind socket. Error: " + str(e[0]) + " , " + e[1])
        handleError(conn, returnMessage, errorCodes.roomSocketError)
        roomToPort.pop(roomName)
        return errorCodes.roomSocketError
    print("Room created on port " + str(roomPort) + " for " + hostName)

    # let host know that room is ready
    returnMessage.clear()
    returnMessage["status"] = "success"
    returnMessage["port"] = roomPort
    returnMessage["name"] = str(roomName)
    conn.send(json.dumps(returnMessage))
    # Close this connection so that only the new game room is used
    conn.close()

    playerList = []
    connectionList = []

    wordList = createList()
    if len(wordList) == 0:
        a = 0
        # TODO: add error handling code for this case. Probably return server error to clients or take room down or something

    hostConnected = False
    numberOfPlayers = 0
    roomSocket.listen(10)
    print("Room " + roomName + " listening")
    # Wait for host to connect before letting anyone else in game room.
    # Need to get the number of players connecting from host
    while not hostConnected:
        conn, addr = roomSocket.accept()
        returnMessage = dict()
        returnMessage["status"] = "connected"
        conn.send(json.dumps(returnMessage))

        data = conn.recv(2048)

        try:
            data = json.loads(data)
        except ValueError:
            print("Error parsing data")
            handleError(conn, returnMessage, errorCodes.jsonError)
            continue
        else:
            # Valid json
            a = 0

        # TODO: add error checking if numberOfPlayers exceeds max allowed
        print("User " + data["user"] + " is attempting to connect")
        if data["user"] != hostName:
            handleError(conn, returnMessage, errorCodes.hostNotConnected)
        else:
            playerList.append(data["user"])
            connectionList.append((conn, addr))
            numberOfPlayers = data["numberOfPlayers"]

            returnMessage.clear()
            returnMessage["status"] = "success"
            conn.send(json.dumps(returnMessage))
            hostConnected = True

    print("Host connected to game room " + roomName)

    while len(playerList) != numberOfPlayers:
        conn, addr = roomSocket.accept()
        returnMessage = dict()
        returnMessage["status"] = "connected"
        conn.send(json.dumps(returnMessage))

        data = conn.recv(2048)

        try:
            data = json.loads(data)
        except ValueError:
            print("Error parsing data")
            handleError(conn, returnMessage, errorCodes.jsonError)
            return
        else:
            # Valid json
            a = 0

        # TODO: added error checking for badly formatted json or missing tags
        playerList.append(data["user"])
        connectionList.append((conn, addr))

    print("Players connected. Final list of players : " + str(playerList))
    # do stuff

    #temp code to test
    closeRoom(roomSocket, connectionList)
    return errorCodes.good


# Pull words from database and store in list for each session to use
# Will be modified later to enable constriants and modifiers
def createList():
    list = []

    try:
        db = MySQLdb.connect(dbConfig.dbHost, dbConfig.dbUser, dbConfig.dbPassword, dbConfig.dbName)
    except MySQLdb.Error as e:
        print("Unable to connect to database.\nReturning empty list.\nError message: ")
        print(e)
        return list

    dbCursor = db.cursor()
    sql = "SELECT word FROM wordbank"
    try:
        dbCursor.execute(sql)
    except MySQLdb.Error as e:
        print("Error fetching results from database. Probably SQL error.\nError message:")
        print(e)
        return list

    for word in dbCursor:
        list.append(word[0])

    return list


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")

try:
    sock.bind((masterConfig.host, masterConfig.hostPort))
except socket.error as e:
    print("Failed to bind socket. Error: " + str(e[0]) + " , " + e[1])
    print("Terminating program")
    sys.exit(-1)

usedPorts.append(masterConfig.hostPort)

print("Socket bound")

sock.listen(10)
print("Socket listening on port " + str(masterConfig.hostPort))

print("Close server with ^C")
while 1:
    conn, addr = sock.accept()

    start_new_thread(handleInbound, (conn,))

sock.close()
