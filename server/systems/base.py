import time
from datetime import datetime
from django.utils.timezone import utc

class BaseSystem(object):

    def __init__(self, system_id, env):
        self.id = system_id
        self.env = env
                
        


    def calculate(self):
        pass

    def find_dependent_systems_in(self, system_list):
        pass

    def attach_to_cogeneration_unit(self, system):
        pass

    def attach_to_peak_load_boiler(self, system):
        pass

    def attach_to_thermal_consumer(self, system):
        pass

    def attach_to_electrical_consumer(self, system):
        pass

    def connected(self):
        return True


class BaseEnvironment(object):

    def __init__(self, initial_time=None, step_size=120, demo=False, forecast=False):
        if initial_time is None:
            self.now = time.time()
        else:
            self.now = initial_time

        self.step_size = step_size
        self.demo = demo
        self.initial_date = datetime.fromtimestamp(self.now).replace(tzinfo=utc)
        self.forecast = forecast

    def get_day_of_year(self):
        return time.gmtime(self.now).tm_yday
