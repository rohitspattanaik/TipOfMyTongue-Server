import sys, socket, signal, masterConfig
from thread import *

def signalHandler(signal, frame):
    print("Closing server")
    sock.close()
    print("Socket closed")
    sys.exit(0)
signal.signal(signal.SIGINT, signalHandler)

#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #Sending message to connected client
    conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string

    #infinite loop so that function do not terminate and thread do not end.
    while True:

        #Receiving from client
        data = conn.recv(1024)
        reply = 'OK...' + data
        if not data:
            break

        conn.sendall(reply)

    #came out of loop
    conn.close()

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

    start_new_thread(clientthread, (conn,))

sock.close()