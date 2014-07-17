import numpy as np
from server.forecasting.tools.plotting import show_plotting
from server.forecasting.forecasting.dataloader import DataLoader
from server.forecasting.forecasting.holt_winters import double_seasonal
from server.forecasting.forecasting.helpers import approximate_index
import calendar
from server.forecasting.forecasting import Forecast
from server.settings import BASE_DIR
import os

from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt


def MSE(input, forecast):
    rmse = sqrt(sum([(m - n) ** 2 for m, n in zip(input, forecast[:-1])]) / len(input))
    #penalty = mean_below_penalty(np.array(forecast[:-1]))
    
    return rmse# + penalty

def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta
        
        
def make_hourly(data, samples_per_hour):
    def avg(hour):
        sum = 0
        for i in range(samples_per_hour):
            sum += data[hour * samples_per_hour + i]
        return sum / samples_per_hour

    hours = len(data) / samples_per_hour
    return [avg(i) for i in range(hours)]

def plot_dataset(sensordata,forecast_start=0,block=True):
    fig, ax = plt.subplots()
    start = datetime(year=2014,month=1,day=1)
    dates = [date for date in perdelta(start,start+timedelta(hours=len(sensordata["measured"])), timedelta(hours=1)) ]
    forecast_plot, = ax.plot(dates[forecast_start:], sensordata["forecasting"], label="forecasting", linewidth=1.5) #range(forecast_start,len(sensordata["forecasting"])+forecast_start)
    sim_plot, = ax.plot(dates, sensordata["measured"], label="measured", linewidth=1.5)
    
    show_plotting(plt, ax, block)
    
    
    return (fig, sim_plot,forecast_plot)


""" a tool for finding the right alpha, beta and gamma parameter for holt winters"""
def value_changer():
    try:
        from matplotlib.widgets import Slider, Button, RadioButtons
        
        from pylab import axes
    except:
        print "ljdlj"
    sep = os.path.sep
    path = os.path.join(BASE_DIR, "server" + sep + "forecasting" + sep + "systems" + sep + "data" + sep + "Electricity_1.1-12.6.2014.csv")
    raw_data = DataLoader.load_from_file(path, "Strom - Verbrauchertotal (Aktuell)",delim="\t")
    ind = len(raw_data) / 2
    kW_data = Forecast.make_hourly([float(val) / 1000.0 for val in raw_data],6) #cast to float and convert to kW
    dates = [int(d) for d in DataLoader.load_from_file(path, "Datum", "\t")]
    input = make_hourly(kW_data,6)[-24*7:]
    start = calendar.timegm(datetime(year=2014,month=1,day=2).timetuple())
    start_index = approximate_index(dates, start)
    train_len= 24*7*8
    trainingdata = kW_data[start_index:start_index+train_len]
    test_start = start_index+train_len 
    testdata = kW_data[test_start:test_start+7*24*2]
    start_forecast = test_start*3600
    end_forecast = start_forecast + len(testdata) * 3600
      

    alpha = 0.0000001
    beta = 0.0
    gamma = 0.05
    delta = 0.01
    #plot_dataset(values)
    m = 24
    m2 = 24 * 7
    #forecast length
    fc = int(len(testdata))
    forecast_values, (alpha, beta, gamma,delta),insample = double_seasonal(trainingdata, m,m2,fc, alpha, beta, gamma,delta)
    print forecast_values
    values ={ 'forecasting':forecast_values, 'measured':testdata}
    
    (fig, sim_plot,forecast_plot) = plot_dataset(values, 0,block=False)
    
    axcolor = 'lightgoldenrodyellow'
    axalpa = axes([0.25, 0.02, 0.65, 0.02], axisbg=axcolor)
    axbeta  = axes([0.25, 0.05, 0.65, 0.02], axisbg=axcolor)
    axgamma  = axes([0.25, 0.08, 0.65, 0.02], axisbg=axcolor)
    axdelta  = axes([0.25, 0.11, 0.65, 0.02], axisbg=axcolor)
    
    alpha_slider = Slider(axalpa, 'Alpha', 0.0, 1.0, valinit=alpha)
    beta_slider = Slider(axbeta, 'Beta', 0.0, 1.0, valinit=beta)
    gamma_slider = Slider(axgamma, 'Gamma', 0.0, 1.0, valinit=gamma)
    delta_slider = Slider(axdelta, 'Delta', 0.0, 1.0, valinit=delta)
    
    def update_hw(val):
        alpha = alpha_slider.val
        beta = beta_slider.val
        gamma = gamma_slider.val
        delta = delta_slider.val
        
        
        forecast_values, (alpha, beta, gamma,delta),insample = double_seasonal(trainingdata, m,m2,fc, alpha, beta, gamma,delta)
        values ={ 'forecasting':forecast_values, 'measured':testdata}
        
        forecast_plot.set_ydata(forecast_values)
        sim_plot.set_ydata(testdata)
        fig.canvas.draw_idle()
        
        print alpha, beta, gamma, MSE(testdata, forecast_values)
        
        
    alpha_slider.on_changed(update_hw)
    beta_slider.on_changed(update_hw)
    gamma_slider.on_changed(update_hw)
    delta_slider.on_changed(update_hw)
    
    plt.show()