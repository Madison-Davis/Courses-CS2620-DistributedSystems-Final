# gui.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import os
import sys
import threading
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tkinter import ttk, messagebox
from client import client_app
from config import config



# ++++++++++++  Variables: Client Data  ++++++++++++ #
# Initialize client gRPC comms and data
# Both of these will be filled once one presses login button (so no need to edit)
app_client = None
data = {}
statuses = {
    0: "Denied",
    1: "Approved",
    2: "Pending",
    3: "Deleted"
}


# +++++++++++++++  Variables: GUI  +++++++++++++++ #
# gui dimensions
FRAME_WIDTH = 1400
FRAME_HEIGHT = 620
# gui
gui = tk.Tk()
gui.title("Login")
gui.geometry(f"{FRAME_WIDTH}x{FRAME_HEIGHT}")
# frames
login_frame = tk.Frame(gui)
main_frame = tk.Frame(gui, bg="gray9")
main_frame_stats_toggled = False


# +++++++++++++ Helper Functions: Login/Logout +++++++++++++ #
# NOTE: for the shelter location dots we can just make like a random number generator for a new user


# +++++++++++++ Helper Functions: Dynamic GUI +++++++++++++ #
def update_broadcast_callback(incoming_request):
    """ Updates the GUI inbox dynamically when a new message arrives. """
    global data
    # sender_shelter = incoming_request.sender_username
    # dogs_requested = incoming_request.amount_requested
    # data["broadcasts_recv"].append([sender_shelter, dogs_requested])
    data["broadcasts_recv"].append(incoming_request)
    gui.after(100, load_main_frame, data)


# ++++++++++++ Helper Functions: Button Presses ++++++++++++ #
def button_clicked_send(quantity):
    """
    When the broadcast 'send' button is clicked.
    """
    global data
    sender_id = data["uuid"]
    region = int(data["region"])
    quantity = int(quantity)
    status = app_client.broadcast(sender_id, region, quantity)
    load_main_frame(data)

def button_stats_numdogs(delta, gui_label):
    """
    User decided to increment/decrement # of dogs they have.
    Reflect change on GUI.
    """
    global data
    data['num_dogs'] = data['num_dogs'] + delta
    gui_label.config(text=f"Capacity: {data['capacity']}\nCurrent No. Dogs: {data['num_dogs']}")
    pass

def button_enter_login(user, pwd, region, is_new):
    """
    Fired when a user presses the login button
    Connect to its region's server
    Grab data to populate main frame
    """
    # populate data {} based on if they are new user or returning
    global data, app_client
    region = int(region)
    if region not in config.SERVER_REGIONS and region != -1:
        messagebox.showerror("Error", f"Valid regions: {config.SERVER_REGIONS}")
        return
    if is_new:
        app_client = client_app.AppClient(region)
        status, uuid = app_client.create_account(username=user, region=region, pwd_hash=pwd)
        if not status:
            messagebox.showerror("Error", "Username already exists.")
            return
        assert(status)
        # NOTE: all are correct except the last 3, i'll just make those empty those later
        data = {
            "username" : user,
            "uuid"     : uuid,
            "pwd"      : pwd,
            "capacity" : 30, # this is just how we start it off at
            "num_dogs" : 0,
            "region"   : region,
            "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
            "broadcasts_sent" : [],
            "broadcasts_recv" : []
        }
    else:
        app_client = client_app.AppClient(region, user)
        status = app_client.verify_password(username=user, pwd_hash=pwd)
        if not status:
            messagebox.showerror("Error", "Invalid username or password.")
            return
        assert(status)
        response = app_client.login(username=user, pwd_hash=pwd)
        data = {
            "username" : user,
            "pwd"      : pwd,
            "uuid"     : response.account_info.uuid,
            "capacity" : response.account_info.capacity,
            "num_dogs" : response.account_info.dogs,
            "region"   : response.account_info.region,
            "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
            "broadcasts_sent" : [] if response.broadcasts_sent is None else response.broadcasts_sent,
            "broadcasts_recv" : [] if response.broadcasts_recv is None else response.broadcasts_recv
        }

    # set up a real-time broadcast thread
    listener_thread = threading.Thread(target=app_client.receive_broadcast, 
                                       args=(data["uuid"], update_broadcast_callback,),
                                       daemon=True)
    listener_thread.start()

    # load main frame
    login_frame.pack_forget()
    load_main_frame(data)

def button_logout():
    """
    User desires to logout
    """
    global data
    data = {}
    main_frame.grid_forget()
    load_login_frame()

def button_delete_account():
    """
    User desires to delete account
    """
    global data
    status = app_client.delete_account(uuid=data["uuid"], username=data["username"], pwd_hash=data["pwd"])
    assert(status)
    data = {}
    main_frame.grid_forget()
    load_login_frame()
    

# ++++++++++++++ Helper Functions: Load Pages ++++++++++++++ #
import tkinter as tk

def load_login_frame():
    """
    Load login frame with toggle for New User / Returning User.
    """
    global login_frame
    if 'login_frame' in globals() and login_frame:
        login_frame.destroy()

    login_frame = tk.Frame(gui)
    login_frame.pack(fill='both', expand=True)

    # Layout weights
    weights = [10, 1, 1, 1, 1, 1, 10]
    for i in range(len(weights)):
        login_frame.rowconfigure(i, weight=weights[i])
    login_frame.columnconfigure(0, weight=1)

    # Label for login type
    # Dropdown for new/returning
    tk.Label(login_frame, text="Login Type:").grid(row=1, column=0)
    login_mode = tk.StringVar(value="new")
    mode_menu = tk.OptionMenu(login_frame, login_mode, "new", "returning", command=lambda _: update_fields())
    mode_menu.grid(row=2, column=0)

    # Container for dynamic input fields
    field_container = tk.Frame(login_frame)
    field_container.grid(row=3, column=0)
    entries = {}  # Store references to input fields

    def update_fields():
        # Clear current widgets
        for widget in field_container.winfo_children():
            widget.destroy()
        entries.clear()
        # Username
        row = 0
        tk.Label(field_container, text="Username:").grid(row=row, column=0, sticky='w', padx=5)
        entries['username'] = tk.Entry(field_container)
        entries['username'].grid(row=row+1, column=0, padx=5)
        row += 2
        # Region (only for new users)
        if login_mode.get() == "new":
            tk.Label(field_container, text="Region:").grid(row=row, column=0, sticky='w', padx=5)
            entries['region'] = tk.Entry(field_container)
            entries['region'].grid(row=row+1, column=0, padx=5)
            row += 2
        # Password
        tk.Label(field_container, text="Password:").grid(row=row, column=0, sticky='w', padx=5)
        entries['pwd'] = tk.Entry(field_container, show='*')
        entries['pwd'].grid(row=row+1, column=0, padx=5)
        row += 2
        # Submit button
        def submit():
            user = entries['username'].get()
            pwd = entries['pwd'].get()
            region = entries['region'].get() if 'region' in entries else -1 # -1 means we're logging in as returning, and we'll find its region via LB + server data
            is_new = login_mode.get() == "new"
            button_enter_login(user, pwd, region, is_new)

        tk.Button(field_container, text="Enter", command=submit).grid(row=row, column=0, pady=10)
    update_fields()

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

def load_main_frame(data):
    """
    Loads the main frame.
    """
    # ++++++++++ Start Clean ++++++++++ #
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
    menu_subframe = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, bg="gray20")
    menu_subframe.grid(row=0, column=0, rowspan=6, sticky='nsew', padx=5, pady=5)
    
    # Part 1: account login/logout labels and buttons
    tk.Label(menu_subframe, text=f"Shelter: {data['username']}", fg="white", bg="gray20", font=('Arial', 12)).pack(pady=10)
    tk.Label(menu_subframe, text=f"Region: {data['region']}", fg="white", bg="gray20", font=('Arial', 12)).pack(pady=10)
    tk.Button(menu_subframe, text="Logout", command=button_logout).pack(pady=5)
    tk.Button(menu_subframe, text="Delete Account", command=button_delete_account).pack(pady=5)
    
    # Part 2: account statistics button and sub-frame
    def toggle_stats():
        if stats_subframe.winfo_ismapped():
            stats_subframe.pack_forget()
        else:
            stats_subframe.pack(pady=5)
    tk.Button(menu_subframe, text="Statistics", command=toggle_stats).pack(pady=5)
    stats_subframe = tk.Frame(menu_subframe)
    stats_label = tk.Label(stats_subframe, text=f"Capacity: {data['capacity']}\nCurrent No. Dogs: {data['num_dogs']}")
    stats_label.pack()
    tk.Button(stats_subframe, text="+", command=lambda: button_stats_numdogs(1, stats_label)).pack()
    tk.Button(stats_subframe, text="-", command=lambda: button_stats_numdogs(-1, stats_label)).pack()

    # +++++++++++ Map Sub-Frame +++++++++++ #
    map_subframe = tk.Frame(main_frame, highlightbackground="red", highlightthickness=1, bg='black')
    map_subframe.grid(row=0, column=1, rowspan=6, sticky='nsew', padx=5, pady=5)
    load_map_with_dots(map_subframe, data["shelter_locations"])

    # ++++++++ Broadcast Sub-Frame ++++++++ #
    # Row 0: broadcast request
    broadcast_subframe = tk.Frame(main_frame, highlightbackground="black", highlightcolor="black", highlightthickness=1, bg="gray20")
    broadcast_subframe.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
    tk.Label(broadcast_subframe, text="Broadcast Request", bg="gray20", fg="white", font=("Helvetica", 14, "bold")).pack(pady=5)
    entry = tk.Entry(broadcast_subframe)
    tk.Label(broadcast_subframe, text="Quantity to send: ", fg="white", bg="gray20").pack(side='left', padx=5, pady=5)
    entry.pack(side='left', padx=5, pady=5)
    tk.Button(broadcast_subframe, text="Send", command=lambda:button_clicked_send(entry.get())).pack(side='left', padx=5, pady=5)
    
    # Row 1: sent-out broadcasts
    sent_out_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black",
                                        highlightthickness=1, relief='solid', bg="gray20")
    sent_out_broadcasts_frame.grid(row=1, column=2, rowspan=2, sticky='nsew', padx=5, pady=5)
    tk.Label(sent_out_broadcasts_frame, text="Sent Broadcasts",
            bg="gray20", fg="white", font=("Helvetica", 14)).pack(pady=5)
    sent_broadcasts_container = tk.Frame(sent_out_broadcasts_frame, bg="gray20")
    sent_broadcasts_container.pack(fill='both', expand=True)
    load_sent_broadcasts(sent_broadcasts_container, data["broadcasts_sent"])
    
    # Row 2: received Broadcasts
    received_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black",
                                         highlightthickness=1, relief='solid', bg="gray20")
    received_broadcasts_frame.grid(row=3, column=2, rowspan=2, sticky='nsew', padx=2, pady=5)
    tk.Label(received_broadcasts_frame, text="Received Broadcasts",
             bg="gray20", fg="white", font=("Helvetica", 14)).pack(pady=5)
    broadcasts_container = tk.Frame(received_broadcasts_frame, bg="gray20")
    broadcasts_container.pack(fill='both', expand=True)
    load_received_broadcasts(broadcasts_container, data["broadcasts_recv"])

    # ++++++++++ Add Frames to GUI ++++++++++ #
    gui.update()
    main_frame.grid(row=0, column=0, sticky="nsew")

def delete_sent_broadcast(broadcast, delete_btn):
    """
    Callback for when the Delete button is pressed in a sent broadcast row.
    Insert your deletion logic here, for example calling a method on app_client,
    then refresh the GUI.
    """
    global data
    print(f"Deleted broadcast")
    success = app_client.delete_broadcast(data["uuid"], broadcast.broadcast_id)
    if success:
        broadcast.status = 3
    else:
        messagebox.showerror("Error", f"Could not delete broadcast")
    delete_btn.config(state="disabled")
    response = app_client.login(username=data["username"], pwd_hash=data["pwd"])
    data = {
        "username" : data["username"],
        "pwd"      : data["pwd"],
        "uuid"     : response.account_info.uuid,
        "capacity" : response.account_info.capacity,
        "num_dogs" : response.account_info.dogs,
        "region"   : response.account_info.region,
        "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
        "broadcasts_sent" : [] if response.broadcasts_sent is None else response.broadcasts_sent,
        "broadcasts_recv" : [] if response.broadcasts_recv is None else response.broadcasts_recv
    }
    load_main_frame(data)


def load_sent_broadcasts(container, broadcasts):
    """
    Clears the container and creates a header row plus rows for each sent broadcast.
    The grid is used to align three columns:
      Column 0: Dogs
      Column 1: Status
      Column 2: Delete button
    All cell contents are centered.
    """
    # Clear any existing widgets in the container.
    for widget in container.winfo_children():
        widget.destroy()
    container.grid_columnconfigure(0, weight=1)

    # Headers frame
    header_frame = tk.Frame(container, bg="gray30")
    header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 2))
    for col in range(3):
        header_frame.columnconfigure(col, weight=1, uniform="sent_cols")
    tk.Label(header_frame, text="Dogs", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=0, sticky="nsew", padx=15, pady=2)
    tk.Label(header_frame, text="Status", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=1, sticky="nsew", padx=15, pady=2)
    tk.Label(header_frame, text="Delete", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=2, sticky="nsew", padx=15, pady=2)

    # Row for each sent broadcast
    for row_idx, broadcast in enumerate(broadcasts, start=1):
        row_frame = tk.Frame(container, bg="gray20")
        row_frame.grid(row=row_idx, column=0, sticky="ew", padx=10, pady=2)
        for col in range(3):
            row_frame.columnconfigure(col, weight=1, uniform="sent_cols")
        tk.Label(row_frame, text=str(broadcast.amount_requested), bg="gray20", fg="white",
                 anchor="center")\
            .grid(row=0, column=0, sticky="nsew", padx=15, pady=2)
        status_text = statuses.get(broadcast.status, "Unknown")
        tk.Label(row_frame, text=status_text, bg="gray20", fg="white",
                 anchor="center")\
            .grid(row=0, column=1, sticky="nsew", padx=15, pady=2)
        is_pending = (broadcast.status == 2)
        delete_btn = tk.Button(row_frame, text="Delete", width=8, state="normal" if is_pending else "disabled")
        if is_pending:
            delete_btn.config(command=lambda b=broadcast, db=delete_btn: delete_sent_broadcast(b, db))
        delete_btn.grid(row=0, column=2, sticky="nsew", padx=15, pady=2)
        # tk.Button(row_frame, text="Delete", width=8,
        #           command=lambda b=broadcast: delete_sent_broadcast(b))\
        #     .grid(row=0, column=2, sticky="nsew", padx=15, pady=2)

def approve_broadcast(broadcast, approve_btn, deny_btn):
    """
    Callback for when the Accept button is pressed.
    You may want to update the broadcast's status or perform an action with app_client.
    """
    global data
    print(f"Accepted broadcast from {broadcast.sender_username}")
    success = app_client.approve_or_deny(data["uuid"], broadcast.broadcast_id, 1)
    if success:
        broadcast.status = 1
    else:
        messagebox.showerror("Error", f"Could not approve broadcast")
    approve_btn.config(state="disabled")
    deny_btn.config(state="disabled")
    response = app_client.login(username=data["username"], pwd_hash=data["pwd"])
    data = {
        "username" : data["username"],
        "pwd"      : data["pwd"],
        "uuid"     : response.account_info.uuid,
        "capacity" : response.account_info.capacity,
        "num_dogs" : response.account_info.dogs,
        "region"   : response.account_info.region,
        "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
        "broadcasts_sent" : [] if response.broadcasts_sent is None else response.broadcasts_sent,
        "broadcasts_recv" : [] if response.broadcasts_recv is None else response.broadcasts_recv
    }
    load_main_frame(data)

def deny_broadcast(broadcast, approve_btn, deny_btn):
    """
    Callback for when the Reject button is pressed.
    You may want to update the broadcast's status or perform an action with app_client.
    """
    global data
    print(f"Rejected broadcast from {broadcast.sender_username}")
    success = app_client.approve_or_deny(data["uuid"], broadcast.broadcast_id, 0)
    if success:
        broadcast.status = 0
    else:
        messagebox.showerror("Error", f"Could not deny broadcast")
    approve_btn.config(state="disabled")
    deny_btn.config(state="disabled")
    response = app_client.login(username=data["username"], pwd_hash=data["pwd"])
    data = {
        "username" : data["username"],
        "pwd"      : data["pwd"],
        "uuid"     : response.account_info.uuid,
        "capacity" : response.account_info.capacity,
        "num_dogs" : response.account_info.dogs,
        "region"   : response.account_info.region,
        "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
        "broadcasts_sent" : [] if response.broadcasts_sent is None else response.broadcasts_sent,
        "broadcasts_recv" : [] if response.broadcasts_recv is None else response.broadcasts_recv
    }
    load_main_frame(data)


def load_received_broadcasts(container, broadcasts):
    """
    Clear the container and dynamically create a row (as a Frame) for each broadcast.
    Each row will include the sender's name, number of dogs, and Approve/Deny buttons.
    """
    # Clear any existing widgets in the container
    for widget in container.winfo_children():
        widget.destroy()
    container.grid_columnconfigure(0, weight=1)

    # Header frame
    header_frame = tk.Frame(container, bg="gray30")
    header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
    for col in range(5):
        header_frame.columnconfigure(col, weight=1, uniform="col_width")
    tk.Label(header_frame, text="Sender", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
    tk.Label(header_frame, text="Quantity", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=1, sticky="nsew", padx=5, pady=2)
    tk.Label(header_frame, text="Approve", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=2, sticky="nsew", padx=5, pady=2)
    tk.Label(header_frame, text="Deny", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=3, sticky="nsew", padx=5, pady=2)
    tk.Label(header_frame, text="Status", bg="gray30", fg="white",
             font=('Arial', 10, 'bold'), anchor="center")\
        .grid(row=0, column=4, sticky="nsew", padx=5, pady=2)

    # Row for each broadcast
    for row_idx, broadcast in enumerate(broadcasts, start=1):
        row_frame = tk.Frame(container, bg="gray20")
        row_frame.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=2)
        for col in range(5):
            row_frame.columnconfigure(col, weight=1, uniform="col_width")
        tk.Label(row_frame, text=broadcast.sender_username, bg="gray20",
                 fg="white", anchor="center")\
            .grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
        tk.Label(row_frame, text=str(broadcast.amount_requested), bg="gray20",
                 fg="white", anchor="center")\
            .grid(row=0, column=1, sticky="nsew", padx=5, pady=2)
        is_pending = (broadcast.status == 2)
        approve_btn = tk.Button(row_frame, text="Approve", width=8, state="normal" if is_pending else "disabled")
        deny_btn = tk.Button(row_frame, text="Deny", width=8, state="normal" if is_pending else "disabled")
        if is_pending:
            approve_btn.config(command=lambda b=broadcast, ab=approve_btn, db=deny_btn: approve_broadcast(b, ab, db))
            deny_btn.config(command=lambda b=broadcast, ab=approve_btn, db=deny_btn: deny_broadcast(b, ab, db))
        approve_btn.grid(row=0, column=2, sticky="nsew", padx=5, pady=2)
        deny_btn.grid(row=0, column=3, sticky="nsew", padx=5, pady=2)
        status_text = statuses.get(broadcast.status, "Unknown")
        tk.Label(row_frame, text=status_text, bg="gray20", fg="white",
                 anchor="center")\
            .grid(row=0, column=4, sticky="nsew", padx=5, pady=2)

# ++++++++++++++  Main Function  ++++++++++++++ #
if __name__ == "__main__":
    load_login_frame()
    gui.mainloop()