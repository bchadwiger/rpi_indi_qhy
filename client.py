"""
Implements a simple PyIndi Client.

This code is based on the INDI tutorial at
https://www.indilib.org/developers/dev-howtos/151-time-lapse-astrophotography-with-indi-python.html
"""

from astropy.io import fits
import numpy as np
import cv2
import os
import io
import sys, time, logging
import argparse
import datetime
import PyIndi
import warnings


class IndiClient(PyIndi.BaseClient):
 
    device = None
 
    def __init__(self, exposure, x0, y0, width, height, raw, override):
        super(IndiClient, self).__init__()
        self.logger = logging.getLogger('PyQtIndi.IndiClient')
        self.logger.info('creating an instance of PyQtIndi.IndiClient')
        self.timer = None
        self.exposure = exposure
        if x0 % 2 != 0:
            warnings.warn(f'Left-most pixel (x0 = {x0}) is not divisible by 2! This can cause problems during debayering')
        if y0 % 2 != 0:
            warnings.warn(f'Top-most pixel (y0 = {y0}) is not divisible by 2! This can cause problems during debayering')

        self.x0 = x0
        self.y0 = y0
        self.width = width
        self.height = height
        self.raw = raw
        self.override = override

    # called when a new device is detected
    def newDevice(self, d):
        self.logger.info("new device " + d.getDeviceName())
        if d.getDeviceName() == "CCD Simulator":
            self.logger.info("Set new device CCD Simulator!")
            # save reference to the device in member variable
            self.device = d
        elif d.getDeviceName() == "QHY CCD QHY5III485C-792":
            self.logger.info("Set new device QHY5III485")
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
        if p.getName() == "CCD_FRAME":
            self.setFrame()
        if p.getName() == "CCD_TEMPERATURE":
            print(f"Chip temperature: {self.device.getNumber('CCD_TEMPERATURE')}")
 
    def setFrame(self):
        print('Set new frame parameters')
        frame = self.device.getNumber('CCD_FRAME')
        for i in range(len(frame)):
            print(frame[i].value)
        # set frame properties
        frame[0].value = self.x0      # X0
        frame[1].value = self.y0      # Y0
        frame[2].value = self.width   # WIDTH
        frame[3].value = self.height  # HEIGHT
        self.sendNewNumber(frame)

    def removeProperty(self, p):
        self.logger.info("remove property " + p.getName() + " for device " + p.getDeviceName())

    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        blobdata = bp.getblobdata()
        blobfile = io.BytesIO(blobdata)

        if self.override:
            out_basename = 'frame'
        else:
            out_basename = f"frame_{self.timer}_exp_{self.exposure}s"

        if self.raw:
            out_filename = out_basename + '.fit'
            with open(out_filename, 'wb') as f:
                f.write(blobfile.getvalue())
        else:
            out_filename = out_basename + '.png'
            print("\n\n\nBEFORE\n\n\n")
            img_fits = fits.getdata(blobfile) * ((2**8 - 1) / (2**16 - 1))
            print("\n\n\nAFTER\n\n\n")
            img_fits = img_fits.astype('uint8')

            # RGGB (used by QHY5III485) corresponds to OpenCV BR Bayer pattern,
            # see https://docs.opencv.org/3.4/de/d25/imgproc_color_conversions.html
            imgBGR = cv2.cvtColor(img_fits, cv2.COLOR_BAYER_BG2BGR)
            cv2.imwrite(out_filename, imgBGR)

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

        # TODO: adapt exposure based on stats of previous image(s)
        self.logger.info(">>>>>>>>")
        
        #get current exposure time
        exp = self.device.getNumber("CCD_EXPOSURE")
        # set exposure time in seconds
        exp[0].value = self.exposure
        # send new exposure time to server/device
        now = datetime.datetime.now()
        self.timer = f"{now.year}{now.month:02}{now.day:02}_{now.hour:02}{now.minute:02}{now.second:02}.{int(now.microsecond/1000):03}"
        self.sendNewNumber(exp)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                      prog='Client.py',
                      description='Cyclicly records images with given parameters')
    parser.add_argument('exposure', type=float, help='Exposure in seconds')
    parser.add_argument('-x0', type=int, default=880, help='Left-most pixel position') # theoretically 842 for center square)
    parser.add_argument('-y0', type=int, default=0, help='Top-most pixel position')
    parser.add_argument('-W', '--width', type=int, default=2180, help='Frame width in pixels')
    parser.add_argument('-H', '--height', type=int, default=2180, help='Frame height in pixels')
    parser.add_argument('-r', '--raw', type=bool, default=False, help='Whether to store raw image (as fits), or debayered image (as png) (default)', action=argparse.BooleanOptionalAction)
    parser.add_argument('-w', '--override', type=bool, default=False, help='Whether to use same filename for each new image (and thus override image with each new exposure). Otherwise, uses a unique filename based on timestamp, etc. (default).', action=argparse.BooleanOptionalAction)
    parser.add_argument('-o', '--output_dir', type=str, default=f'{os.getcwd()}/images', action='store')
    args = parser.parse_args()
    print(f'Using the following parameters: {args}')

    image_dir = args.output_dir
    print(f'Using output directory: {image_dir}')
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    # instantiate the client
    indiclient = IndiClient(args.exposure, args.x0, args.y0, args.width, args.height, args.raw, args.override)
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
