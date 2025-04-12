# gui.py

# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import threading
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tkinter import messagebox, ttk
from client import client



# ++++++++++++  Variables: Client Data  ++++++++++++ #
# Initialize gRPC Client
# client = chat_client.ChatClient()
data_coordinates = [(30, 60), (45, 120), (60, 150)]
data_shelter = [(1, "pending"), (2, "accepted"), (3, "none")]
data_shelter_rec = [("A", 2), ("B", 5)]
data_numdogs = 0
data_capacity = 30


# +++++++++++++++  Variables: GUI  +++++++++++++++ #
# frame dimensions
FRAME_WIDTH = 1400
FRAME_HEIGHT = 620
# gui
gui = tk.Tk()
gui.title("Login")
gui.geometry(f"{FRAME_WIDTH}x{FRAME_HEIGHT}")
# frames
login_frame = tk.Frame(gui)
main_frame = tk.Frame(gui)
main_frame_stats_toggled = False


# +++++++++++++ Helper Functions: Login/Logout +++++++++++++ #

def check_username(username):
    """
    Check if username exists.
    """
    # TODO: change
    login_frame.pack_forget()
    load_main_frame()


# ++++++++++++ Helper Functions: Button Presses ++++++++++++ #

def button_stats_numdogs(delta, gui_label):
    """
    User decided to increment/decrement # of dogs they have.
    Reflect change on GUI.
    """
    global data_numdogs
    data_numdogs = data_numdogs + delta
    gui_label.config(text=f"Capacity: {data_capacity}\nCurrent No. Dogs: {data_numdogs}")
    pass


# ++++++++++++++ Helper Functions: Load Pages ++++++++++++++ #

def load_login_frame():
    """
    Load login frame.
    """
    global login_username, login_pwd, login_frame
    # Part 0: destroy login frame if we're logging out/going back after changes
    if login_frame:
        login_frame.destroy()
        login_frame = tk.Frame(gui)
    login_frame.pack(fill='both', expand=True)
    # Part 1: define column/row weights
    weights = [10,1,1,1,1,1,1,10]
    for i in range(len(weights)):
        login_frame.rowconfigure(i, weight=weights[i]) 
    login_frame.columnconfigure(0, weight=1) 
    # Part 2: create username label and entry
    tk.Label(login_frame, text="Enter New or Existing Username:").grid(row=1, column=0, padx=5)
    login_username = tk.Entry(login_frame)
    login_username.grid(row=2, column=0, padx=5)
    # Part 3: determine if new/existing user
    login_username.bind('<Return>', lambda event,username=login_username: check_username(username))

def load_map_with_dots(map_frame, coordinates):
    """
    Load the actual map.
    Separate from load_main_frame to allow for dynamic updates.
    """
    # Part 1: configure map size (-20 to allow for padding)
    map_width = FRAME_HEIGHT - 20
    map_height = FRAME_HEIGHT - 20 
    # Part 2: create a canvas for map
    canvas = tk.Canvas(map_frame, width=map_width, height=map_height, bg="black")
    canvas.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
    # Part 3: define map boundaries
    lat_min = 0     # min latitude
    lat_max = 90    # max latitude
    lon_min = 0     # min longitude
    lon_max = 180   # max longitude
    # Part 4: function to normalize lat/lon to canvas x, y coordinates
    def lat_lon_to_canvas(lat, lon):
        x = (lon - lon_min) / (lon_max - lon_min) * map_width
        y = map_height - (lat - lat_min) / (lat_max - lat_min) * map_height
        return x, y
    # Part 5: plot dots on the map
    for lat, lon in coordinates:
        x, y = lat_lon_to_canvas(lat, lon)
        canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="black")

def load_main_frame():
    """
    Loads the main frame.
    """
    # ++++++++++ Start Clean ++++++++++ #
    global data_numdogs
    for widget in main_frame.winfo_children():
        widget.destroy()

    # ++++++++++ Main Frame ++++++++++ #
    # Part 1: Column weights
    main_frame.columnconfigure(0, weight=1)   # menu
    main_frame.columnconfigure(1, weight=4)   # map
    main_frame.columnconfigure(2, weight=3)   # broadcast section
    # Part 2: Row weights
    for r in range(6):
        main_frame.rowconfigure(r, weight=1)

    # ++++++++ Menu Sub-Frame ++++++++ #
    # Part 0: menu sub-frame
    menu_subframe = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1)
    menu_subframe.grid(row=0, column=0, rowspan=6, sticky='nsew', padx=5, pady=5)
    
    # Part 1: account login/logout labels and buttons
    tk.Label(menu_subframe, text="Shelter: [username]", font=('Arial', 12)).pack(pady=10)
    tk.Button(menu_subframe, text="Logout", command=load_login_frame).pack(pady=5)
    tk.Button(menu_subframe, text="Delete Account").pack(pady=5)
    
    # Part 2: account statistics button and sub-frame
    def toggle_stats():
        if stats_subframe.winfo_ismapped():
            stats_subframe.pack_forget()
        else:
            stats_subframe.pack(pady=5)
    tk.Button(menu_subframe, text="Statistics", command=toggle_stats).pack(pady=5)
    stats_subframe = tk.Frame(menu_subframe)
    stats_label = tk.Label(stats_subframe, text="Capacity: 30\nCurrent No. Dogs: 0")
    stats_label.pack()
    tk.Button(stats_subframe, text="+", command=lambda: button_stats_numdogs(1, stats_label)).pack()
    tk.Button(stats_subframe, text="-", command=lambda: button_stats_numdogs(-1, stats_label)).pack()

    # +++++++++++ Map Sub-Frame +++++++++++ #
    map_subframe = tk.Frame(main_frame, highlightbackground="red", highlightthickness=1, bg='black')
    map_subframe.grid(row=0, column=1, rowspan=6, sticky='nsew', padx=5, pady=5)
    load_map_with_dots(map_subframe, data_coordinates)

    # ++++++++ Broadcast Sub-Frame ++++++++ #
    # Row 0: broadcast request
    broadcast_subframe = tk.Frame(main_frame, highlightbackground="black", highlightcolor="black", highlightthickness=1)
    broadcast_subframe.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
    tk.Label(broadcast_subframe, text="Broadcast Request", font=("Helvetica", 14, "bold")).pack(pady=5)
    entry = tk.Entry(broadcast_subframe)
    entry.pack(side='left', padx=5, pady=5)
    tk.Button(broadcast_subframe, text="Send").pack(side='left', padx=5, pady=5)
    
    # Row 1: sent-out broadcasts
    sent_out_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, relief='solid')
    sent_out_broadcasts_frame.grid(row=1, column=2, rowspan=2, sticky='nsew', padx=5, pady=5)
    tk.Label(sent_out_broadcasts_frame, text="Sent Broadcasts", font=("Helvetica", 14)).pack()
    sent_outs_table = ttk.Treeview(sent_out_broadcasts_frame, columns=("ID", "Status", ""), show="headings")
    sent_outs_table.heading("ID", text="Dogs")
    sent_outs_table.heading("Status", text="Status")
    sent_outs_table.heading("", text="Delete")
    sent_outs_table.pack(fill='both', expand=True)
    for shelter_id, status in data_shelter:
        sent_outs_table.insert("", "end", values=(shelter_id, status, "X"))
    
    # Row 2: received Broadcasts
    received_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, relief='solid')
    received_broadcasts_frame.grid(row=3, column=2, rowspan=3, sticky='nsew', padx=5, pady=5)
    tk.Label(received_broadcasts_frame, text="Received Broadcasts", font=("Helvetica", 14)).pack()
    receives_table = ttk.Treeview(received_broadcasts_frame, columns=("From", "Dogs", "Action"), show="headings")
    receives_table.heading("From", text="From Shelter")
    receives_table.heading("Dogs", text="# Dogs")
    receives_table.heading("Action", text="Accept/Reject")
    receives_table.pack(fill='both', expand=True)
    for sid, dogs in data_shelter_rec:
        receives_table.insert("", "end", values=(sid, dogs, "Yes/No"))

    # ++++++++++ Add Frames to GUI ++++++++++ #
    gui.update()
    main_frame.grid(row=0, column=0, sticky="nsew")


# ++++++++++++++  Main Function  ++++++++++++++ #

if __name__ == "__main__":
    load_main_frame()
    gui.mainloop()