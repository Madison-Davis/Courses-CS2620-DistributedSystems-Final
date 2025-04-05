# client_gui.py

# +++++++++++++ Imports and Installs +++++++++++++ #
import sys
import os
import threading
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tkinter import messagebox, ttk
from client import client_comms



# ++++++++++++  Variables: Client Data  ++++++++++++ #

# Initialize gRPC Client
# client = chat_client.ChatClient()



# +++++++++++++++  Variables: GUI  +++++++++++++++ #

# Vars: TK Frames We Use
gui = tk.Tk()
gui.title("Login")
gui.geometry("1400x670")
login_frame = tk.Frame(gui)
main_frame = tk.Frame(gui)

# Vars: TK Column-Positioning
"""
[Incoming Messages]
1: delete
2: checkbox (on = read, off = unread)
3: message
[Sending Messages]
4: send checkbox
5: message
6: edit
7: save
8: recipient
"""
col_incoming_delete     = 1
col_incoming_checkbox   = 2
col_incoming_message    = 3
col_sending_checkbox    = 4
col_sending_message     = 5
col_sending_edit        = 6
col_sending_save        = 7
col_sending_recipient   = 8
start_row_messages      = 5
start_row_drafts        = 5
incoming_cols = [col_incoming_delete, col_incoming_checkbox, 
                 col_incoming_message, col_incoming_message]
sending_cols = [col_sending_checkbox, col_sending_message, 
                 col_sending_edit, col_sending_save,
                 col_sending_recipient]



# ++++++++++ Helper Functions: Login/Logout ++++++++++ #

def check_username(username):
    # TODO: change
    login_frame.pack_forget()
    load_main_frame()


# ++++++++++++++ Helper Functions: Load Pages ++++++++++++++ #

def load_login_frame():
    """
    Load login frame.
    """
    global login_username, login_pwd, login_frame
    # Destroy login frame if we're logging out/going back after changes
    if login_frame:
        login_frame.destroy()
        login_frame = tk.Frame(gui)
    login_frame.pack(fill='both', expand=True)
    # Part 0: dfine column/row weights
    weights = [10,1,1,1,1,1,1,10]
    for i in range(len(weights)):
        login_frame.rowconfigure(i, weight=weights[i]) 
    login_frame.columnconfigure(0, weight=1) 
    # Part 1: create username label and entry
    # use 'pack' to position relative to other items
    tk.Label(login_frame, text="Enter New or Existing Username:").grid(row=1, column=0, padx=5)
    login_username = tk.Entry(login_frame)
    login_username.grid(row=2, column=0, padx=5)
    # Part 2: determine if new/existing user
    login_username.bind('<Return>', lambda event,username=login_username: check_username(username))

def load_map_with_dots(map_frame, coordinates):
    # Map size (can adjust based on your needs)
    map_width = 740
    map_height = 640
    
    # Create a canvas for the map
    canvas = tk.Canvas(map_frame, width=map_width, height=map_height, bg="lightblue")
    canvas.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
    
    # Define the map boundaries in latitude and longitude
    lat_min = 0   # Minimum latitude (adjust as per your data)
    lat_max = 90  # Maximum latitude (adjust as per your data)
    lon_min = 0   # Minimum longitude (adjust as per your data)
    lon_max = 180 # Maximum longitude (adjust as per your data)

    # Function to convert lat/lon to canvas x, y coordinates
    def lat_lon_to_canvas(lat, lon):
        # Normalize the lat/lon values to the canvas coordinates
        x = (lon - lon_min) / (lon_max - lon_min) * map_width
        y = map_height - (lat - lat_min) / (lat_max - lat_min) * map_height
        return x, y
    
    # Plot dots on the map
    for lat, lon in coordinates:
        x, y = lat_lon_to_canvas(lat, lon)
        canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="black")  # Draw a dot as a small circle

def load_main_frame():
    # Clear any previous widgets from the main_frame
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Part 1: Map Sub-GUI
    # Spans the left column and all rows
    map_frame = tk.Frame(main_frame, width=700, height=600)
    map_frame.grid(row=0, column=0, rowspan=4, padx=10, pady=10, sticky="nsew")
    coordinates = [(30, 60), (45, 120), (60, 150)]  # Example coordinates (latitude, longitude)
    load_map_with_dots(map_frame, coordinates)  # Call the function to lo

    # Part 2: Logout and Delete Account Buttons
    button_frame = tk.Frame(main_frame)  # Create a frame to hold both buttons
    button_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    # Logout button
    logout_button = tk.Button(button_frame, text="Logout")
    logout_button.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    # Delete Account button
    delete_button = tk.Button(button_frame, text="Delete Account")
    delete_button.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    # Ensure both buttons share the same cell within the frame
    button_frame.grid_rowconfigure(0, weight=1)
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    # Part 3: Drafts Sub-GUI
    # Spans the right column, second row
    drafts_frame = tk.Frame(main_frame, bd=2, relief="solid")  # Border and outline around drafts_frame
    drafts_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    drafts_title = tk.Label(drafts_frame, text="Drafts", font=("Helvetica", 14, "bold"))
    drafts_title.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    input1 = tk.Entry(drafts_frame)
    input1.grid(row=1, column=0, padx=5, pady=5)
    input2 = tk.Entry(drafts_frame)
    input2.grid(row=1, column=1, padx=5, pady=5)
    input3 = tk.Button(drafts_frame, text="Send")
    input3.grid(row=1, column=2, padx=5, pady=5)

    # Part 4: Sent-Outs Sub-GUI
    # Spans the right column, third row
    sent_outs_frame = tk.Frame(main_frame)
    sent_outs_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

    sent_outs_title = tk.Label(sent_outs_frame, text="Sent Outs", font=("Helvetica", 14, "bold"))
    sent_outs_title.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    sent_outs_table = ttk.Treeview(sent_outs_frame, columns=("ID", "Status", ""), show="headings")
    sent_outs_table.heading("ID", text="Shelter ID")
    sent_outs_table.heading("Status", text="Status")
    sent_outs_table.heading("", text="Delete")
    sent_outs_table.grid(row=1, column=0, sticky="nsew")
    
    # Example Data
    sent_outs_data = [(1, "pending"), (2, "accepted"), (3, "rejected")]
    for shelter_id, status in sent_outs_data:
        sent_outs_table.insert("", "end", values=(shelter_id, status, "X"))

    # Part 5: Receives Sub-GUI
    # Spans the right column, fourth row
    receives_frame = tk.Frame(main_frame)
    receives_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

    receives_title = tk.Label(receives_frame, text="Receives", font=("Helvetica", 14, "bold"))
    receives_title.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    receives_table = ttk.Treeview(receives_frame, columns=("ID", "", ""), show="headings")
    receives_table.heading("ID", text="Shelter ID")
    receives_table.heading("", text="Yes/No")
    receives_table.grid(row=1, column=0, sticky="nsew")
    
    # Example Data
    receives_data = [(1,), (2,), (3,)]
    for shelter_id in receives_data:
        receives_table.insert("", "end", values=(shelter_id[0], "Yes"))

    # Adjust the row and column weights so the frames expand properly
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_rowconfigure(2, weight=1)
    main_frame.grid_rowconfigure(3, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)

    # Add the main_frame to the GUI
    gui.update()
    main_frame.grid(row=0, column=0, sticky="nsew")




# ++++++++++++++  Main Function  ++++++++++++++ #

if __name__ == "__main__":
    load_login_frame()
    gui.mainloop()