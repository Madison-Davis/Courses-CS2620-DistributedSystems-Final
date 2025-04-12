# gui.py


# +++++++++++++ Imports and Installs +++++++++++++ #
import os
import sys
import client
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tkinter import ttk


# ++++++++++++  Variables: Client Data  ++++++++++++ #
# Initialize client gRPC comms and data
# Both of these will be filled once one presses login button (so no need to edit)
app_client = None
data = {}


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
def grab_user_data(username, pwd, region):
    """
    If returning user, grab their data to load onto gui.
    Otherwise, set it to the default for a new user.
    """
    global data
    # TODO: query server and delete this hard-coded version of data
    data = {
        "username" : username,
        "password" : pwd,
        "capacity" : 0,
        "num_dogs" : 0,
        "region"   : region,
        "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
        "broadcast_sendouts" : [(1, "pending"), (2, "accepted"), (3, "none")],
        "broadcast_received" : [("A", 2), ("B", 5)]
    }
    return data

def button_enter_login(user, pwd, region, is_new):
    """
    Fired when a user presses the login button
    Connect to its region's server
    Grab data to populate main frame
    """
    # populate data {} based on if they are new user or returning
    global data, app_client
    app_client = client.AppClient(region)
    if is_new:
        data = {
            "username" : user,
            "password" : pwd,
            "capacity" : 0,
            "num_dogs" : 0,
            "region"   : region,
            "shelter_locations" : [(30, 60), (45, 120), (60, 150)],
            "broadcast_sendouts" : [(1, "pending"), (2, "accepted"), (3, "none")],
            "broadcast_received" : [("A", 2), ("B", 5)]
        }
    else:
        data = grab_user_data(user, pwd, region)
    # load main frame
    login_frame.pack_forget()
    load_main_frame(data)


# ++++++++++++ Helper Functions: Button Presses ++++++++++++ #
def button_stats_numdogs(delta, gui_label):
    """
    User decided to increment/decrement # of dogs they have.
    Reflect change on GUI.
    """
    global data
    data['num_dogs'] = data['num_dogs'] + delta
    gui_label.config(text=f"Capacity: {data["capacity"]}\nCurrent No. Dogs: {data['num_dogs']}")
    pass


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
        entries['password'] = tk.Entry(field_container, show='*')
        entries['password'].grid(row=row+1, column=0, padx=5)
        row += 2
        # Submit button
        def submit():
            user = entries['username'].get()
            pwd = entries['password'].get()
            region = entries['region'].get() if 'region' in entries else None
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
    tk.Label(menu_subframe, text=f"Shelter: {data["username"]}", fg="white", bg="gray20", font=('Arial', 12)).pack(pady=10)
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
    stats_label = tk.Label(stats_subframe, text=f"Capacity: {data["capacity"]}\nCurrent No. Dogs: {data["num_dogs"]}")
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
    entry.pack(side='left', padx=5, pady=5)
    tk.Button(broadcast_subframe, text="Send").pack(side='left', padx=5, pady=5)
    
    # Row 1: sent-out broadcasts
    sent_out_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, relief='solid', bg="gray20")
    sent_out_broadcasts_frame.grid(row=1, column=2, rowspan=2, sticky='nsew', padx=5, pady=5)
    tk.Label(sent_out_broadcasts_frame, text="Sent Broadcasts", bg="gray20", fg="white", font=("Helvetica", 14)).pack()
    sent_outs_table = ttk.Treeview(sent_out_broadcasts_frame, columns=("ID", "Status", ""), show="headings")
    sent_outs_table.heading("ID", text="Dogs")
    sent_outs_table.heading("Status", text="Status")
    sent_outs_table.heading("", text="Delete")
    sent_outs_table.pack(fill='both', expand=True)
    for shelter_id, status in data["broadcast_sendouts"]:
        sent_outs_table.insert("", "end", values=(shelter_id, status, "X"))
    
    # Row 2: received Broadcasts
    received_broadcasts_frame = tk.Frame(main_frame, highlightbackground="black", highlightthickness=1, relief='solid', bg="gray20")
    received_broadcasts_frame.grid(row=3, column=2, rowspan=3, sticky='nsew', padx=5, pady=5)
    tk.Label(received_broadcasts_frame, text="Received Broadcasts", bg="gray20", fg="white", font=("Helvetica", 14)).pack()
    receives_table = ttk.Treeview(received_broadcasts_frame, columns=("From", "Dogs", "Action"), show="headings")
    receives_table.heading("From", text="From Shelter")
    receives_table.heading("Dogs", text="# Dogs")
    receives_table.heading("Action", text="Accept/Reject")
    receives_table.pack(fill='both', expand=True)
    for sid, dogs in data["broadcast_received"]:
        receives_table.insert("", "end", values=(sid, dogs, "Yes/No"))

    # ++++++++++ Add Frames to GUI ++++++++++ #
    gui.update()
    main_frame.grid(row=0, column=0, sticky="nsew")


# ++++++++++++++  Main Function  ++++++++++++++ #
if __name__ == "__main__":
    load_login_frame()
    gui.mainloop()