import numpy as np
import matplotlib.pyplot as plt

###
## Simple 2d histogram because np.histogram is goddawful slow

class hist2d(object):

    def __init__(self, xbins, nbinsy, ylow,yhigh):

        self.xbins = np.array(xbins)

        ywidth = (yhigh-ylow)/nbinsy
        self.ybins = np.linspace(ylow,yhigh,nbinsy+1)
#        print ("h2 edges x = ",self.xbins," y = ", self.ybins)

        self.histys = []
        for xbin in xbins:
            hhy,edgesy = np.histogram([], bins=self.ybins)
            self.histys.append(hhy.astype(float))

        self.centersx = 0.5*(self.xbins[:-1] + self.xbins[1:])
        self.centersy = 0.5*(self.ybins[:-1] + self.ybins[1:])
#        print (" centers =  x= ", self.centersx, " y = ", self.centersy)

    def fill(self, arr,weight=1.0):
        xbin = np.where(self.xbins > arr[0])[0][0] - 1
        histy,edges = np.histogram([arr[1]], bins=self.ybins, weights = [weight])
        
        self.histys[xbin] += histy


def test():

    h2 = hist2d(5, 0, 1,10,0,10)
    for _ in range(1000):
        e = np.random.random()
        h = int(np.random.uniform(0,10))
        h2.fill([e,h])

    e_centers = h2.centersy
    for i in range(5):
        y_data = h2.histys[i]
        print (" i = ",i," center = ",e_centers[i], " data = ", y_data," sum = ",y_data.sum(), " cum sum = ",np.cumsum(y_data))
        eff = 1.0 - (np.cumsum(y_data)[5]/y_data.sum())
        print (" eff = ",eff)



#test()
