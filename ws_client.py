import json
from queue import Queue
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import threading
from tkinter import Tk
import tkinter

from minesweeper import Minesweeper


# NOTE Old example:

# top = tkinter.Tk()
# top.title("Chatter")

# messages_frame = tkinter.Frame(top)
# MY_MSG = tkinter.StringVar()  # For the messages to be sent.
# MY_MSG.set("Type your messages here.")
# scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.
# # Following will contain the messages.
# MSG_LIST = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
# scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
# MSG_LIST.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
# MSG_LIST.pack()
# messages_frame.pack()

# entry_field = tkinter.Entry(top, textvariable=MY_MSG)
# entry_field.bind("<Return>", send)
# entry_field.pack()
# send_button = tkinter.Button(top, text="Send", command=send)
# send_button.pack()


MY_MSG = ""
MINESWEEPER = None
MSG_LIST = []
WINDOW = None
MY_TURN = None
WS_MSG_QUEUE = Queue(maxsize=1)
_WINDOW_UPDATE_DELAY = 1000


class WsMessage:
    msg: str 
    my_turn: bool
    board: str # serailized json of Board class 


LBL_MSG = None 
LBL_MY_TURN = None
LBL_BOARD = None


def update_gui():
    if not WS_MSG_QUEUE.empty():
        ws_msg:  = WS_MSG_QUEUE.get_nowait()

    if not isinstance(ws_msg, WsMessage):
        raise ValueError(f"Incorrect data type given to WS_MSG_QUEUE: {type(ws_msg)}")
    
    if ws_msg.msg:
        LBL_MSG.config(text=ws_msg.msg)
    if ws_msg.my_turn:
        LBL_MY_TURN.config(text=int(ws_msg.msg))
    if ws_msg.board:
        LBL_BOARD.config(text=ws_msg.board)

    WINDOW.after(_WINDOW_UPDATE_DELAY, update_gui)


def run_client():
    global MINESWEEPER, WINDOW, MY_TURN
    
    # create Tk instance
    WINDOW = Tk()
    WINDOW.protocol("WM_DELETE_WINDOW", on_closing)
    # set program title
    WINDOW.title("MINESWEEPER")
    # create game instance
    MINESWEEPER = Minesweeper(WINDOW)
    # run event loop

    update_thread = threading.Thread(target = update_gui)
    update_thread.daemon = True
    update_thread.start()
    
    update_gui()

    WINDOW.mainloop()


def unserialize_json_string(s: str) -> str | None:
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        print(f"Error decoding json: {e}")
        return None 
    

def receive():
    """Handles receiving of messages."""
    while True:
        try:
            ws_msg = client_socket.recv(BUFSIZ).decode("utf8")
            if isinstance(ws_msg, str):
                msg_dict = unserialize_json_string(ws_msg)
                print(f"Received msg_dict: {msg_dict}")

                if not msg_dict:
                    raise ValueError("Excepted json string")
                
                print(f"[ws] Msg: {msg_dict}")
                msg = msg_dict.get("msg")
                my_turn = msg_dict.get("my_turn", False)

                
                ws_msg = WsMessage(msg=msg, my_turn=my_turn)
                WS_MSG_QUEUE.put(ws_msg)

            # TODO move to ws_msg
            elif isinstance(msg, "Board"):
                print(f"[ws] Board: {msg}")
            
            else:
                raise Exception(f"Unexpected type received from websockets: {type(msg)}\nThe object itself: {msg}")

        except OSError:  # Possibly client has left the chat.
            break


def send_board(event=None, board: "Board" = None):  # event is passed by binders.
    if board is None:
        raise RuntimeError("Null board provided")
    
    """Handles sending of messages."""
    msg = MY_MSG.get()
    MY_MSG.set("")  # Clears input field.
    client_socket.send(bytes(board, "utf8"))
    if msg == "{quit}":
        client_socket.close()
        WINDOW.quit()


def on_closing(event=None):
    """This function is to be called when the WINDOW is closed."""
    MY_MSG.set("{quit}")


#----Now comes the sockets part----
HOST = input('Enter host: ')
PORT = input('Enter port: ')
if not PORT:
    PORT = 33000
else:
    PORT = int(PORT)

BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)

receive_thread = Thread(target=receive)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.