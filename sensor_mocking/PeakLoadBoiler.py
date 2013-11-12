import Device
from Device import Sensor


class PlBoiler(Device.Device):
	
	def __init__(self,device_id):
 		Device.Device.__init__(self,device_id)

 		#faster timestep, PLBoiler changes its temperature faster than BHKW
 		self.timestep = 0.01

		self.name = "PeakloadBoiler"
		self.currentWorkload 	= Sensor(name="workload",id=0,value=0,unit=r"%")
		self.currentTemperature = Sensor(name="Temperature",id=1,value=0,unit="Celsius")
		self.sensors = [self.currentWorkload,self.currentTemperature]



	def mainloop(self):
		pass


