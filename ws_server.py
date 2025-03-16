from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time

from websockets import broadcast


clients = {}
addresses = {}
whos_turn = None
WAIT_FOR_OPPONENT_TIME = 2 # in secs
CUR_CLIENT = None 

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)
SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)


def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Greetings from the cave!"+
                          "Now type your name and press enter!", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


def handle_messages(client): 
    name = clients[client]
    count_connected_clients = len(clients)

    assert count_connected_clients == 2

    while True:
        msg = client.recv(BUFSIZ)
        if msg == bytes("{quit}", "utf8"):
            client.send(bytes("{quit}", "utf8"))
            client.close()
            del clients[client]
            broadcast(bytes("%s has left the chat." % name, "utf8"))
            break            


def handle_client(client):  
    """Handles a single client connection."""

    name = client.recv(BUFSIZ).decode("utf8")
    
    count_connected_clients = len(clients)
    if count_connected_clients >= 2:
        error_msg = "Guys are already playing, %s. You're quit. Goodbye" % name
        client.send({"error": error_msg})
        return    
    
    welcome = 'Welcome %s! If you ever want to quit, type {quit} to exit.' % name
    client.send(bytes(welcome, "utf8"))
    msg = "%s has joined the chat!" % name
    broadcast(bytes(msg, "utf8"))
    clients[client] = name

    while count_connected_clients < 2:
        msg = "Wait for your opponent"
        client.send(bytes(msg))
        time.sleep(WAIT_FOR_OPPONENT_TIME)

    assert count_connected_clients == 2, "No 2 clients"

    try:
        handle_messages(client=client)    
    except Exception as e:
        print(f"Exception during handle_message: {e}")
    finally:
        clients.pop(client)

        


if __name__ == "__main__":
    SERVER.listen(5)  # Listens for 5 connections at max.
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()  # Starts the infinite loop.
    ACCEPT_THREAD.join()
    SERVER.close()