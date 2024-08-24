#import pyautogui
#import keyboard
import re, os, time
#from ctypes import wintypes, windll, create_unicode_buffer, cdll
import win32gui
from threading import Thread, Event
from plyer import utils; platform = utils.platform
#from plyer.utils import platform
from plyer import notification
#
import configparser
from pynput import keyboard

from enum import Enum

class ProgramState(Enum):
    WAITING = 0
    SESSIONSTARTED = 1
    BREAKTIME = 2



CONFIG_NAME = 'breakTimeConfig.ini'
DEFUALT_CONFIG = """
[settings]
defualt break time = 3
defualt session time = 30
Strict Mode = True 
stopping key = p
#In Strict Mode, you can't stop a session in the middle of it or prevent a break


[windows to keep open]
action center
volume control
manager
"""

AVOIDKEYWORDS = ['breaktime','breakTimeConfig']
DEFUALTWINDOWSTOAVOID = ["action center","volume control","task manager","network connections"]


DEFUALT_NOTIFICATION_SCHEDULES = {0.5,0.75, 0.9}

#config.get("settings","defualt break time")




config = configparser.ConfigParser(allow_no_value=True)


def createConfig():
    #config['settings'] = {'breakTimeLength': '3'}
    global config
    config.read_string(DEFUALT_CONFIG)
    with open(CONFIG_NAME, 'w') as configFile:
        config.write(configFile)

def readConfig():
    global config

#    'YELLOW.ini')
    if os.path.exists(CONFIG_NAME):
        config.read(CONFIG_NAME)
    else:
        createConfig()

    # checking for bad syntax

    #if config.get("settings","stopping key")


evnt = Event()

state = ProgramState.WAITING
last_time_paused = None
keybaord_con = keyboard.Controller()

def on_press(key):
    global last_time_paused
    try:
        #print("I can't stop, and you know why")
        if(key.char == config.get("settings","stopping key")):
            focused_window_title = get_focused_window_title().lower()

            if 'breaktime' not in focused_window_title: #To make sure you won't stop a session from a different window
                return


            if config.getboolean('settings','Strict Mode'):
                print("I can't stop the session and you know why... :P")
                return

            match state:
                case ProgramState.SESSIONSTARTED:
                    last_time_paused = time.time()

                    evnt.clear()
                    input(time.strftime("%H:%M:%S", time.localtime())+": Session Stopped. press ENTER to resume.\n")
                    evnt.set()
                case ProgramState.BREAKTIME:
                    print("Break stopped")
                    evnt.clear()

    except AttributeError:
        pass
        #print('special key {0} pressed'.format(key))










is_str_numeric = lambda s: bool(re.match('^[0-9]+\.?[0-9]*$', s))
convert_to_minutes = lambda min_str: 60 * float(min_str)
get_focused_window_title = lambda: win32gui.GetWindowText(win32gui.GetForegroundWindow())



def includesKeyWords(str, keywords_list):
    if not str:
        return False

    for kw in keywords_list:
        if kw in str:
            return True
    else:
        return False


def minimizeAllWindows():

    focused_window_title = get_focused_window_title()
    print("window",focused_window_title, "was opened during break!")
    focused_window_title = focused_window_title.lower()

    if focused_window_title and not includesKeyWords(focused_window_title,AVOIDKEYWORDS) \
            and not (focused_window_title in DEFUALTWINDOWSTOAVOID or focused_window_title in DEFUALTWINDOWSTOAVOID):

        with keybaord_con.pressed(keyboard.Key.cmd):
            keybaord_con.press('m')
            keybaord_con.release('m')


def limitScreen(screen_limit_duration, break_duration,notificationsChedules=None):
    global state
    notificationsChedules = notificationsChedules or []
    convertToMinutes = lambda t: round(t / 60, 2)
    notificationsChedules = sorted(DEFUALT_NOTIFICATION_SCHEDULES.union(set(notificationsChedules)))

    notificationsChedules.sort()
    #print(notificationsChedules)
    start_time = time.localtime()
    timeSlept = 0

    def check_for_event():
        if not evnt.is_set():
            evnt.set()
            return True

        return False

    def app_notifiy(title, message):

        notification.notify(
            title=title,
            message=message,

            # displaying time
            timeout=300
        )


    def sleptAggrigate(sleepTime):
        nonlocal timeSlept
        print("waiting for ", str(sleepTime))
        evnt.wait() #if the user pauses before the sleep, then wait and then keep sleeping
        waitedSince = time.time()
        print("{}: break in {} minutes!".format(time.strftime("%H:%M:%S", time.localtime()), convertToMinutes(screen_limit_duration - timeSlept)))
        app_notifiy("עוד {} דקות הפסקה".format(convertToMinutes(screen_limit_duration - timeSlept)),
                "עברו {} דקות מאז תחילת הסשן ב {}".format(convertToMinutes(timeSlept),
                                                          time.strftime("%H:%M:%S", start_time)))

        time.sleep(sleepTime)
        if not evnt.is_set():
            evnt.wait()
            print("wait for ", str(sleepTime-(last_time_paused-waitedSince)))
            time.sleep(sleepTime-(last_time_paused-waitedSince)) #if the user pauses after the sleep, then wait and then keep sleepin


        timeSlept +=sleepTime



    for notificationTime in notificationsChedules:
        if notificationTime>1:
            raise ValueError("notification schedules should be less then 1!")


        sleptAggrigate(screen_limit_duration*notificationTime-timeSlept)

    print("{}: {}".format((time.strftime("%H:%M:%S", time.localtime())),
                          "זמן הפסקה למשך {} דקות".format(convertToMinutes(break_duration))))

    state = ProgramState.BREAKTIME
    app_notifiy(
        title="זמן הפסקה",
        message="זמן הפסקה למשך {} דקות".format(convertToMinutes(break_duration))
    )

    timerDecorator(break_duration, 1, check_for_event)(minimizeAllWindows)()
    app_notifiy("אתה יכול לחזור לעבוד","בהצלחה")


def timerDecorator(runningTime, runningRate,checkToStop=None):

    checkToStop = checkToStop or (lambda : True)
    def decorator(func):
        def inner(*args, **kwargs):
            startT = time.time()

            while time.time()-startT < runningTime:
                if checkToStop():
                    break

                func(*args, **kwargs)
                time.sleep(runningRate)

        return inner

    return decorator


def run_session():
    global state

    state = ProgramState.SESSIONSTARTED
    session_time_str = input("How many minutes will this session be: ").strip() or config.get("settings","defualt session time")

    while(not is_str_numeric(session_time_str)):
        print(config.get("settings", "defualt session time"))
        session_time_str = input("The input here or from the config file needs to be a number!\nhow many minutes: ").strip() or config.get("settings","defualt session time")
        readConfig()

    else:
        print(config.get("settings","defualt break time"))
        if not(is_str_numeric(config.get("settings","defualt break time"))):
            raise ValueError('The value for "defualt break time" in the config file is not a number or a float')

        limitScreen(convert_to_minutes(session_time_str),
                    convert_to_minutes(config.get("settings","defualt break time")))

    evnt.wait()
    state = ProgramState.WAITING






def main():
    print('Welcome To BreakTime!')
    readConfig() #setting up config
    evnt.set()  # setting up the keybaord listener
    listener = keyboard.Listener(
        on_press=on_press)
    listener.start()
    while True:

        #try:
        run_session()
        print("session ended")
        #except Exception as error:
            #print(error)

        #finally:
        input('For another session, press ENTER.\n')



main()

"""
nevermind!

create a new shortcut in desktop and for the address copy: 
"""
#    C:\Windows\System32\cmd.exe /k python D:\python\PycharmProjects\RPA\breakTime.py
"""




https://www.icoconverter.com/index.php

delete current version 
and run in terminal it works!

it works the best with the command "pyinstaller" and not "pyinstaller.exe"
"""

# pyinstaller --onefile --clean --icon=favicon.ico --hidden-import plyer.platforms.win.notification --distpath D:\Users\Itai\Desktop breakTime.py