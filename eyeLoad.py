import numpy
from numpy import *

from pylab import *

class EyeData:
    """
    Implements an object to analyze eye tracking data.

    Example:

    """

    def __init__(self):
        self.outfile = None
        self.verbose = verbose
        self.gazeHist = ones((3,5), Float)*-1

    def getCurGazeSmooth(self,x,y,pw,ph,quality,minSaccadeDistSq=64):
       """gets a dampened version of the current gaze position."""
       """Dampening is achieved by taking a running average of the last 3 gaze readings."""
       """However, if the current gaze is more than minSaccadeDist from the mean of the """
       """last 3 and the quality is good, then the gaze history is reset and the actual current gaze is returned."""
       minQual = 0.1
       saccadeQual = 0.25
       keep = self.gazeHist[:,2]!=-1
       if(quality>=minQual or sum(keep)==0):
          if(sum(keep)>0):
             (mx,my,mpw,mph,mqual) = sum(self.gazeHist[keep])/sum(keep)
             dSq = (mx-x)*(mx-x) + (my-y)*(my-y)
             if(dSq>minSaccadeDistSq and quality>saccadeQuality):
                # Reset the gaze history
                self.gazeHist[:,4] = -1
             else:
                self.gazeHist[2,:] = self.gazeHist[1,:]
                self.gazeHist[1,:] = self.gazeHist[0,:]
          self.gazeHist[0,:] = array((x,y,pw,ph,quality))
          keep = self.gazeHist[:,4]!=-1
       (mx,my,mpw,mph,mqual) = sum(self.gazeHist[keep])/sum(keep)
       # If conf is below this threshold, then we are just returning old values
       # from the stored history, so we should set the returned conf to zero.
       if(quality<minQual):
          mqual = 0
       return(mx,my,mpw,mph,mqual)



      gazePosMean = sum(gazePos,2)/shape(gazePos)[2]
      # compute the affine transform that best fits the measured points
      # This xform matrix will convert homogeneous raw gaze values to
      # screen position coords. Eg. screenCoords = rawGazeVals * gazeToScreen
      gazeToScreen = dot(la.generalized_inverse(gazePosMean), posList)
      print "gazeToScreen xform:", gazeToScreen
      print "predicted screen positions:", dot(gazePosMean,gazeToScreen)

