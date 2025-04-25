# gui.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import os
import sys
import random
import threading
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tkinter import messagebox
from client import client_app
from config import config


# ++++++++++++  Variables: Client Data  ++++++++++++ #
# Initialize client gRPC comms and data
# Both of these will be filled once one presses login button (so no need to edit)
app_client = None
data = {}

# DO NOT edit ordering
statuses_to_word = {
    0: "Denied",
    1: "Pending",
    2: "Deleted",
    3: "Approved"
}
statuses = {
    "Denied": 0,
    "Pending": 1,
    "Deleted": 2,
    "Approved": 3
}


# +++++++++++++++  Variables: GUI  +++++++++++++++ #
# gui dimensions
FRAME_WIDTH = 1425
FRAME_HEIGHT = 725
# gui
gui = tk.Tk()
gui.title("Login")
gui.geometry(f"{FRAME_WIDTH}x{FRAME_HEIGHT}")
gui.rowconfigure(0, weight=1)
gui.columnconfigure(0, weight=1)
# gui.resizable(False, False)
# frames
login_frame = tk.Frame(gui)
main_frame = tk.Frame(gui, bg="gray20")
main_frame_stats_toggled = False

# shelter locations
# region #      where on map        boundaries
# region 0      bottom              lat: [60, ], lon: [60,]
# region 1      middle
# region 2      top


# +++++++++++++ Helper Functions: Login/Logout +++++++++++++ #
# NOTE: for the shelter location dots we can just make like a random number generator for a new user

def reload_update_data():
    global data
    response = app_client.login(username=data["username"], pwd_hash=data["pwd"])
    data = {
        "username" : data["username"],
        "pwd"      : data["pwd"],
        "uuid"     : response.account_info.uuid,
        "capacity" : response.account_info.capacity,
        "num_dogs" : response.account_info.dogs,
        "region"   : response.account_info.region,
        "shelter_locations" : data["shelter_locations"],
        "broadcasts_sent" : [] if response.broadcasts_sent is None else response.broadcasts_sent,
        "broadcasts_recv" : [] if response.broadcasts_recv is None else response.broadcasts_recv
    }
    load_main_frame(data)


# +++++++++++++ Helper Functions: Dynamic GUI +++++++++++++ #
def update_broadcast_callback(incoming_request):
    """ Updates the GUI inbox dynamically when a new message arrives. """
    global data
    gui.after(100, reload_update_data)


# ++++++++++++ Helper Functions: Button Presses ++++++++++++ #
def button_clicked_send(quantity):
    """
    When the broadcast 'send' button is clicked.
    """
    global data
    sender_id = data["uuid"]
    region = int(data["region"])
    current = int(data["num_dogs"])
    quantity = int(quantity)
    if quantity > current:
        messagebox.showerror("Error", "Quantity requested exceeds current inventory.")
        return
    status = app_client.broadcast(sender_id, region, quantity)
    reload_update_data()

def button_stats_numdogs(delta, gui_label):
    """
    User decided to increment/decrement # of dogs they have.
    Reflect change on GUI.
    """
    global data
    data['num_dogs'] = data['num_dogs'] + delta
    success = app_client.change_dogs(data["uuid"], delta)
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
        # TODO: all are correct except the last 3, i'll just make those empty those later
        shelter_locations = [1,0,0] if region == 0 else [0,1,0] if region == 1 else [0,0,1]
        data = {
            "username" : user,
            "uuid"     : uuid,
            "pwd"      : pwd,
            "capacity" : 30, # this is just how we start it off at
            "num_dogs" : 0,
            "region"   : region,
            "shelter_locations" : shelter_locations, # how many shelters per region
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
        # TODO: all are correct except the shelter location, i'll just make those empty those later
        region = response.account_info.region
        shelter_locations = [1,0,0] if region == 0 else [0,1,0] if region == 1 else [0,0,1]
        data = {
            "username" : user,
            "pwd"      : pwd,
            "uuid"     : response.account_info.uuid,
            "capacity" : response.account_info.capacity,
            "num_dogs" : response.account_info.dogs,
            "region"   : response.account_info.region,
            "shelter_locations" : shelter_locations, # how many shelters per region
            "broadcasts_sent" : [] if response.broadcasts_sent is None else response.broadcasts_sent,
            "broadcasts_recv" : [] if response.broadcasts_recv is None else response.broadcasts_recv
        }

    # set up a real-time broadcast thread
    listener_thread = threading.Thread(target=app_client.receive_broadcast, 
                                       args=(data["uuid"], update_broadcast_callback,),
                                       daemon=True)
    listener_thread.start()
    # set up a real-time approval thread
    approval_thread = threading.Thread(target=app_client.receive_approval, 
                                       args=(data["uuid"], update_broadcast_callback,),
                                       daemon=True)
    approval_thread.start()
    # set up a real-time deletion thread
    deletion_thread = threading.Thread(target=app_client.receive_deletion, 
                                       args=(data["uuid"], update_broadcast_callback,),
                                       daemon=True)
    deletion_thread.start()
    # set up a real-time denial thread
    denial_thread = threading.Thread(target=app_client.receive_denial, 
                                       args=(data["uuid"], update_broadcast_callback,),
                                       daemon=True)
    denial_thread.start()

    # load main frame
    login_frame.pack_forget()
    load_main_frame(data)

def button_logout():
    """
    User desires to logout
    """
    response = app_client.logout()
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
        # Password
        tk.Label(field_container, text="Password:").grid(row=row, column=0, sticky='w', padx=5)
        entries['pwd'] = tk.Entry(field_container, show='*')
        entries['pwd'].grid(row=row+1, column=0, padx=5)
        row += 2
        # Region (only for new users)
        if login_mode.get() == "new":
            tk.Label(field_container, text="Region:").grid(row=row, column=0, sticky='w', padx=5)
            # Define the options for the dropdown
            regions = ["East", "Midwest", "West"]  # Example regions
            # StringVar to hold the selected region's name
            selected_region_name = tk.StringVar(field_container)
            selected_region_name.set(regions[0])  # Default selection
            # Create the dropdown menu (OptionMenu)
            entries['region'] = tk.OptionMenu(field_container, selected_region_name, *regions)
            entries['region'].grid(row=row+1, column=0, padx=5)
            row += 2
        # Submit button
        def submit():
            user = entries['username'].get()
            pwd = entries['pwd'].get()
            region_name = entries['region'].cget('text') if 'region' in entries else None
            region_map = {"East": 0, "Midwest": 1, "West": 2}
            region = region_map.get(region_name, -1) if region_name else -1
            is_new = login_mode.get() == "new"
            button_enter_login(user, pwd, region, is_new)

        tk.Button(field_container, text="Enter", command=submit).grid(row=row, column=0, pady=10)
    update_fields()

def random_point_in_polygon(region):
    """
    Find the bounding box for region
    """
    # Add a buffer to ensure it lies within
    min_lat = min(lat for lat, _ in region)+7
    max_lat = max(lat for lat, _ in region)-7
    min_lon = min(lon for _, lon in region)+10
    max_lon = max(lon for _, lon in region)-10
    # Generate a random point within the bounding box
    random_lat = random.uniform(min_lat, max_lat)
    random_lon = random.uniform(min_lon, max_lon)
    return random_lat, random_lon
        
def load_map_with_dots(map_frame):
    """
    Load a stylized country map with three distinct regions and plot coordinates as red dots.
    """
    # Canvas setup
    canvas = tk.Canvas(map_frame, bg="black")
    canvas.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
    map_frame.grid_rowconfigure(0, weight=1)
    map_frame.grid_columnconfigure(0, weight=1)
    # Coordinate normalization
    lat_min, lat_max = 0, 90
    lon_min, lon_max = 0, 180
    map_width, map_height = 698, 711
    # Define a function to plot points
    def lat_lon_to_canvas(lat, lon):
        x = (lon - lon_min) / (lon_max - lon_min) * map_width
        y = map_height - (lat - lat_min) / (lat_max - lat_min) * map_height
        return x, y
    # Design fictional regions
    region_0 = [
        (20, 80), (25, 78), (28, 76), (30, 72),
        (32, 68), (34, 64), (36, 60), (38, 58),
        (40, 56), (42, 52), (44, 48), (46, 44),
        (44, 40), (42, 38), (40, 36), (38, 34),
        (36, 30), (34, 28), (30, 28), (28, 30),
        (26, 34), (24, 40), (22, 50), (20, 60)
    ]
    region_0 = [(lat, 1.2*lon+30) for lat, lon in region_0]
    region_1 = [
        (46, 44), (50, 46), (54, 48), (56, 52),
        (58, 56), (60, 60), (62, 64), (64, 66),
        (66, 68), (68, 66), (66, 60), (64, 56),
        (62, 52), (60, 48), (58, 44), (56, 42),
        (54, 40), (52, 38), (50, 36), (48, 36),
        (46, 38), (44, 40)
    ]
    region_1 = [(lat, 1.2*lon+30) for lat, lon in region_1]
    region_2 = [
        (68, 66), (70, 62), (72, 58), (74, 54),
        (76, 50), (78, 46), (80, 42), (82, 38),
        (84, 34), (86, 30), (84, 26), (82, 24),
        (80, 22), (78, 24), (76, 28), (74, 32),
        (72, 36), (70, 40), (68, 44), (66, 48),
        (66, 54)
    ]
    region_2 = [(lat, 1.2*lon+30) for lat, lon in region_2]
    # Draw region polygons
    def draw_region(region_coords):
        points = [lat_lon_to_canvas(lat, lon) for lat, lon in region_coords]
        canvas.create_polygon(points, fill="#333333", outline="darkgray", smooth=True, width=2)
    draw_region(region_0)
    draw_region(region_1)
    draw_region(region_2)
    # Plot red dots for each lat/lon in coordinates
    for region, num_shelters in enumerate(data["shelter_locations"]):
        for _ in range(num_shelters):
            region_polygon = region_0 if region == 0 else region_1 if region == 1 else region_2
            x, y = random_point_in_polygon(region_polygon)
            x, y = lat_lon_to_canvas(x, y)
            canvas.create_oval(x-4, y-4, x+4, y+4, fill="red", outline="black")

def load_main_frame(data):
    """
    Loads the main frame.
    """
    # ++++++++++ Start Clean ++++++++++ #
    for widget in main_frame.winfo_children():
        widget.destroy()

    # ++++++++++ Main Frame ++++++++++ #
    # Part 1: Column weights for dynamic resizing
    main_frame.columnconfigure(0, weight=1, uniform="main_frame_cols")   # menu
    main_frame.columnconfigure(1, weight=4, uniform="main_frame_cols")   # map
    main_frame.columnconfigure(2, weight=3, uniform="main_frame_cols")   # broadcast section

    # Part 2: Row weights for dynamic resizing
    main_frame.rowconfigure(0, weight=0)
    for r in range(1, 6):
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
    load_map_with_dots(map_subframe)

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
    # frame
    sent_out_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, relief='solid', bg="gray20")
    sent_out_broadcasts_frame.grid(row=1, column=2, sticky='nsew', padx=5, pady=5)
    # title label
    tk.Label(sent_out_broadcasts_frame, text="Sent Broadcasts", bg="gray20", fg="white", font=("Helvetica", 14)).pack(pady=5)
    # data table
    canvas_sent = tk.Canvas(sent_out_broadcasts_frame, bg="gray20")
    canvas_sent.pack(side="left", fill="both", expand=True)
    # data table scrollbar
    scrollbar_received = tk.Scrollbar(sent_out_broadcasts_frame, orient="vertical", command=canvas_sent.yview, width=5)
    scrollbar_received.pack(side="right", fill="y")
    canvas_sent.configure(yscrollcommand=scrollbar_received.set)
    # internal container for rows
    sent_broadcasts_container = tk.Frame(canvas_sent, bg="gray20")
    window_id = canvas_sent.create_window((0, 0), window=sent_broadcasts_container, anchor="nw")
    # func: auto-resize container to match canvas width
    def resize_container(event):
        canvas_sent.itemconfig(window_id, width=event.width)
    canvas_sent.bind("<Configure>", resize_container)
    # func: scrollregion updates as content changes
    sent_broadcasts_container.bind(
        "<Configure>",
        lambda event: canvas_sent.configure(scrollregion=canvas_sent.bbox("all"))
    )
    load_sent_broadcasts(sent_broadcasts_container, data["broadcasts_sent"])
    
    # Row 2: received Broadcasts
    # frame
    received_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, relief='solid', bg="gray20")
    received_broadcasts_frame.grid(row=2, column=2, sticky='nsew', padx=5, pady=5)
    # title label
    tk.Label(received_broadcasts_frame, text="Received Broadcasts", bg="gray20", fg="white", font=("Helvetica", 14)).pack(pady=5)
    # data table
    canvas_received = tk.Canvas(received_broadcasts_frame, bg="gray20")
    canvas_received.pack(side="left", fill="both", expand=True)
    # data table scrollbar
    scrollbar_received = tk.Scrollbar(received_broadcasts_frame, orient="vertical", command=canvas_received.yview, width=5)
    scrollbar_received.pack(side="right", fill="y")
    canvas_received.configure(yscrollcommand=scrollbar_received.set)
    # internal container for rows
    broadcasts_container = tk.Frame(canvas_received, bg="gray20")
    window_id = canvas_received.create_window((0, 0), window=broadcasts_container, anchor="nw")
    # func: auto-resize container to match canvas width
    def resize_container(event):
        canvas_received.itemconfig(window_id, width=event.width)
    canvas_received.bind("<Configure>", resize_container)
    # func: scrollregion updates as content changes
    broadcasts_container.bind(
        "<Configure>",
        lambda event: canvas_received.configure(scrollregion=canvas_received.bbox("all"))
    )
    load_received_broadcasts(broadcasts_container, data["broadcasts_recv"])

    # ++++++++++ Add Frames to GUI ++++++++++ #
    main_frame.grid(row=0, column=0, sticky="nsew")
    gui.update()

    
# ++++++++++++++ Helper Functions: Broadcasts ++++++++++++++ #

def approve_broadcast(broadcast, approve_btn, deny_btn):
    """
    Callback for when the Accept button is pressed.
    You may want to update the broadcast's status or perform an action with app_client.
    """
    global data
    success = app_client.approve_or_deny(data["uuid"], broadcast.broadcast_id, 1)
    if success:
        broadcast.status = statuses["Approved"]
    else:
        messagebox.showerror("Error", f"Could not approve broadcast")
    approve_btn.config(state="disabled")
    deny_btn.config(state="disabled")
    reload_update_data()

def deny_broadcast(broadcast, approve_btn, deny_btn):
    """
    Callback for when the Reject button is pressed.
    You may want to update the broadcast's status or perform an action with app_client.
    """
    global data
    success = app_client.approve_or_deny(data["uuid"], broadcast.broadcast_id, 0)
    if success:
        broadcast.status = statuses["Denied"]
    else:
        messagebox.showerror("Error", f"Could not deny broadcast")
    approve_btn.config(state="disabled")
    deny_btn.config(state="disabled")
    reload_update_data()

def delete_sent_broadcast(broadcast, delete_btn):
    """
    Callback for when the Delete button is pressed in a sent broadcast row.
    Insert your deletion logic here, for example calling a method on app_client,
    then refresh the GUI.
    """
    global data
    success = app_client.delete_broadcast(data["uuid"], broadcast.broadcast_id)
    if success:
        broadcast.status = statuses["Deleted"]
    else:
        messagebox.showerror("Error", f"Could not delete broadcast")
    delete_btn.config(state="disabled")
    reload_update_data()

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
    header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
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
        # Create row
        for col in range(3):
            row_frame.columnconfigure(col, weight=1, uniform="sent_cols")
        # Amount Requested
        tk.Label(row_frame, text=str(broadcast.amount_requested), bg="gray20", fg="white",
                 anchor="center")\
            .grid(row=0, column=0, sticky="nsew", padx=15, pady=2)
        # Status
        status_text = statuses_to_word.get(broadcast.status, "Unknown")
        tk.Label(row_frame, text=status_text, bg="gray20", fg="white",
                 anchor="center")\
            .grid(row=0, column=1, sticky="nsew", padx=15, pady=2)
        is_pending = (broadcast.status == statuses["Pending"])
        delete_btn = tk.Button(row_frame, text="Delete", width=8, state="normal" if is_pending else "disabled")
        if is_pending:
            delete_btn.config(command=lambda b=broadcast, db=delete_btn: delete_sent_broadcast(b, db))
        delete_btn.grid(row=0, column=2, sticky="nsew", padx=15, pady=2)
        # tk.Button(row_frame, text="Delete", width=8,
        #           command=lambda b=broadcast: delete_sent_broadcast(b))\
        #     .grid(row=0, column=2, sticky="nsew", padx=15, pady=2)

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
        # Create row
        for col in range(5):
            row_frame.columnconfigure(col, weight=1, uniform="col_width")
        # Username and Amount Requested
        tk.Label(row_frame, text=broadcast.sender_username, bg="gray20", fg="white", anchor="center")\
            .grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
        tk.Label(row_frame, text=str(broadcast.amount_requested), bg="gray20", fg="white", anchor="center")\
            .grid(row=0, column=1, sticky="nsew", padx=5, pady=2)
        # Status and Approve/Deny
        is_pending = (broadcast.status == statuses["Pending"])
        approve_btn = tk.Button(row_frame, text="Approve", width=8, state="normal" if is_pending else "disabled")
        deny_btn = tk.Button(row_frame, text="Deny", width=8, state="normal" if is_pending else "disabled")
        if is_pending:
            approve_btn.config(command=lambda b=broadcast, ab=approve_btn, db=deny_btn: approve_broadcast(b, ab, db))
            deny_btn.config(command=lambda b=broadcast, ab=approve_btn, db=deny_btn: deny_broadcast(b, ab, db))
        approve_btn.grid(row=0, column=2, sticky="nsew", padx=5, pady=2)
        deny_btn.grid(row=0, column=3, sticky="nsew", padx=5, pady=2)
        status_text = statuses_to_word.get(broadcast.status, "Unknown")
        tk.Label(row_frame, text=status_text, bg="gray20", fg="white", anchor="center")\
            .grid(row=0, column=4, sticky="nsew", padx=5, pady=2)

# ++++++++++++++  Main Function  ++++++++++++++ #
if __name__ == "__main__":
    load_login_frame()
    gui.mainloop()