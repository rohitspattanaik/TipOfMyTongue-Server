import sys, socket, signal, json, MySQLdb, time
import masterConfig, errorCodes, dbConfig
from random import randint
from setup import dbSetup
from thread import *

set = raw_input("Run Server DB Setup? \n")
if set in ["Yes", "yes", "Y", "y"]:
    dbSetup()

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
    conn.sendall(json.dumps(returnMessage))
    if close:
        conn.close()


# Function for handling connections.
def handleInbound(conn):
    returnMessage = dict()
    returnMessage["status"] = "connected"
    conn.sendall(json.dumps(returnMessage))  # sendall only takes string

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
        roomName = generateRoomName()
        roomPort = generatePortNumber()
        roomToPort[roomName] = roomPort
        ret = gameRoom(conn, roomPort, roomName, data["user"])
        if ret == errorCodes.good:
            print("Game ended in room " + str(roomName) + " successfully")
            return

    elif type == "guest":
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
        conn.sendall(json.dumps(returnMessage))
    else:
        handleError(conn, returnMessage, errorCodes.invalidType)

def closeRoom(roomSocket, connectionList):
    returnMessgae = dict()
    returnMessgae["status"] = "error"
    returnMessgae["error"] = errorCodes.roomShutdown
    for conn in connectionList:
        conn[1][0].sendall(json.dumps(returnMessgae))
        conn[1][0].close()
    roomSocket.close()

def getRandomWord(wordList, usedWords):
    randIndex = randint(0, len(wordList) - 1)
    if wordList[randIndex] in usedWords:
        return getRandomWord(wordList, usedWords)
    else:
        return wordList[randIndex]

def playGame(roomSocket, connectionList):
    wordList = createList()
    usedWords = []
    returnMessage = dict()
    returnMessage["status"] = "begin"
    returnMessage["recipient"] = "all"
    returnMessage["rounds"] = masterConfig.maxNumberOfRounds  #this is only for now until the game is ready. Normally would be upto the host
    messageRoom(connectionList, returnMessage.copy())
    time.sleep(2)
    round = 0

    userScores = dict()
    for user in connectionList:
        userScores[user[0]] = 0

    while round < masterConfig.maxNumberOfRounds:  #again, temporary
        # print("starting a round")
        judgeIndex = 0
        while judgeIndex < len(connectionList):
            # print("starting a cycle")
            word = getRandomWord(wordList, usedWords)
            usedWords.append(word)
            judgeName = connectionList[judgeIndex][0]
            returnMessage.clear()
            returnMessage["status"] = "word"
            returnMessage["judge"] = judgeName
            returnMessage["recipient"] = "all"
            returnMessage["word"] = word
            messageRoom(connectionList, returnMessage.copy())
            # print("sendall word to room")
            userDefinitions = getRoomResults(connectionList)
            userDefinitions.pop(judgeName)
            # print("got word results from room")
            returnMessage.clear()
            returnMessage["status"] = "judge"
            returnMessage["recipient"] = "all"
            returnMessage["judge"] = judgeName
            returnMessage["definitions"] = userDefinitions.items()
            messageRoom(connectionList, returnMessage.copy())
            # print("sent info to judge")
            judgeResult = getRoomResults(connectionList)
            # print("got judge stuff back")

            winner = judgeResult[judgeName][0]
            userScores[winner] += 1
            returnMessage.clear()
            returnMessage["status"] = "result"
            returnMessage["winnerName"] = winner
            returnMessage["definitions"] = userDefinitions.items()
            messageRoom(connectionList, returnMessage.copy())
            #adding this cause of a weird problem where score isn't getting send at the end of a round
            #putting this in fixes that for some reason so it stays for now
            result = getRoomResults(connectionList)

            judgeIndex += 1

        returnMessage.clear()
        returnMessage["status"] = "score"
        returnMessage["score"] = userScores
        messageRoom(connectionList, returnMessage.copy())

        round += 1

def gameRoom(conn, roomPort, roomName, hostName):
    # initial room setup
    returnMessage = dict()

    roomSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #print("binding with: " + str((masterConfig.host, str(roomPort))))
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
    conn.sendall(json.dumps(returnMessage))
    # Close this connection so that only the new game room is used
    conn.close()

    #playerList = []
    connectionList = []

    hostConnected = False
    numberOfPlayers = 0
    roomSocket.listen(10)
    print("Room " + roomName + " listening")

    # Wait for host to connect before letting anyone else in game room.
    # Need to get the number of players connecting from host
    while not hostConnected:
        conn, addr = roomSocket.accept()
        print("Guest attempting to connect in room " + roomName)
        returnMessage = dict()
        returnMessage["status"] = "connected"
        conn.sendall(json.dumps(returnMessage))

        data = conn.recv(2048)

        try:
            data = json.loads(data)
        except ValueError:
            print("Error parsing data")
            handleError(conn, returnMessage, errorCodes.jsonError)
            continue
        else:
            pass

        # TODO: add error checking if numberOfPlayers exceeds max allowed
        print("User " + data["user"] + " is attempting to connect")
        if data["user"] != hostName:
            handleError(conn, returnMessage, errorCodes.hostNotConnected)
        else:
            #playerList.append(data["user"])
            connectionList.append((data["user"], (conn, addr)))
            numberOfPlayers = data["numberOfPlayers"]

            returnMessage.clear()
            returnMessage["status"] = "success"
            conn.sendall(json.dumps(returnMessage))
            hostConnected = True

    print("Host connected to game room " + roomName)

    while len(connectionList) != numberOfPlayers:
        connG, addrG = roomSocket.accept()
        returnMessage.clear()
        returnMessage["status"] = "connected"
        connG.sendall(json.dumps(returnMessage))

        data = connG.recv(2048)
        try:
            data = json.loads(data)
        except ValueError:
            print("Error parsing data")
            handleError(connG, returnMessage, errorCodes.jsonError)
            return
        else:
            pass
        #playerList.append(data["user"])
        connectionList.append((data["user"], (connG, addrG)))
        returnMessage.clear()
        returnMessage["status"] = "success"
        connG.sendall(json.dumps(returnMessage))

    print("Players connected. Final list of players : " + str(connectionList))

    playGame(roomSocket, connectionList)
    closeRoom(roomSocket, connectionList)

    #test stuff
    # returnMessage.clear()
    # returnMessage["status"] = "game"
    # messageRoom(connectionList, returnMessage)
    # testPrompts = getRoomResults(connectionList)
    # print("Got back from room:")
    # print(str(testPrompts))
    # returnMessage.clear()
    # returnMessage["status"] = "end"
    # messageRoom(connectionList, returnMessage)
    # closeRoom(roomSocket, connectionList)
    return errorCodes.good

#the return message passed to this function should be populated already
def messageRoom(connectionList, returnMessage):
    for conn in connectionList:
        conn[1][0].sendall(json.dumps(returnMessage))

def getUserResult(conn, resultList):
    data = conn.recv(4096)
    print(str(data))
    try:
        data = json.loads(data)
    except ValueError as e:
        print("Error parsing data")
        print("Error: " + str(e))
        #TODO: figure out how to handle
    else:
        pass
    print(str(data))
    resultList[data["user"]] = data["data"]
    return


def getRoomResults(connectionList):
    roomResults = dict()
    for conn in connectionList:
        start_new_thread(getUserResult, (conn[1][0], roomResults,))
    while len(roomResults) != len(connectionList):
        #Busy wait for now
        pass
    return roomResults

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
