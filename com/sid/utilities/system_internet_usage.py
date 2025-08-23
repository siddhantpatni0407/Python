import psutil
import socket
import tkinter as tk
from tkinter import ttk
import time
import subprocess
import re
from datetime import datetime


# Function to get network usage stats
def get_network_usage():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent, net_io.bytes_recv


# Function to get system and network details (correct Wi-Fi Name)
def get_system_info():
    # System Name (Hostname)
    system_name = socket.gethostname()

    # Get all network interfaces
    network_info = psutil.net_if_addrs()

    # Default value for Wi-Fi name (SSID)
    wifi_name = "Not connected"

    # Try to find Wi-Fi SSID using system commands (Windows example)
    if psutil.LINUX:
        for interface, addrs in network_info.items():
            if 'wlan' in interface:
                wifi_name = addrs[0].address
                break
    elif psutil.WINDOWS:
        wifi_name = get_wifi_ssid_windows()

    # Local IP Address
    ip_address = socket.gethostbyname(system_name)

    # System Boot Time
    boot_time = psutil.boot_time()
    boot_time = datetime.fromtimestamp(boot_time).strftime(
        "%I:%M:%S %p %d/%m/%Y")  # AM/PM time first, then date (DD/MM/YYYY)

    # Get CPU Usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # Get Memory Usage
    memory = psutil.virtual_memory()
    memory_usage = memory.percent

    # Get Disk Usage
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent

    return system_name, wifi_name, ip_address, boot_time, cpu_usage, memory_usage, disk_usage


# Function to fetch Wi-Fi SSID on Windows
def get_wifi_ssid_windows():
    try:
        result = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
        ssid_search = re.search(r"SSID\s*:\s*(.*)", result)
        if ssid_search:
            return ssid_search.group(1)
        else:
            return "Not connected"
    except subprocess.CalledProcessError:
        return "Not connected"


# Function to update the current time in AM/PM format
def get_current_time():
    return datetime.now().strftime("%I:%M:%S %p")  # 12-hour format with AM/PM


# Update the pop-up with new data
def update_stats():
    # Get current network stats
    bytes_sent, bytes_recv = get_network_usage()

    # Convert bytes to MB
    sent_mb = bytes_sent / (1024 * 1024)
    recv_mb = bytes_recv / (1024 * 1024)

    # Get the system info and update the labels in the table
    system_name, wifi_name, ip_address, boot_time, cpu_usage, memory_usage, disk_usage = get_system_info()

    # Get the current time
    current_time = get_current_time()

    # Update the table rows with the data
    treeview.item(system_name_item, values=("System Name", system_name))
    treeview.item(wifi_name_item, values=("Wi-Fi Name", wifi_name))
    treeview.item(ip_address_item, values=("IP Address", ip_address))
    treeview.item(boot_time_item, values=("System Boot Time", boot_time))
    treeview.item(cpu_item, values=("CPU Usage", f"{cpu_usage}%"))
    treeview.item(memory_item, values=("Memory Usage", f"{memory_usage}%"))
    treeview.item(disk_item, values=("Disk Usage", f"{disk_usage}%"))
    treeview.item(sent_item, values=("Data Sent", f"{sent_mb:.2f} MB"))
    treeview.item(recv_item, values=("Data Received", f"{recv_mb:.2f} MB"))
    treeview.item(time_item, values=("Current Time", current_time))

    # Call this function again after 1 second
    window.after(1000, update_stats)


# Create a tkinter window
window = tk.Tk()
window.title("Internet Usage & System Info")

# Set window size and background color
window.geometry("500x500")
window.configure(bg="#2C3E50")  # Dark background

# Set window to be resizable
window.resizable(True, True)

# Add a rounded frame for a modern look
frame = tk.Frame(window, bg="#34495E", bd=10)
frame.pack(padx=20, pady=20, fill="both", expand=True)

# Add a header label with a nice font
header_label = ttk.Label(frame, text="System & Internet Usage", font=("Helvetica", 20, "bold"), foreground="white",
                         background="#34495E")
header_label.pack(pady=10)

# Create a frame to hold the table and scroll bar
table_frame = tk.Frame(frame)
table_frame.pack(fill="both", expand=True)

# Create a Treeview widget to display data in a table format (2 columns)
treeview = ttk.Treeview(table_frame, columns=("Label", "Value"), show="headings", height=12)
treeview.pack(side="left", fill="both", expand=True)

# Add vertical scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=treeview.yview)
scrollbar.pack(side="right", fill="y")
treeview.configure(yscrollcommand=scrollbar.set)

# Define headings for the table
treeview.heading("Label", text="Label")
treeview.heading("Value", text="Value")

# Set a black border for the table
treeview.configure(show="headings", style="Custom.Treeview")

# Add placeholder rows
system_name_item = treeview.insert("", "end", values=("System Name", "Loading..."))
wifi_name_item = treeview.insert("", "end", values=("Wi-Fi Name", "Loading..."))
ip_address_item = treeview.insert("", "end", values=("IP Address", "Loading..."))
boot_time_item = treeview.insert("", "end", values=("System Boot Time", "Loading..."))
cpu_item = treeview.insert("", "end", values=("CPU Usage", "Loading..."))
memory_item = treeview.insert("", "end", values=("Memory Usage", "Loading..."))
disk_item = treeview.insert("", "end", values=("Disk Usage", "Loading..."))
sent_item = treeview.insert("", "end", values=("Data Sent", "0.00 MB"))
recv_item = treeview.insert("", "end", values=("Data Received", "0.00 MB"))
time_item = treeview.insert("", "end", values=("Current Time", "Loading..."))

# Define a style for the treeview
style = ttk.Style()
style.configure("Custom.Treeview",
                font=("Helvetica", 13),  # Increase font size
                rowheight=35,  # Increase row height for readability
                background="#34495E",  # Dark background
                fieldbackground="#34495E",  # Same as background
                foreground="white")  # White text color
style.configure("Custom.Treeview.Heading",
                font=("Helvetica", 13, "bold"),  # Larger headings
                background="black",  # Black background for headers
                foreground="white")  # White text for headers

# Set color for value columns based on data type
def get_value_color(label):
    if label == "Data Sent":
        return "lightgreen"
    elif label == "Data Received":
        return "lightblue"
    elif label == "Current Time":
        return "lightpink"
    elif label == "System Boot Time":
        return "lightyellow"
    elif label == "CPU Usage":
        return "lightcyan"
    elif label == "Memory Usage":
        return "lightcoral"
    elif label == "Disk Usage":
        return "lightseagreen"
    return "white"


# Apply the colors dynamically based on the label value
def update_row_colors():
    for item in treeview.get_children():
        label = treeview.item(item, "values")[0]
        value_color = get_value_color(label)
        treeview.item(item, tags=(value_color,))
    treeview.tag_configure("lightgreen", foreground="lightgreen")
    treeview.tag_configure("lightblue", foreground="lightblue")
    treeview.tag_configure("lightpink", foreground="lightpink")
    treeview.tag_configure("lightyellow", foreground="lightyellow")
    treeview.tag_configure("lightcyan", foreground="lightcyan")
    treeview.tag_configure("lightcoral", foreground="lightcoral")
    treeview.tag_configure("lightseagreen", foreground="lightseagreen")


# Add a footer with a modern look (Developer Info)
footer_label = ttk.Label(window, text="Developer by Siddhant Patni", font=("Helvetica", 10), foreground="gray",
                         background="#2C3E50")
footer_label.pack(side="bottom", anchor="se", padx=10, pady=5)  # Bottom-right corner

# Start the stats update loop
update_stats()

# Update row colors based on the label values
update_row_colors()

# Run the tkinter main loop
window.mainloop()
