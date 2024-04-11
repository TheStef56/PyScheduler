from datetime import datetime, timedelta
import threading, ctypes, time

class Scheduler:
    class KillableThread(threading.Thread):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            threading.Thread.__init__(self, *self.args, **self.kwargs)

        def get_id(self):    
            if hasattr(self, '_thread_id'):
                return self._thread_id
            for id, thread in threading._active.items():
                if thread is self:
                    return id
    
        def raise_exception(self):
            thread_id = self.get_id()
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print(f'Could not kill thread with pid {thread_id}')

    def __init__(self, blocking = True, interval = 60,
                                        mon: str | None = None,
                                        tue: str | None = None,
                                        wed: str | None = None,
                                        thu: str | None = None,
                                        fri: str | None = None,
                                        sat: str | None = None,
                                        sun: str | None = None) -> None:
        
        """
            Time format to use: `mon="15:30"`, `tue="09:15"`, etc

            `blocking` = `True` (default) will call the function directly,
            `blocking` = `False` will start the function on a separate thread.
            `interval` = `60` is how many seconds the main loop will sleep before checking
            if it is the time to run the function.
            That thread can be killed with `Scheduler.stop_thread()`.
            
            Don't set as function a function that sleeps forever, or the
            thread won't be killed with stop_thread().
        """
        self.blocking = blocking
        self.interval = interval
        self.__thread__: self.KillableThread | None = None
        self.schedules = {
            0: mon,
            1: tue,
            2: wed,
            3: thu,
            4: fri,
            5: sat,
            6: sun,
        }


    def __call_func__(self):
        self.function(*self.args, **self.kwargs)

    def __now_str_to_min__(self, now_str) -> int | None:
        if not now_str:
            return None
        return int(now_str.split(":")[0])*60 + int(now_str.split(":")[1])

    def __get_sleep_time__(self) -> int:
        today = datetime.today().weekday()
        now_str = datetime.now().strftime("%H:%M")
        now_min = self.__now_str_to_min__(now_str)

        for index in range(today, 13):
            cidx = index%7
            schedule = self.schedules[cidx]
            int_schedule = self.__now_str_to_min__(schedule)
            if schedule:
                if today == cidx:
                    if int_schedule > now_min:
                        return (int_schedule - now_min) * 60 
                    elif now_min == int_schedule:
                        return 0
                else:
                    return ((cidx - today + 7)%7 * 24 * 60 + int_schedule - now_min) * 60
                
    def __main_loop__(self) -> None:
        while True:
            while self.__get_sleep_time__() > 0:
                time.sleep(1)
            self.__call_func__()
            time.sleep(self.interval)

    def set_function(self, function: callable, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def start(self) -> None:
        if self.blocking:
            self.__main_loop__()
        else:
            self.__thread__  = self.KillableThread(target=self.__main_loop__)
            self.__thread__.start()
    
    def stop_thread(self) -> None:
        self.__thread__.raise_exception()