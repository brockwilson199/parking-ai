# backsub_w_contour.py
from logging import captureWarnings
from operator import xor
import cv2 
import os
from cv2 import threshold
import scipy.ndimage as sp
import pdb
import numpy as np 
import tkinter as tk
import math
import key_log
import record


'''
    Document conventions:
    - A variable that contains this in its name: "frame" suggests that it contains the best visualization for output.
    This means it will always include the original input image and apply some visualization to it.
    
'''


# FILEPATHS 
main_path = os.path.dirname(os.path.abspath(__file__)) 

save_folder = "Inflow_Results"
save_path = os.path.join(main_path, save_folder)

datapath = os.path.join(main_path, "Data", "Inflow")

car_path = os.path.join(datapath, "Car")
combo_path = os.path.join(datapath, "Combo")
not_car_path = os.path.join(datapath, "Not_Car")

# addr = os.path.join(car_path, "car1.mp4")
# addr = os.path.join(combo_path, "combo5.mp4")
# addr = os.path.join(not_car_path, "not_car10.mp4")


addr = os.path.join(car_path, "car8.mp4")
# addr = os.path.join(combo_path, "combo1.mp4")
# addr = os.path.join(not_car_path, "not_car10.mp4")


# PARAMETERS
VAR_THRESHOLD = 200 # BACKGROUND SUB PARAMETER

CONTOUR_THRESHOLD = 7000 # COUNTOR THRESHOLD FOR CONTOUR AREA


# KANADE PARAMETERS
# params for corner detection
feature_params = dict( maxCorners = 50,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )
  
# Parameters for lucas kanade optical flow
lk_params = dict( winSize = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                              10, 0.03))
  
# Create some random colors
color = np.random.randint(0, 255, (100, 3))

# Get screen resolution
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
def main():
    # Create key_log object to control what video is processed
    print("Controls: ")
    print("  s: Start/Stop")
    print("  r: Record Start/Pause")
    # print("  a: Previous")
    # print("  d: Next")
    logger = key_log.log(['s', 'r', 'q'])
    logger.start()

    # Get Video from mp4 source
    cap = cv2.VideoCapture(addr)

    frames = []
    recording = False

    # Get R.O.I. tool
    background_object = cv2.createBackgroundSubtractorMOG2(varThreshold=VAR_THRESHOLD, detectShadows=False) 
    
    try:
        
        while True:
            
            display_frames = []

            '''Extract image from input mp4 video file'''
            ret, frame = cap.read()
            if not ret: break
            display_frames.append(frame) 

            '''Background subtraction to detect motion'''
            # Get binary mask of movement
            backsub_mask, backsub_frame = back_sub(frame, background_object)
            display_frames.append(backsub_frame) 


            '''Contour Detection with threshold to find reigons of interest'''
            # Get an enhanced mask by thresholding reigons of interest by sizes of white pixel areas
            contour_crop, contour_frame = contour_detection(frame, backsub_mask)
            display_frames.append(contour_frame) 

            contour_crop2, contour_frame2 = contour_approx(frame, backsub_mask)
            display_frames.append(contour_frame2) 

            contour_crop3, contour_frame3 = contour_hull(frame, backsub_mask)
            display_frames.append(contour_frame3) 


            # R, G, B = cv2.split(frame)

            # output1_R = cv2.equalizeHist(R)
            # output1_G = cv2.equalizeHist(G)
            # output1_B = cv2.equalizeHist(B)

            # equ = cv2.merge((output1_R, output1_G, output1_B))
            equ = cv2.normalize(frame, frame, 0, 255, cv2.NORM_MINMAX)

            backsub_mask2, backsub_frame2 = back_sub(equ, background_object)
            display_frames.append(backsub_mask2) 


            contour_crop4, contour_frame4 = contour_hull(equ, backsub_mask2)
            display_frames.append(contour_frame4) 


            # '''Feature Detection with Kernel Convolution'''
            # # Get array of points where Kernel Convolution was most effective
            # features, features_frame = feature_detection(frame, contour_crop)
            # display_frames.append(features_frame) 


            # '''Feature Segmentation using Clustering'''
            # # Segment the features into clusters to best imply the existence of individual vehicles
            # clusters, clustering_frame = clustering(frame, features)
            # display_frames.append(clustering_frame) 


            # '''Feature Motion using Optic Flow'''
            # # Track the motion of each feature
            # feature_motions, feature_motions_frame = track_features(frame, clusters)
            # display_frames.append(feature_motions_frame) 
            # # Track the motion of each cluster (cluster motion found using the average of each features' motion in a given cluster)
            # cluster_motions, cluster_motions_frame = track_clusters(frame, feature_motions)
            # display_frames.append(cluster_motions_frame) 



            ''' IMPLEMENTATION THOUGHTS AND IDEAS:
                - If a feature has motion that deviates from it's cluster too much, it should be discarded as a feature worth tracking
                
            '''
            
            
            # display_frames = np.asarray([frame, cv2.cvtColor(backsub_mask, cv2.COLOR_GRAY2BGR), contour_frame3, equ, cv2.cvtColor(backsub_mask2, cv2.COLOR_GRAY2BGR), contour_frame4])#equ,  cv2.cvtColor(backsub_mask2, cv2.COLOR_GRAY2BGR), contour_frame4])
            cmask = contour_mask(np.array(contour_frame4), (0,255,0))
            
            _, cmask = contour_hull(frame, cv2.cvtColor(cmask, cv2.COLOR_RGB2GRAY))
            # pdb.set_trace()
            cmask = contour_mask(cmask, (255,255,255))

            foregound = cv2.bitwise_and(frame, frame, mask=cv2.cvtColor(cmask, cv2.COLOR_RGB2GRAY))
            
            # pdb.set_trace()
            display_frames = np.asarray([equ, cv2.cvtColor(backsub_mask2, cv2.COLOR_GRAY2BGR), contour_frame4, foregound ])#equ,  cv2.cvtColor(backsub_mask2, cv2.COLOR_GRAY2BGR), contour_frame4])

            '''Display output in a practical way'''
            # USE THIS VARIABLE TO WRAP THE WINDOW
            max_h_frames = 3
            # Format the output
            window = format_window(display_frames, max_h_frames, screen_width*.75)
            
            # Show image
            cv2.imshow("", window)
            cv2.waitKey(50)
            
            # Check if we should still be recording (and other controls)
            recording = check_log(logger, recording)

            if recording == True:
                record.start_recording(window, frames)
            
        logger.stop()
    except Exception as e:
        logger.stop()
        raise
    

    if frames != []:
        record.save_recording(frames, save_path, "inflow_results")
    
    cv2.destroyAllWindows() 
    cap.release()


'''This method applies Background Subtraction 
PARAMETERS: 
- frame: frame from video
- background_object: filter to apply to frame from background subtraction''' 
def back_sub(frame, background_object):
    fgmask = frame

    # fgmask = apply_pyramids(fgmask, 1)
    
    fgmask = background_object.apply(fgmask) # apply background subtraction to frame 
    _, fgmask = cv2.threshold(fgmask, 150, 255, cv2.THRESH_BINARY) # remove the gray pixels which represent shadows
    # fgmask = cv2.erode(fgmask, kernel=(15,15), iterations = 5)

    fgmask = cv2.dilate(fgmask, kernel=(25,25), iterations=5) # dilate
    foregound = cv2.bitwise_and(frame, frame, mask=fgmask) # show frame in areas in motion

    return fgmask, foregound


    # OTHER METHODS
    # sp.gaussian_filter(frame, sigma = 4) # blur
    # cv2.erode(fgmask, kernel=(10,10), iterations=2) # erode
    # _, fgmask = cv2.threshold(fgmask, 150, 255, cv2.THRESH_BINARY) # apply threshold
    # fgmask = cv2.dilate(fgmask, kernel=None, iterations=30) # dilate


'''This method reduces noise by applying gaussian pyramids. Pyramid up and pyramid down applied equally
PARAMETERS:
frame - original image to apply pyramids to
iterations - number of times pyrUp and pyrDown should occur each
'''
def apply_pyramids(frame, iterations):

    pyrFrame = frame
    
    for j in range(iterations):
        pyrFrame = cv2.pyrDown(pyrFrame)

    for i in range(iterations):
        pyrFrame = cv2.pyrUp(pyrFrame)
     
    return pyrFrame
    
 
'''This method draws the rectangles around areas of detected motion
PARAMETERS: 
- frame: frame from the video
- fgmask: foreground mask to show which areas motion was detected '''
def contour_detection(frame, fgmask):

    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # find contours
    contour_frame = frame.copy()

    for i in range(len(contours)): # for each contour found 
        if cv2.contourArea(contours[i]) > CONTOUR_THRESHOLD: # if the countour area is above a # 

            cv2.drawContours(contour_frame, contours, i, (0,255,0), 3)

            # # draw a rectangle 
            # x, y, width, height = cv2.boundingRect(contours[i])
            # cv2.rectangle(contour_frame, (x,y - 10), (x + width, y + height), (0,0,255), 2)
            # cv2.putText(contour_frame, "car detected", (x,y), cv2.FONT_HERSHEY_COMPLEX, 0.3, (0, 255, 0), 1, cv2.LINE_AA)

    return None, contour_frame 

def contour_approx(frame, fgmask):
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # find contours
    contour_frame = frame.copy()

    for c in contours:
        if cv2.contourArea(c) > CONTOUR_THRESHOLD:
            epsilon = 0.01*cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            cv2.drawContours(contour_frame, [approx], 0, (0, 255, 0), 3)
    return None, contour_frame
def contour_hull(frame, fgmask):
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # find contours
    contour_frame = frame.copy()

    count = 0
    for c in contours:
        if cv2.contourArea(c) > CONTOUR_THRESHOLD:
            hull = cv2.convexHull(c)
            count += 1
            # saves.append(hull)
            cv2.drawContours(contour_frame, [hull], -1, (0, 255, 0), thickness=cv2.FILLED)
    
    return None, contour_frame

def contour_mask(contour, color):
    
    r1, g1, b1 = color # Original value
    r2, g2, b2 = 0, 0, 0 # Value that we want to replace it with

    red, green, blue = contour[:,:,0], contour[:,:,1], contour[:,:,2]
    bleh = ~ ((red == r1) | (green == g1) | (blue == b1))
    contour[:,:,:3][bleh] = [r2, g2, b2]
    # contour = contour.astype('uint8')

    temp = cv2.cvtColor(contour, cv2.COLOR_RGB2GRAY)
    _, fgmask = cv2.threshold(temp, 1, 255, cv2.THRESH_BINARY)
    
    
    fgmask = cv2.cvtColor(fgmask, cv2.COLOR_GRAY2RGB)
    return fgmask
    
def feature_detection(initial_frame, frame):
    return None, None

def clustering(initial_frame, frame):
    return None, None

def track_features(initial_frame, frame):
    return None, None

def track_clusters(initial_frame, frame):
    return None, None


'''This method is used to format the final output window
PARAMETERS: 
- frames: a list of all the frames which are to be displayed
- max_h_frames: maximum horizontal frames to be displayed
- mad_width: maximum desired pixel width for the output window '''
def format_window(frames, max_h_frames, max_width):

    filler = np.zeros(np.asarray(frames[0]).shape,dtype=np.uint8 )
    
    single_frame_ratio = frames[0].shape[0]/frames[0].shape[1]

    frame_count = len(frames)
    
    filler_count = 0
    if frame_count%max_h_frames != 0:
        filler_count = max_h_frames - (frame_count%max_h_frames)
        
        frames = np.hstack(frames)
        for i in range(filler_count):
            frames = np.hstack([frames, filler])
    else:
        frames = np.hstack(frames)

    #pdb.set_trace()
    frames = np.hsplit(frames, filler_count+frame_count)
    hframeslist = []
    
    for i in range(0, len(frames), max_h_frames):
        hframeslist.append(np.hstack(frames[i:i+max_h_frames]))
        
    window = np.vstack(hframeslist[:])

    ratio = window.shape[0]/window.shape[1]
    
    window = cv2.resize(window, dsize=(math.floor( max_width ), math.floor( max_width*ratio )) )
    
    return window
        

'''This method acts as a controller to manipulate the video feed
PARAMETERS: 
- logger: log object from key_log.py '''
def check_log(logger, recording):
    
    if logger.keys_clicked:
        key = logger.keys_clicked[-1]
        
        if key in logger.valid_keys:
            
            if key == 's':
                logger.keys_clicked.append(None)
                key = logger.keys_clicked[-1]
                while 's' != key:
                    key = logger.keys_clicked[-1]
                    
                    cv2.waitKey(50)
                logger.keys_clicked.append(None)
            elif key == 'r':
                recording = not recording
                cv2.waitKey(50)
                logger.keys_clicked.append(None)
            elif key == 'q':
                recording = not recording
                cv2.waitKey(50)
                logger.keys_clicked.append(None)
                raise

            else:
                print("The key {" + key + "} has not been set up. Set up this key in 'check_log'")
    return recording




if __name__ == "__main__":
    main()