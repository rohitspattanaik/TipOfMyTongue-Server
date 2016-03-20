import sys, socket, signal, json
import masterConfig, errorCodes
from thread import *

roomToPort = dict()

#Intercept ^C to shut server down
def signalHandler(signal, frame):
    print("Closing server")
    sock.close()
    print("Socket closed")
    sys.exit(0)
signal.signal(signal.SIGINT, signalHandler)

#Function for handling connections. This will be used to create threads
def handleInbound(conn):
    returnMessage = dict()
    returnMessage["status"] = "connected"
    conn.send(json.dumps(returnMessage)) #send only takes string

    data = conn.recv(1024)

    try:
        data = json.loads(data)[0]
    except:
        print("Error parsing data")
        returnMessage.clear()
        returnMessage["status"] = "error"
        returnMessage["error"] = errorCodes.jsonError
        conn.send(json.dumps(returnMessage))
        conn.close()
        return

    if data["users"] == "":
        returnMessage.clear()
        returnMessage["error"] = str(errorCodes.invalidUser)
        conn.send(json.dump(returnMessage))
        conn.close()
        return

    type = data["type"]
    if type == "host":
        a=0
        #TODO: Find new port, create session and send port back to host
    elif type == "guest":
        a=0
        #TODO: Get room code, find matching port and send back
    else:
        returnMessage.clear()
        returnMessage["status"] = "error"
        returnMessage["error"] = str(errorCodes.invalidType)
        conn.send(json.dumps(returnMessage))


    # #infinite loop so that function do not terminate and thread do not end.
    # while True:
    #
    #     #Receiving from client
    #     data = conn.recv(1024)
    #     reply = 'OK...' + data
    #     if not data:
    #         break
    #
    #     conn.sendall(reply)
    #
    # #came out of loop
    # conn.close()

def gameRoom(conn, roomPort,roomName, hostName):
    #initial room setup
    roomSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((masterConfig.host, roomPort))
    except socket.error as e:
        print("Failed to bind socket. Error: " + str(e[0]) + " , " + e[1])
        #TODO: send message back to host and close connection here
        return errorCodes.roomSocketError
    print("Room created on port " + str(roomPort) + " for " + hostName)

    #let host know that room is ready
    returnMessage = dict()
    returnMessage["status"] = "success"
    returnMessage["port"] = roomPort
    returnMessage["name"] = roomName
    conn.send(json.dumps(returnMessage))

    conn.close()

    #TODO: The rest of this...



sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")

try:
    sock.bind((masterConfig.host, masterConfig.hostPort))
except socket.error as e:
    print("Failed to bind socket. Error: " + str(e[0]) + " , " + e[1])
    print("Terminating program")
    sys.exit(-1)

print("Socket bound")

sock.listen(10)
print("Socket listening on port " + str(masterConfig.hostPort))

nextPort = masterConfig.hostPort + 1

print("Close server with ^C")
while 1:
    conn, addr = sock.accept()

    start_new_thread(handleInbound, (conn,))

sock.close()