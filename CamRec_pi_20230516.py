from picamera2 import Picamera2, Preview
from picamera2.encoders import JpegEncoder, Quality
import time
from picamera2.outputs import CircularOutput
from gpiozero import Button
from gpiozero import LED
from gpiozero import InputDevice
from datetime import datetime
import os
import csv
#Need a method for recording GPIO pins <- this will give us TTL and video trig times independent  if the camera
manSynchButton=Button(8)#change this?
vidTrigButton=Button(7)
Sig=LED(15)
TTL_1=InputDevice(18, pull_up=False)#Frame trigger TTL
TTL_2=InputDevice(23, pull_up=False)#Video trigger TTL
#TTL_out=[]
Sig.off()
picam2=Picamera2()

#Below is going to be repeated often
encoder=JpegEncoder(q=70)
output=CircularOutput(buffersize=4000, pts='TimePointCSV_1.txt')
output.fileoutput='SessionName_1.mjpeg'
encoder.output=output
# config=picam2.create_video_configuration(main={"size": (640,400)}, controls={"FrameDurationLimits": (10,10), "Sharpness": 10.0, "AeEnable": False, "AwbEnable": False, "Brightness": 0.8, "Contrast": 2.5}, buffer_count=15)
# picam2.configure(config)
start_ext_trig_cmd='v4l2-ctl -d /dev/v4l-subdev0 -c trigger_mode=1'
stop_ext_trig_cmd='v4l2-ctl -d /dev/v4l-subdev0 -c trigger_mode=0'
os.system(stop_ext_trig_cmd)
#Above is going to be repeated often

#Below is a list of variables that are going to be changed every session
STRAIN='DYT1'
MOUSE=9999
DATEtime=datetime.now()
cam='cam1'
parent_folder='/home/pi/data'#'/media/pi/T7/'

#Create local directory
mouseID = STRAIN+'_{:04d}'.format(MOUSE)
session_folder_name=os.path.join(parent_folder,mouseID,DATEtime.strftime('%Y%m%d')+'_1')
session_num=1
while os.path.exists(session_folder_name):
        session_num += 1
        session_folder_name=session_folder_name[0:len(session_folder_name)-2]+'_'+str(session_num)
os.makedirs(session_folder_name)


vid_dtstr = DATEtime.strftime('%Y%m%d_%H-%m-%S')    

#Record session video
#NO FRAMERATE! EXTERNAL TRIGGER
Sig.on()
config=picam2.create_video_configuration(main={"size": (640,400)}, controls={"FrameDurationLimits": (10,10), "Sharpness": 10.0, "AeEnable": False, "AwbEnable": False, "Brightness": 0.55, "Contrast": 2.5}, buffer_count=15)
#config=picam2.create_video_configuration(main={"size": (640,400)}, controls={"FrameDurationLimits": (10,10), "Sharpness": 10.0, "AeEnable": False, "AwbEnable": False}, buffer_count=15)

picam2.configure(config)
os.system(start_ext_trig_cmd)#
manSynchButton.wait_for_press()
print("Synch Start")
Sig.off()

ii=1
j=time.time()
#print(j)
while time.time()-j<900:
    with open(session_folder_name+'/TTL_log.csv', 'a') as csvfile:
    #csv.QUOTE_NONNUMERIC()
        logcsv=csv.writer(csvfile, delimiter=',')
        logcsv.writerow([str(time.time_ns()/1000000),str(int(TTL_1.is_active)),str(int(TTL_2.is_active))])
    if vidTrigButton.is_pressed:
        print('PRESSED')
        with open(session_folder_name+'/TTL_log.csv', 'a') as csvfile:
                #csv.QUOTE_NONNUMERIC()
                logcsv=csv.writer(csvfile, delimiter=',')
                logcsv.writerow([str(time.time_ns()/1000000),str(int(TTL_1.is_active)),str(int(TTL_2.is_active))])
        #videoName='_'.join([mouseID, vid_dtstr, cam])+str(ii)+'.mjpeg'
        #videoName='/'.join([session_folder_name, videoName])
        videoName=session_folder_name+'/'+mouseID+'_'+vid_dtstr+'_'+cam+'_'+str(ii)+'.mjpeg'
        timePointName='_'.join([mouseID, vid_dtstr, cam])+'_'+str(ii)+'.txt'
        timePointName='/'.join([session_folder_name, timePointName])
        
        output = CircularOutput(buffersize=4000, pts=timePointName)
        output.fileoutput=videoName
        picam2.start_recording(encoder, output, pts=timePointName, quality=Quality.VERY_LOW);
        #time.sleep(8)
        jj=time.time()
        while time.time()-jj<8:
            #TTL_out.append(int(TTL_1.is_active))
            with open(session_folder_name+'/TTL_log.csv', 'a') as csvfile:
                #csv.QUOTE_NONNUMERIC()
                logcsv=csv.writer(csvfile, delimiter=',')
                logcsv.writerow([str(time.time_ns()/1000000),str(int(TTL_1.is_active)),str(int(TTL_2.is_active))])
        picam2.stop_recording()
        ii+=1

#Record calibration video, No GPIO recording, external trigger off 
calibrationFPS=30
os.system(stop_ext_trig_cmd)#Should be redundant, but just to make sure that the video is free running
calibration_video_name='_'.join([mouseID, vid_dtstr, cam]) + '_calibration.mjpeg'
calibration_video_name='/'.join([session_folder_name, calibration_video_name])
calibration_timestamp_name='_'.join([mouseID, vid_dtstr, cam]) + '_calibration.txt'
calibration_timestamp_name='/'.join([session_folder_name, calibration_timestamp_name])
    
Sig.on()
manSynchButton.wait_for_press()
print('PRESSED')
Sig.off()
fdl = int(1000000 / calibrationFPS)
    #Check below!!!!
video_config =picam2.create_video_configuration(main={"size": (640, 400)}, lores={"size": (320, 200)}, display="lores", controls={"FrameDurationLimits":(fdl, fdl)}, buffer_count=10)
picam2.stop()
picam2.stop_preview()
picam2.configure(video_config)
picam2.start_preview(Preview.QTGL)
encoder2 = JpegEncoder(q=70)#MJPEGEncoder(20000000)#H264Encoder(1000000)#THIS NEEDS EDITED!!!!
picam2.start_recording(encoder2, calibration_video_name, pts=calibration_timestamp_name)
time.sleep(10)
picam2.stop_recording()
picam2.stop_preview()


#CLEANUP -> rename .txt to .csv and convert .mjpeg to .avi
# fldDir=os.listdir(session_folder_name)
# for ii in fldDir:
#     if '.mjpg' in ii:#A conditional that *SHOULD* be unnecessary, but is here in case I misspell '.mjpeg'
#         task_vid_name='/'.join([session_folder_name,ii])
#         os.rename(task_vid_name,task_vid_name[0:len(task_vid_name)-1]+'eg')
#     if '.mjpeg' in ii:
#         task_vid_name='/'.join([session_folder_name,ii])
#         task_vid_avi=ii[0:len(ii)-5]+'avi'
#         task_vid_avi='/'.join([session_folder_name, task_vid_avi])
#         compileFrames='ffmpeg -i '+ task_vid_name + ' -pix_fmt yuv420p -b:v 4000k -c:v libx264 ' + task_vid_avi
#         os.system(compileFrames)
#     if '.txt' in ii:
#         TimeStampName='/'.join([session_folder_name,ii])
#         TimestampCSV = ii[0:len(ii)-3]+'csv'
#         TimestampCSV = '/'.join([session_folder_name,TimestampCSV])
#         os.rename(TimeStampName,TimestampCSV)
