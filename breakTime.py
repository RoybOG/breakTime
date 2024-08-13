#import pyautogui
import keyboard
import re
import time
#from ctypes import wintypes, windll, create_unicode_buffer, cdll
import win32gui
from plyer import utils; platform = utils.platform
#from plyer.utils import platform
from plyer import notification
#


listToAvoid = []
def getWindowTitle(hwnd, ):

    length = cdll.user32.GetWindowTextLengthW(hwnd)
    buff = create_unicode_buffer(length + 1)
    cdll.user32.GetWindowTextW(hwnd, buff, length + 1)
    #if buff.value:
    return buff.value




def timerDecorator(runningTime, runningRate):

    def decorator(func):
        def inner(*args, **kwargs):
            startT = time.time()

            while time.time()-startT < runningTime:
                func(*args, **kwargs)
                time.sleep(runningRate)

        return inner

    return decorator



DEFUALT_SESSIONTIME = 45 * 60
DEFAULT_BREAKTIME = 2 * 60
DEFUALT_NOTIFICATION_SCHEDULES = {0.5,0.75, 0.9}

exclude_keyWords = ['breaktime', 'manager','.py']


def includesKeyWords(str):
    if not str:
        return False

    for kw in exclude_keyWords:
        if kw in str.lower():
            return True
    else:
        return False


def minimizeAllWindows():
    #print("window",win32gui.GetWindowText(win32gui.GetForegroundWindow()), "detected")
    if not includesKeyWords(win32gui.GetWindowText(win32gui.GetForegroundWindow())):

        keyboard.press_and_release('windows+m')


def limitScreen(screen_limit_duration=DEFUALT_SESSIONTIME, break_duration=DEFAULT_BREAKTIME,notificationsChedules=None):
    notificationsChedules = notificationsChedules or []
    convertToMinutes = lambda t: round(t / 60, 2)
    notificationsChedules = sorted(DEFUALT_NOTIFICATION_SCHEDULES.union(set(notificationsChedules)))

    notificationsChedules.sort()
    #print(notificationsChedules)
    start_time = time.localtime()
    timeSlept = 0

    def app_notifiy(title, message):
        print("{}: {}".format(time.strftime("%H:%M:%S", time.localtime()), title))
        notification.notify(
            title=title,
            message=message,

            # displaying time
            timeout=300
        )


    def sleptAggrigate(sleepTime):
        nonlocal timeSlept
        app_notifiy("עוד {} דקות הפסקה".format(convertToMinutes(screen_limit_duration - timeSlept)),
                "עברו {} דקות מאז תחילת הסשן ב {}".format(convertToMinutes(timeSlept),
                                                          time.strftime("%H:%M:%S", start_time)))

        time.sleep(sleepTime)
        timeSlept +=sleepTime



    for notificationTime in notificationsChedules:
        if notificationTime>1:
            raise ValueError("notification schedules should be less then 1!")


        sleptAggrigate(screen_limit_duration*notificationTime-timeSlept)

    print("{}: {}".format((time.strftime("%H:%M:%S", time.localtime())),
                          "זמן הפסקה למשך {} דקות".format(convertToMinutes(break_duration))))
    app_notifiy(
        title="זמן הפסקה",
        message="זמן הפסקה למשך {} דקות".format(convertToMinutes(break_duration))
    )
    timerDecorator(break_duration, 1)(minimizeAllWindows)()
    app_notifiy("אתה יכול לחזור לעבוד","בהצלחה")


def main():
    print('Welcome To BreakTime!')

    while True:
        session_time = input("How many minutes will this session be: ").strip()
        try:
            if not session_time:
                limitScreen()
            else:
                while(not re.match('^[0-9.]+$',session_time)):
                    session_time = input("The input needs to be a number!\nhow many minutes: ").strip() or str(defualt_session)
                else:
                    limitScreen(60*float(session_time))
        except Exception as error:
            print(error)
        finally:
            input('For another session, press ENTER')



main()
#minimizeAllWindows()
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
#  pyinstaller --onefile --clean --icon=favicon.ico --distpath D:\Users\Itai\Desktop breakTime.py

# pyinstaller --onefile --clean --icon=favicon.ico --hidden-import plyer.platforms.win.notification --distpath D:\Users\Itai\Desktop breakTime.py