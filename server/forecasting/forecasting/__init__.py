"""
This module contains the statistical forecasting initiation and management.

The base class for all forecastings is :class:`StatisticalForecast`, 
to generate forecasts one of the following subclasses has to be used

.. autosummary::

    ~DSHWForecast
    ~DayTypeForecast

"""

import os
import time
import numpy as np
from multiprocessing import Pool
from datetime import date, datetime, timedelta
from multiprocessing.process import Process
import multiprocessing
from sys import platform as _platform
import cPickle as pickle

from django.utils.timezone import utc
from holt_winters import multiplicative, additive
from server.settings import BASE_DIR
import logging
from server.forecasting.forecasting.holt_winters import double_seasonal

logger = logging.getLogger('simulation')

class StatisticalForecast:
    """
    This is the abstract class for statistical forecasting. Statistical forecasts use exponential smoothing methods
    to forecast timeseries into the future. These methods rely on the right parameters to make a realistic forecast.
    The parameters can be passed to the function, if they are omitted they are found by minimizing the MSE.


    Forecastings are calculated after contruction of class and then whenever needed, 
    which is set by :attr: `forecast_update_interval`.

    :param list input_data: list of consecutive values sampled in ``samples_per_hour``
    :param datetime start: start date of input data
    :param int samples_per_hour: Number of samples per hour in input_data
    :param tuple hw_parameters: holt-winter parameters (depends on Subclass used)
    :param str hw_optimisation: type of minimization measure, if minimization is used

        *   None - given hw_parameters are always used (fastest, hw_parameters required)
        *   "MSE" - Mean Square Error used as optimization parameter for Holt-Winters (default)
        *   "MASE" - Mean Absolute Scaled Error is used. (slowest)
    :param boolean try_cache: Read and Save forecasts to a cache on the file device to avoid unneccesary recomputation, is ``True`` by default.
    :param \*\*kwargs: Any instance variable can be overwritten with a keyword from here, f.e. *input_weeks = 14*. Will be set before any data is processed. Only use, if you know what your doing.

    :ivar int forecast_update_interval: The time in seconds for how long forecasts stay valid. When this interval is passed, a new forecast is calculated. 
    :ivar int input_weeks: only forecast with this many weeks of data, default are 12 weeks.
    :ivar int output_weeks: the forecast will cover this many weeks of future data,default are 8 weeks.
    :ivar [[],] demands: the processed demands, depending on subclass this contains one or more series 

    """

    def __init__(self, env, input_data, samples_per_hour=1, start=None, 
        hw_parameters=(), hw_optimization="MSE", try_cache=True, **kwargs):
        if hw_parameters == ():
            self.hw_parameters = (None, None, None)
        else:
            self.hw_parameters = hw_parameters 

        self.hw_optimization = hw_optimization
        self.calculated_parameters = []
        self.samples_per_hour = samples_per_hour
        self.env = env
        self.try_cache = try_cache
        self.forecast_update_interval = 24 * 60 * 60 
        #
        self.input_weeks = 12 
        self.input_hours = self.input_weeks*24*7*self.samples_per_hour
        self.output_weeks = 8 

        data_length = timedelta(hours=len(input_data) / samples_per_hour)
        #only use days
        data_length = timedelta(days=data_length.days) 
        if start == None:
            start = datetime.utcfromtimestamp(self.env.now).replace(tzinfo=utc) - data_length
            
        #always set to start of day
        start = start.replace(hour=0,minute=0) 
        # ending time of input data
        self.time_series_end = datetime.utcfromtimestamp(self.env.now).replace(tzinfo=utc)

        # overwrite standard instance variables by passing in keyword arguments
        for key in vars(self).keys():
            if key in kwargs:
                setattr(self,key,kwargs[key])

        self.demands = self.process_inputdata(input_data[-self.input_hours:] ,samples_per_hour,start)
        
        #forecast all demands.. might take long
        self.forecasted_demands = self.forecast_demands()
        
    def get_forecast_at(self, timestamp):
        """ Return the forecast at the timestamp.

        :param timestamp: a unix timestamp
        :returns: `single value`

        :raises :py:exc:`IndexError` if there is no forecast for the timestamp."""
        try:
            return self.forecast_at(timestamp)[0]
        except IndexError as e:
            msg = " .. tried to access at a timepoint, for which no forecast is existant"
            logger.error(str(e) + msg)
            raise IndexError(str(e) + msg)

    
    
    def read_from_cache(self):
        """ Return a cached result. If  *try_cache* = ``True``, this will try to read from cache/cached_forecasts.cache. 
        The results are only returned, if the timestamp of the forecast creation is not older than 24h.
        Else or if no cached file is available, ``None`` is returned.

        :returns: `list` or `None`
        """
        if self.try_cache: 
            try:
                cached = pickle.load(open( os.path.join(BASE_DIR,"cache/cached_forecasts.cache"), "rb" ))
                diff_time = datetime.utcfromtimestamp(cached["date"]).replace(tzinfo=utc) - self.time_series_end
                if diff_time.total_seconds() < 24 * 60 * 60: #24 hours epsilon
                    forecasted_demands = cached["forecasts"]
                    self.calculated_parameters = cached["parameters"] 
                    logger.info("read forecasts from cache")
                    return forecasted_demands
            except IOError as e:
                logger.info(str(e) + " .. creating new cache file")
        return None
    
    
    def process_inputdata(self, data, samples_per_hour,start):
        """Preprocess the input demands. Needed for the division into weekdays in :class: `DayTypeForecast`.
        :param datetime start: the time of the first datapoint. Only the day is of interest

        :returns: processed demands
        """
        raise NotImplementedError("This is an abstract class, please use a subclass")
    
    def forecast_demands(self):
        """Forecast the :attr: `demands`. The forecasting method depends on the subclass.

        :returns: forecasted demands"""
        raise NotImplementedError("This is an abstract class, please use a subclass")
    
    
    def update_if_needed(self):
        """Update the forecasts, if `env.now` is more than `forecast_update_interval` seconds ahead from last demand measurement"""

        now = datetime.utcfromtimestamp(self.env.now).replace(tzinfo=utc)
        delta = (now - self.time_series_end).total_seconds()
        if delta > self.forecast_update_interval:
            self.forecasted_demands = self.forecast_demands()
            self.time_series_end = datetime.utcfromtimestamp(self.env.now).replace(tzinfo=utc)

    @classmethod
    def make_hourly(cls, data, samples_per_hour):
        """ aggregates data series to 1hourly data.

        :param list data: the series
        :param int samples_per_hour: number of samples per hour contained in `data`

        :returns: list of 1hourly data
        """
        def avg(hour):
            sum = 0
            for i in range(samples_per_hour):
                sum += data[hour * samples_per_hour + i]
            return sum / samples_per_hour

        hours = len(data) / samples_per_hour
        return [avg(i) for i in range(hours)]



    @classmethod
    def MASE(cls, training_series, testing_series, prediction_series):
        """
        Computes the MEAN-ABSOLUTE SCALED ERROR forecast error for univariate time series prediction.
        
        See `"Another look at measures of forecast accuracy" <http://robjhyndman.com/papers/another-look-at-measures-of-forecast-accuracy/>`_, Rob J Hyndman
        
        
        :param list   training_series: the series used to train the model
        :param list   testing_series: the test series to predict
        :param list   prediction_series: the prediction of testing_series (same size as testing_series)
        """
        training_series = np.array(training_series)
        testing_series = np.array(testing_series)
        prediction_series = np.array(prediction_series)
        n = training_series.shape[0]
        d = np.abs(np.diff(training_series)).sum() / (n - 1)

        errors = np.abs(testing_series - prediction_series)
        return errors.mean() / d


class DSHWForecast(StatisticalForecast):
    """ This forecast uses the double seasonal exponential smoothing method. It often delivers better results 
    than the :class: `DayTypeForecast`. """
    
    def forecast_at(self, timestamp):
        date = datetime.utcfromtimestamp(timestamp).replace(tzinfo=utc)
        delta = (date - self.time_series_end).total_seconds()
        #print int(delta / 3600 * self.samples_per_hour)
        return [self.forecasted_demands[int(delta / 3600 * self.samples_per_hour)]]
    
    def process_inputdata(self, data, samples_per_hour,start):
        return [data]
    
    def forecast_demands(self,verbose=False):
        print "forecasting demands with double seasonal HW.."
        cached = StatisticalForecast.read_from_cache(self)
        if cached != None:
            return cached
        demand = self.demands[0] #dshw demands only contains one dataset
        sph = self.samples_per_hour
        fc = self.output_weeks * 24 * 7 * self.samples_per_hour #forecast_length
        if None not in self.hw_parameters:
            (alpha, beta, gamma, delta, autocorr) = self.hw_parameters
        else:
            (alpha, beta, gamma, delta, autocorr) = (None for i in range(5))
            
        forecast_values, (alpha, beta, gamma, delta, autocorrelation),in_sample = double_seasonal(demand, m=24*sph, m2=24*7*sph,
                                                                           forecast=fc, alpha=alpha, beta=beta, gamma=gamma, delta=delta,
                                                                            autocorrelation=autocorr)
        
        calculated_parameters = {
            "alpha": alpha, "beta": beta, "gamma": gamma, "delta":delta, 
            "autocorrelation":autocorrelation, "mse": in_sample}
        if verbose:
            print "use auto HW ",calculated_parameters
        
        print "forecasting completed"
        
        return forecast_values
    
    def append_values(self, data, start_date=None):
        demand = self.demands[0]
        demand += data
        
        if len(demand) > self.input_hours:
            #only keep number of input_weeks
            start_index = len(demand) - self.input_hours
            self.demands[0] = demand[start_index:]
        
        self.update_if_needed()




class DayTypeForecast(StatisticalForecast):
    """This forecast splits the demands into 7 weekdays and minimizes and forecasts each with the
    holt-winters multiplicative method."""
    
    @classmethod
    def split_weekdata(cls, data, samples_per_hour, start_date=None):
        if start_date != None:
            weekday = start_date.weekday()
        else:
            weekday = 0
        split_array = [[] for i in range(7)]
        for index, element in enumerate(data):
            if index % (24 * samples_per_hour) == 0:
                weekday = (weekday + 1) % 7
            split_array[weekday].append(element)
        return split_array
        
    def process_inputdata(self, data, samples_per_hour,start):
        return DayTypeForecast.split_weekdata(data, samples_per_hour, start)
  
    def forecast_multiplicative(self, demand, index, result_dict, verbose=False):
        #seasonality length -- one day
        m = 24 * self.samples_per_hour
        fc = self.output_weeks * 24 * self.samples_per_hour #forecast_length
        # alpha, beta, gamma. if any is None, holt.winters determines them automatically
        # cost-expensive, so only do this once..
        (alpha, beta, gamma) = self.hw_parameters
        print "find holt winter parameters for day: ", index

        # find values automatically
        forecast_values, (alpha, beta, gamma),in_sample = multiplicative(demand, m, fc, optimization_type="MSE")
        

        calculated_parameters = {
            "alpha": alpha, "beta": beta, "gamma": gamma, "mse": in_sample}
        if verbose:
            print "use auto HW ",calculated_parameters
            
        result_dict[index] = (forecast_values, calculated_parameters, index)
        
 
    
    
    def forecast_demands(self):
        cached = StatisticalForecast.read_from_cache(self)
        if cached != None:
            return cached
        
        split_results = [[] for i in range(7)]
        #multi processed forecasting
        ## WARNING: hangups:
        #v.1 :  pool.map
        #v.2  use multiple processes instead of pool.map to circumvent a hangup caused
        # by a multiprocessing/django incompabatility
        #share results in a multiaccess queue
        #note: this queue can not hold unlimited elements and will hang up with no warning if there are too many elements
        #12 weeks 1hourly will work, 20 not
        #result_queue = multiprocessing.Queue()
        #v.3 now uses a shared multiprocessing dict, to circumvent hang up problems with queue on windows
        
        mgr = multiprocessing.Manager()
        dict_threadsafe = mgr.dict()
        print "forecasting demands with daytype strategy.."

        #call class as Functor because class methods are not pickeable
        jobs = [Process(target=self, args=(demand,index,dict_threadsafe)) for index, demand in enumerate(self.demands)]
        for job in jobs: job.start()
        for job in jobs: job.join()
         
        for index in dict_threadsafe.keys():
            split_results[index] = dict_threadsafe[index]
            
        forecasted_demands = []
        self.calculated_parameters = []
        for fc_tuple in split_results:
            forecasted_demands.append(list(fc_tuple[0]))
            self.calculated_parameters.append(fc_tuple[1])
            
        pickle.dump( {"forecasts" :forecasted_demands, "parameters" : self.calculated_parameters, "date": self.env.now },
                      open(os.path.join(BASE_DIR,"cache/cached_forecasts.cache"), "wb" ) ) 
        print "forecasting completed"

        return forecasted_demands
    
    
    def forecast_at(self, timestamp):
        date = datetime.utcfromtimestamp(timestamp).replace(tzinfo=utc)
        delta = (date - self.time_series_end).total_seconds()
        arr_index = int((delta / (60.0 * 60.0)) * self.samples_per_hour)
        week_index = int(arr_index / (7 * 24))
        hour_index = arr_index % 24
        #print "yes"
        return (self.forecasted_demands[date.weekday()][week_index * 24 + hour_index], week_index, hour_index)
    
    
    def append_values(self, data, start_date=None):
        new_demands = DayTypeForecast.split_weekdata(data, self.samples_per_hour, start_date)
        
        for index, demand in enumerate(new_demands):
            self.demands[index] += demand
            
            if len(self.demands[index]) > self.input_hours / 7:
                #only keep number of input_weeks
                start_index = len(self.demands[index]) - self.input_hours / 7
                self.demands[index] = self.demands[index][start_index:]
        self.update_if_needed()
    
    
    # callable class
    def __call__(self, demand, index, result_dict):
        self.forecast_multiplicative(demand, index, result_dict)