"""
Implements a simple PyIndi Client.

This code is based on the INDI tutorial at
https://www.indilib.org/developers/dev-howtos/151-time-lapse-astrophotography-with-indi-python.html
"""

import sys, time, logging
import datetime
import PyIndi
  
class IndiClient(PyIndi.BaseClient):
 
    device = None
 
    def __init__(self):
        super(IndiClient, self).__init__()
        self.logger = logging.getLogger('PyQtIndi.IndiClient')
        self.logger.info('creating an instance of PyQtIndi.IndiClient')
        self.timer = None
    
    # called when a new device is detected
    def newDevice(self, d):
        self.logger.info("new device " + d.getDeviceName())
        if d.getDeviceName() == "CCD Simulator":
            self.logger.info("Set new device CCD Simulator!")
            # save reference to the device in member variable
            self.device = d
        elif d.getDeviceName() == "QHY CCD QHY5III485C-792":
            self.logger.info("Set new device CCD Simulator!")
            self.device = d
        else:
            raise NotImplementedError(f"Device {d.getDeviceName()} not supported!")
    def newProperty(self, p):
        self.logger.info("new property "+ p.getName() + " for device "+ p.getDeviceName())
        if self.device is not None and p.getName() == "CONNECTION" and p.getDeviceName() == self.device.getDeviceName():
            self.logger.info("Got property CONNECTION for CCD Simulator!")
            # connect to device
            self.connectDevice(self.device.getDeviceName())
            # set BLOB mode to BLOB_ALSO
            self.setBLOBMode(1, self.device.getDeviceName(), None)
        if p.getName() == "CCD_EXPOSURE":
            # take first exposure
            self.takeExposure()

    def removeProperty(self, p):
        self.logger.info("remove property " + p.getName() + " for device " + p.getDeviceName())

    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        img = bp.getblobdata()
        # write image data to BytesIO buffer
        import io
        blobfile = io.BytesIO(img)
        # open a file and save buffer to disk
        with open(f"frame_{self.timer}.fit", "wb") as f:
            f.write(blobfile.getvalue())
        # start new exposure
        self.takeExposure()

    def newSwitch(self, svp):
        self.logger.info ("new Switch " + svp.name + " for device " + svp.device)

    def newNumber(self, nvp):
        self.logger.info("new Number " + nvp.name + " for device " + nvp.device)

    def newText(self, tvp):
        self.logger.info("new Text " + tvp.name + " for device " + tvp.device)

    def newLight(self, lvp):
        self.logger.info("new Light " + lvp.name + " for device " + lvp.device)

    def newMessage(self, d, m):
        #self.logger.info("new Message "+ d.messageQueue(m))
        pass

    def serverConnected(self):
        print("Server connected (" + self.getHost() + ":" + str(self.getPort()) + ")")

    def serverDisconnected(self, code):
        self.logger.info("Server disconnected (exit code = " + str(code) + "," + str(self.getHost()) + ":" + str(self.getPort()) + ")")

    def takeExposure(self):
        self.logger.info(">>>>>>>>")
        #get current exposure time
        exp = self.device.getNumber("CCD_EXPOSURE")
        # set exposure time in seconds
        exp[0].value = 0.01
        # send new exposure time to server/device
        now = datetime.datetime.now()
        self.timer = f"{now.year}{now.month:02}{now.day:02}_{now.hour:02}{now.minute:02}{now.second:02}.{int(now.microsecond/1000):03}"
        self.sendNewNumber(exp)


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
 
# instantiate the client
indiclient = IndiClient()
# set indi server localhost and port 7624
indiclient.setServer("localhost",7624)

# connect to indi server
print("Connecting to indiserver")
if not indiclient.connectServer():
     print("No indiserver running on " + indiclient.getHost() + ":" + str(indiclient.getPort()) + " - Try to run")
     print("  indiserver indi_simulator_telescope indi_simulator_ccd")
     sys.exit(1)
  
# start endless loop, client works asynchron in background
while True:
    time.sleep(1)