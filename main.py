

from tkinter import E
import pydivert     # for cx_Freeze?
from filter import DropLengthSettings, Filter, FilterFlags, FilterSettings
from msvcrt import kbhit, getch   # For getting keyboard input.
from time import sleep, time
from menu_options import Menu, MenuNames
from os import system
from webbrowser import open as open_in_browser
from logger import Logger
from multiprocessing import Queue as ProxyQueue, freeze_support
from traceback import format_exc
from settings import Settings
from ctypes import windll
from sys import exit as sys_exit

DONATE = "https://www.linkedin.com/in/bugmikey/"



def get_filter_flags():
    flags = FilterFlags(False)
    if Menu.IS_DROP_INC_80: flags |= FilterFlags.DROP_INC_80
    if Menu.IS_DROP_CLIENT_POST: flags |= FilterFlags.DROP_CLIENT_POST
    if Menu.IS_DROP_LENGTH: flags |= FilterFlags.DROP_LENGTH
    return flags


def get_filter_settings():
    return FilterSettings(get_filter_flags(), get_drop_lengths())


def get_drop_lengths():
    return DropLengthSettings(max_offset=500)


def is_capslock_enabled():
    keycode_caps_lock = 0x14
    return windll.user32.GetKeyState(keycode_caps_lock)


def wait_for_valid_key(menu):
    while True:
        if kbhit():                                  # User has pressed a key
            key = getch()                            # Save what key was pressed
            if is_capslock_enabled():
                key = key.lower()                    # Make sure that CAPS LOCK doesn't affect user input
            try:
                if key !=E:
                    return menu[key.decode()]        # See if there was an option associated with this key
            except (KeyError, UnicodeDecodeError):
                pass                                 # Invalid keys are ignored
        sleep(3)


def trigger_auto_action(menu_item):
    try:
        menu_item["action"](menu_item["name"])      # Try to trigger automatic action
    except KeyError:
        pass                                        # Didn't have an action


def main():
    start = time()
    Logger.static_add_message("Booting up program.")
    logger = Logger(ProxyQueue())
    logger.add_message("Logger initialized.")
    logger.start()                              # Run the logger all the time. Pass the queue to Filter when necessary.
    logger.add_message("Logger process is now running.")
    is_filter_running = False                   # filter will not be running at boot
    config = Settings(Menu.get_options())       # load settings, will save default options if doesn't exist
    Menu.set_options(config.get_settings())     # set options according to config file
    logger.add_message("Loaded config settings: " + str(config.get_settings()))
    Menu.update_menu()                          # force update
    filter_obj = Filter(get_filter_settings())
    previous_menu_state = None                  # helps check if overall state changed
    should_exit = False                         # shouldn't exit immediately
    while not should_exit:
        # At this point in the UI loop, we should check if menu state changed.
        Menu.update_menu()                                      # Update settings before printing
        system('cls')                                           # Clear the command prompt screen
        current_menu_state = Menu.get_options()
        #if previous_menu_state != current_menu_state:          # If a setting has changed
        if True:                                                # DEBUG: Force update every time
            logger.add_message("Menu state has changed: " + str(previous_menu_state) + " -> " + str(current_menu_state))
            config.write_settings(current_menu_state)           # Update config file
            previous_menu_state = current_menu_state
            if Menu.IS_FILTER_RUNNING:                          # Filter should be running
                settings = get_filter_settings()
                if settings.flags == FilterFlags(False):        # No filters are being applied
                    logger.add_message("WARN: User attempted to start network filter with no filters applied.")
                    print(Menu.ERR_MSG_NO_FILTERS)              # Tell the user something's wrong
                    Menu.IS_FILTER_RUNNING = False              # Filter should no longer be running
                    config.write_settings(Menu.get_options())   # Force updated an option
                    Menu.update_menu()                          # Force menu to update (since we're overriding a value)
                    current_menu_state = Menu.get_options()     # The menu state has now changed (probably bad fix)
                else:
                    logger.add_message("Starting network filter...")
                
                    logger_queue = logger.queue if Menu.IS_LOGGING else None
                    filter_obj = Filter(FilterSettings(get_filter_flags(),
                                                       drop_lengths=get_drop_lengths(),
                                                       logger_queue=logger_queue))
                    filter_obj.start()                          # Re-initialize filter with new settings
                    logger.add_message("Started network filter.")

            if is_filter_running and not Menu.IS_FILTER_RUNNING:# Filter is currently running but shouldn't be
                logger.add_message("Stopping network filter...")
                filter_obj.stop()
                logger.add_message("Successfully stopped network filter.")

            is_filter_running = Menu.IS_FILTER_RUNNING          # Update filter state

        # Now we have processed the menu changes, we can prompt again.
        print(Menu.construct_print_options(Menu.MAIN_OPTIONS))

        option = wait_for_valid_key(Menu.MAIN_OPTIONS)          # Wait until we get a valid option
        trigger_auto_action(option)                             # Attempt to trigger its' automatic action

        if option["name"] == MenuNames.ADJUST_FILTER:
            should_go_back = False
            while not should_go_back:
                Menu.update_menu()
                system('cls')
                print(Menu.construct_print_options(Menu.FILTER_OPTIONS))    # New Menu to print

                option2 = wait_for_valid_key(Menu.FILTER_OPTIONS)
                trigger_auto_action(option2)

                if option2["name"] == MenuNames.FILTER_SETTINGS_GO_BACK:     # Time to go back
                    should_go_back = True

        if option["name"] == MenuNames.OPEN_DONATION_URL:
            logger.add_message("User selected OPEN_DONATION_URL...")
            open_in_browser(DONATE)
            sleep(3)    # Pause the UI thread so we don't open 10 billion pages

        if option["name"] == MenuNames.EXIT_PROGRAM:
            logger.add_message("User selected EXIT_PROGRAM...")
            if is_filter_running:
                logger.add_message("Stopping network filter...")
                filter_obj.stop()                               # Stop the filter if it is running
                logger.add_message("Successfully stopped network filter.")
            should_exit = True                                  # Inform the UI loop that we're done

    # Bye!
    logger.add_message("Program ended from menu")
    logger.stop()
    logger.add_message("Logger process has been stopped.")


if __name__ == "__main__":
    freeze_support()
    system('mode con: cols=92 lines=30')       # make console wider to fit all text
    windll.kernel32.SetConsoleTitleW()
    if not windll.shell32.IsUserAnAdmin():     # need admin perms
        Logger.static_add_message("User attempted to run program without Administrator permissions")
        print("\n This program requires Administrator permissions to run.\n"
               " Press any key to continue...")
        while True:
            if kbhit(): sys_exit(1)
            sleep(0.5)
    try:
        main()
    except (Exception, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            Logger.static_add_message("User ended program forcefully")
        else:
            Logger.static_add_message("Oops! Looks like the program crashed. Reason: " + str(e))
            Logger.static_add_message(format_exc())
            raise   