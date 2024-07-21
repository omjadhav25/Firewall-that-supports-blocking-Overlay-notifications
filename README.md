# Firewall-that-supports-blocking-Overlay-notifications


Concept:

Overlay notifications are visual elements displayed on top of other applications or the desktop. They can originate from various sources like chat applications, social media platforms, or system alerts. A firewall with overlay notification blocking capabilities would typically target the process responsible for generating these notifications.

Usage:

Download and extract (or build yourself). The direct download link to the latest compiled release is above this message.

Run SCBlocker.exe as Administrator.

Alternatively,

if you have Python, you can run directly from the interpreter by executing python main.py in an elevated command prompt while at the repo directory. If you use this method then no build is needed. If the program is running and the network filter is ON, notifications should now be blocked and won't reach your client. Use the keys on your keyboard to navigate the menu.
Filters:

This app provides three different filtering heuristics that all target different points in the chain of communication between your client and the SocialClub Overlay.

Filter #1 DROP_INC_80 is the fastest and impacts performance the least but you may be flooded with notifications when the filter is turned off.

Filter #2 DROP_CLIENT_POST is enabled by default as the end result is probably what most users are looking for.

