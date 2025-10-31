import numpy as np
import matplotlib.pyplot as plt

###
## Simple 1d histogram because np.histogram is goddawful slow

class hist1d(object):

    def __init__(self, nbins, xlow, xhigh):

        width = (xhigh-xlow)/nbins
        self.bins = np.linspace(xlow-width,xhigh+width,nbins+3) #  +1 for under/overflow, +1 becauase N bins need N+1 edges

        hh,edges = np.histogram([], bins=self.bins)
        self.hist= hh.astype(float)
        self.centers = (self.bins[:-1] + self.bins[1:]) / 2
        print (" === histogram from ", xlow, xhigh, " nbins= ",nbins)
        print (" bin edges = ",self.bins)
        print (" bin centers = ", self.centers)

    def fill(self, arr,weight=1.0):
        hist,edges = np.histogram(arr, bins=self.bins, weights = weight*np.ones(shape=arr.shape))
        self.hist += hist

    def draw(self,**kwargs):
        plt.step(self.bins[:-1],self.hist,where='post',**kwargs)

    def draw_cumsum(self,**kwargs):
        plt.step(self.bins[:-1],np.cumsum(self.hist[::-1])[::-1],where='post',**kwargs)

    def mean(self):
        return np.sum(self.centers*self.hist)/np.sum(self.hist)
        
    def quantile(self, val):
        cdf = np.cumsum ( self.hist/(np.sum(self.hist)) )
        return cdf[np.where(self.centers > val)[0][0]]

    @property
    def data(self):
        return self.bins, self.hist


def test():

    h = hist1d(10, -0.5, 9.5)
    for _ in range(1000):
        a = np.random.random((3,))*9.0
        h.fill(a)

    h.draw(color='red')
    plt.savefig("testhist.pdf")


#test()
