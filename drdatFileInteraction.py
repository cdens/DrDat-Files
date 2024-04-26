#!/usr/bin/env python3
# drdatFileInteraction.py
#
# Python function to save and write data to a simple binary data format
# Casey R. Densmore, 22APR2024

# File type .drdat overview:
# Binary file, little endian, containing any number of variables 
# (can be any number of dimensions)
#
# First byte: Encodes number of bits per datapoint (8-bit number)
# Second byte: Number of dimensions per variable (8-bit number)
# Next nDimensions x 2 bytes: Number of datapoints per dimension (16-bit numbers)
# Next (nDimensions + nVariables) x 4 bytes: Offset and scale values for each variable
#   Both numbers are stored as 16-bit integers (signed)
#   Both numbers (integers) are divided by 200 to give the scale and offset values
#   For each variable: V = scale * Vint + offset = (scaleint * Vint + offset ) / 200
# Dimensional data is stored as 16-bit integers in the following bytes
# Variable data is stored as N-bit integers (based on data in first byte) in the remainder
# of the file

import numpy as np

defaultOptions = {'endian':'little', 'nBits':[16], 'scale':[1], 'offset':[0]}


#options based on defaultOptions struct
#data should be a list of numpy arrays containing data to save to the file
#corresponding options for bit status

def writeDrData(filename, options, data):
    
    byteType = defaultOptions['endian']
    
    with open(filename,'wb') as f:
        
        #write header data, starting with number 69, then number of variables
        f.write((69).to_bytes(1, byteorder=byteType, signed=False))
        f.write(len(data).to_bytes(1, byteorder=byteType, signed=False))
        
        #for each variable
        for (curData, curNbits, scale, offset) in zip(data, defaultOptions['nBits'], defaultOptions['scale'], defaultOptions['offset']):
            
            dataSize = curData.shape
            bitFormat = f'0{curNbits}b'
            dataArray = []
            
            #applying offset, rounding, scaling
            curData = np.round((curData + offset) * scale)
            dataArray = curData.flatten('C') # for i, then for j, then for k, then for l, ... (curData[i][j][k][l])
                                
            nbytes=int(curNbits/8)
            print(f"Writing variable: {nbytes=}, {dataSize=}, {scale=}, {offset=}, npoints={len(dataArray)}")
                            
            #write header data, starting with initial bit with data length (8-bit number- 1 byte)
            f.write(curNbits.to_bytes(1, byteorder=byteType, signed=False))
            
            #write number of dimensions (8-bit number- 1 byte)
            f.write(len(dataSize).to_bytes(1, byteorder=byteType, signed=False))
            
            #write length of each dimension (32-bit numbers, 4 bytes per dimension)
            for dim in dataSize:
                f.write(dim.to_bytes(4, byteorder=byteType, signed=False))
                
            #NOTE: conversion is Dint = (D + scale) * offset, reverse is D = Dint/offset - scale
            #write data scale (32-bit number/4 bytes signed with scale factor of 1E3)
            f.write(int(np.round(scale * 1E3)).to_bytes(4, byteorder=byteType, signed=True))
            
            #write data offset (32 bit number/4 bytes signed with scale factor of  1E3)
            f.write(int(np.round(offset * 1E3)).to_bytes(4, byteorder=byteType, signed=True))
            
            nbytes = int(curNbits / 8) #only supports even byte integers
            
            #constrains the values to range of integers
            minval = 0
            maxval = 2**curNbits - 2
            nanval = maxval + 1
            ge = np.greater_equal(dataArray, maxval) 
            le = np.less_equal(dataArray, minval) 
            isnan = np.isnan(dataArray)
            dataArray[ge] = maxval
            dataArray[le] = minval
            dataArray[isnan] = nanval
            
            for intval in dataArray:
                cbytes = int(intval).to_bytes(nbytes, byteorder=byteType, signed=False)
                f.write(cbytes)
    
        
    
def readDrData(filename, byteType):
    
    #reading in all data
    with open(filename,'rb') as f:
        fileContent = f.read()
    
    data = [] #empty list to be filled with all relevant data    
    
    #unpacking data
    firstNum = int.from_bytes(fileContent[0:1], byteorder=byteType, signed=False)
    numVars = int.from_bytes(fileContent[1:2], byteorder=byteType, signed=False)
    readPoint = 2
        
    if firstNum == 69: #nice (file is hopefully correctly formatted)
        
        for varnum in range(numVars):
    
            #number of bytes per datapoint for current variable
            nbits = int.from_bytes(fileContent[readPoint:readPoint+1], byteorder=byteType, signed=False)
            nbytes = int(nbits / 8) #bytes per var. Currently only supports 8/16 bits per variable
            readPoint += 1
            
            #number of dimensions for current variable
            ndims = int.from_bytes(fileContent[readPoint:readPoint+1], byteorder=byteType, signed=False)
            readPoint += 1
            
            #reading size of variable
            dataSize = []
            for i in range(ndims):
                dataSize.append( int.from_bytes(fileContent[readPoint:readPoint+4], byteorder=byteType, signed=False))
                readPoint += 4
                
            #reading scale and offset
            #NOTE: conversion is Dint = (D + scale) * offset, reverse is D = Dint/offset - scale
            scale = float(int.from_bytes(fileContent[readPoint:readPoint+4], byteorder=byteType, signed=True)) / 1E3
            readPoint += 4
            offset = float(int.from_bytes(fileContent[readPoint:readPoint+4], byteorder=byteType, signed=True)) / 1E3
            readPoint += 4
            
            print(f"Reading variable: {nbytes=}, {dataSize=}, {scale=}, {offset=}")
            
            #reading all data in current variable
            cdata = []
            for i in range(np.prod(dataSize)):
                cdata.append(int.from_bytes(fileContent[readPoint:readPoint+nbytes], byteorder=byteType, signed=False))
                readPoint += nbytes
            
            # reorganizing to proper structure, applying scale and offsets
            cdata = np.reshape(cdata, dataSize, 'C')
            data.append((cdata/scale) - offset)
            
    return data
        
    
    
def runUnitTest():
    
    filename = 'test.drdat'
    
    #create one, two, thee, and four-dimensional variables with random data
    test1D = np.arange(-90, 90, 0.25) #simulate latitude
    test2D = np.random.random((23, 48)) * 16000 #simulate bathymetry (ft)
    test3D = np.random.random((12, 24, 45)) * 40 + 32 #simulate SST (F)
    test4D = np.random.random((5, 7, 4, 8)) #random 4D array
    
    #creating conversion parameters
    #NOTE: conversion is Dint = (D + scale) * offset, reverse is D = Dint/offset - scale
    #NOTE: integer ranges- 255 (8-bit), 65535 (16-bit), 4.29E9 (32-bit), 18.4E18 (64-bit)
    options = defaultOptions
    options["nBits"]  = [16, 16,  8,  8]
    options["scale"]  = [360, 2,  5,200]
    options["offset"] = [90,  0,-30,  0]
    
    #saving data to write
    data_in = [test1D, test2D, test3D, test4D]
    
    #write data to file
    writeDrData(filename, options, data_in)
    
    #read data from file
    data_out = readDrData(filename, options['endian'])
    
    #compare data (set random indices)
    i = 1
    j = 6
    k = 3
    l = 2
    for (din, dout) in zip(data_in, data_out):
        print(f"Variable shape- in: {din.shape}, out: {dout.shape}")
        inshape = din.shape
        if len(inshape) == 1:
            inval = din[i]
            outval = dout[i]
        elif len(inshape) == 2:
            inval = din[i][j]
            outval = dout[i][j]
        elif len(inshape) == 3:
            inval = din[i][j][k]
            outval = dout[i][j][k]
        elif len(inshape) == 4:
            inval = din[i][j][k][l]
            outval = dout[i][j][k][l]
            
        print(f" Data comparison- in: {inval}, out: {outval}")
    
    
    
if __name__ == "__main__":
    
    #running a functionality test to make sure data is written to file and re-read properly
    runUnitTest()
    
    