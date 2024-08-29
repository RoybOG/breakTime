input("starting")

from enum import Enum
import re, os, time
from threading import Thread, Event

import configparser

from pynput import keyboard
import win32gui
from plyer import utils; platform = utils.platform
from plyer import notification
#







#-------------- utils --------------------
class ProgramState(Enum):
    WAITING = 0
    SESSIONSTARTED = 1
    BREAKTIME = 2



is_str_float = lambda s,can_be_whole=True: bool(re.match('^[0-9]+\.'+('?' if can_be_whole else '')+'[0-9]*$', s))
is_str_hour_format = None
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


stopping_left = 3

AVOIDKEYWORDS = ['breaktime','breakTimeConfig']
DEFUALTWINDOWSTOAVOID = ["action center","volume control","task manager","network connections"]


DEFUALT_NOTIFICATION_SCHEDULES = {0.5,0.75, 0.9}


def time_format(time_amount):

    time_amount = int(time_amount)
    if time_amount==0:
        return "0 seconds"


    output_parts = []
    d=time_amount //(60*60)
    if d:
        output_parts.append(str(d)+' hour'+('s' if d>1 else ''))
        time_amount %=(60*60)

    d = time_amount // 60
    if d:
        output_parts.append(str(d)+' minute'+('s' if d>1 else ''))
        time_amount %=60
    if time_amount:
        output_parts.append(str(time_amount)+' second'+('s' if time_amount>1 else ''))

    if(len(output_parts)>1):
        return ', '.join(output_parts[:-1]) + ' and ' + output_parts[-1]

    return output_parts[0]


# ------------------- config setup ----------------------------

CONFIG_NAME = 'breakTimeConfig.ini'
DEFUALT_CONFIG = """
[settings]
defualt break time = 3
defualt session time = 30
stopping key = P
#The stopping key currently can only be one character: a-z, A-Z, 0-9, !@#$ etc...
amount of times allowed to stop = 3 
#If you set it to 0, the app will be in strict mode, you won't be able to stop in the middle of a session or prevent a break.
#If you leave empty, you can stop as many times as you want
text for break time = 






[windows to keep open]
action center
volume control
manager
"""


config = configparser.ConfigParser(allow_no_value=True)

def get_minutes_from_format(config_var_str):
    if not config_var_str:
        return None


    if config_var_str.isnumeric():
        return int(config_var_str)

    if is_str_float(config_var_str, False):
        return round(float(config_var_str)*60)

    m = re.match('^(?P<hours>\d{1,2})\:(?P<minutes>\d{0,2})$',config_var_str)

    if m:
        hours = int(m.group('hours') or '0')
        minutes = int(m.group('minutes') or '0')
        if hours<24 and minutes<60:
            return hours*60+minutes

    return None





def createConfig():
    #config['settings'] = {'breakTimeLength': '3'}
    global config
    config.read_string(DEFUALT_CONFIG)
    with open(CONFIG_NAME, 'w') as configFile:
        config.write(configFile)

def readConfig():
    global config
    global stopping_left
#    'YELLOW.ini')
    if os.path.exists(CONFIG_NAME):
        config.read(CONFIG_NAME)
        # checking for bad syntax from user

        if len(config.get("settings", "stopping key")) != 1:
            raise ValueError('The stopping key currently can only be one character: a-z, A-Z, 0-9, !@#$ etc...')

        if not (is_str_float(config.get("settings", "defualt break time"))):
            raise ValueError('The value for "defualt break time" in the config file is not a number or a float')

        if not config.get("settings", "amount of times allowed to stop") \
                or config.get("settings", "amount of times allowed to stop").isnumeric():
            stopping_left = config.get("settings", "amount of times allowed to stop")
            stopping_left = int(stopping_left) if stopping_left else None

        else:
            raise ValueError('The value for "amount of times allowed to stop" is not a whole number or empty')

    else:
        createConfig() #The user won't be fast enough to modify the config here



# -------- keyboard controlller setup ---------------

evnt = Event()

state = ProgramState.WAITING
last_time_paused = None
keybaord_con = keyboard.Controller()


def on_press(key):
    global last_time_paused
    global stopping_left
    try:
        #print("I can't stop, and you know why")
        if(key.char == config.get("settings","stopping key") and state!= ProgramState.WAITING):
            focused_window_title = get_focused_window_title().lower()

            if 'breaktime' not in focused_window_title: #To make sure you won't stop a session from a different window
                return


            if stopping_left == 0:
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

            if stopping_left:
                stopping_left -= 1
                if stopping_left==0:
                    print("next time you won't be able to stop...")
                else:
                    print("you have",stopping_left,"time"+('' if stopping_left==1 else 's'),"left to stop a session")


    except AttributeError:
        pass
        #print('special key {0} pressed'.format(key))




def minimizeAllWindows():

    focused_window_title_raw = get_focused_window_title()

    focused_window_title = focused_window_title_raw.lower()

    if focused_window_title and not includesKeyWords(focused_window_title,AVOIDKEYWORDS) \
            and not (focused_window_title in DEFUALTWINDOWSTOAVOID or focused_window_title in DEFUALTWINDOWSTOAVOID):
        print('window "{}" was opened during break!'.format(focused_window_title_raw))
        with keybaord_con.pressed(keyboard.Key.cmd):
            keybaord_con.press('m')
            keybaord_con.release('m')



# ---------- limit screen function ------------

def breakTime(runningTime, runningRate):

    startT = time.time()

    while time.time()-startT < runningTime:
        if not evnt.is_set():
            evnt.set()
            break

        minimizeAllWindows()
        time.sleep(runningRate)





def limitScreen(screen_limit_duration, break_duration,notificationsChedules=None):
    global state
    notificationsChedules = notificationsChedules or []
    convertToMinutes = lambda t: round(t / 60, 2)
    notificationsChedules = sorted(DEFUALT_NOTIFICATION_SCHEDULES.union(set(notificationsChedules)))

    notificationsChedules.sort()
    #print(notificationsChedules)
    start_time = time.localtime()
    timeSlept = 0

    """
    def check_for_event():
        if not evnt.is_set():
            evnt.set()
            return True

        return False
    """

    def app_notifiy(title, message):

        notification.notify(
            title=title,
            message=message,

            # displaying time
            timeout=300
        )
        print(time.strftime("%H:%M:%S", time.localtime()),":",title)


    def sleptAggrigate(sleepTime):
        nonlocal timeSlept
        print("waiting for ", time_format(sleepTime))
        evnt.wait() #if the user pauses before the sleep, then wait and then keep sleeping
        waitedSince = time.time()
        #print("{}: break in {} minutes!".format(time.strftime("%H:%M:%S", time.localtime()), convertToMinutes(screen_limit_duration - timeSlept)))
        app_notifiy(time_format(screen_limit_duration - timeSlept)+" till break time!",
                time_format(timeSlept)+" passed since the session began at "+time.strftime("%H:%M:%S", start_time))

        time.sleep(sleepTime)
        if not evnt.is_set():
            evnt.wait()
            print("wait for ", time_format(sleepTime-(last_time_paused-waitedSince)))
            time.sleep(sleepTime-(last_time_paused-waitedSince)) #if the user pauses after the sleep, then wait and then keep sleepin


        timeSlept +=sleepTime



    for notificationTime in notificationsChedules:
        if notificationTime>1:
            raise ValueError("notification schedules should be less then 1!")


        sleptAggrigate(screen_limit_duration*notificationTime-timeSlept)

    #print("{}: {}".format((time.strftime("%H:%M:%S", time.localtime())),"Take a break for {} minutes!".format(convertToMinutes(break_duration))))

    state = ProgramState.BREAKTIME
    app_notifiy(
        title="Break Time!",
        message="Take a break for "+time_format(break_duration)
    )

    #timerDecorator(break_duration, 1, check_for_event)(minimizeAllWindows)()
    breakTime(break_duration,1)
    app_notifiy("Welcome Back!","Now you can go back to work!")




def run_session():
    global state


    session_time = get_minutes_from_format(input("How many minutes will this session be: ").strip() or config.get("settings","defualt session time"))
    break_time = get_minutes_from_format(config.get("settings","defualt break time"))

    while(not session_time or not break_time): #Also check if bigger than zero in here and config input
        session_time = get_minutes_from_format(input("The values for session time and break time needs"
                                 " to be a number a float or in time format 'HH:MM' "
                                 "\ncheck your config file or rewrite here how many minutes: ").strip())
        readConfig()
        session_time = session_time or get_minutes_from_format(config.get("settings","defualt session time"))
        break_time = get_minutes_from_format(config.get("settings", "defualt break time"))



    else:
        state = ProgramState.SESSIONSTARTED
        limitScreen(session_time*60,break_time*60)

    evnt.wait()
    state = ProgramState.WAITING



def main():
    try:
        print('Welcome To BreakTime!')
        readConfig() #setting up config
        evnt.set()  # setting up the keybaord listener
        listener = keyboard.Listener(
        on_press=on_press)
        listener.start()
        while True:


            run_session()
            print("session ended")



            input('For another session, press ENTER.\n')
    except Exception as error:
        print(error)



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