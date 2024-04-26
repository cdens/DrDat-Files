# **DrData (drd) File Reading/Writing**


**Author: Casey Densmore (cdensmore101@gmail.com)**


## Overview <a id="overview"></a>
The DrData (.drd) file format is useful for saving  a single variable or a series of variables containing gridded, multidimensional data with explicit control over integer size and data conversion, reducing file size while retaining maximum control over data resolution and conversion between floating point numbers and N-bit integers. Any N-bit integers are theoretically supported by the file type, however the code only currently functions for 8-, 16-, and 32-bit integers. Data are input and returned as a list (Python) or array (Javascript) containing a series of variables stored as Nd numpy arrays (Python) or multidimensional arrays (Javascript). Future support will include read/write capabilities for additional languages.

The python file (drdatFileInteraction.py) includes read and write functions, as well as a unit test that can be used as an example for how to read/write data to and from the file format. The javascript file (readDrDat.js) includes a read-only function to convert an input [ArrayBuffer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer) into an output array containing the variables stored in the file. 


## File Format Overview
The first byte of the drd file format contains the decimal number 69, to confirm that the file is a drd version 1 format (future non backwards-compatible versions of the file format could use different integers). The second byte contains a number (1-255) containing the number of variables stored in the file. Following the second byte, variables are written in order, with a series of header data for each variable, followed by the variable data. All data is encoded as little-endian.

Variable data headers include:

* 1 byte: the number of bits (Nbits) for each data point for the current variable (currently supports 8, 16, and 32)
* 1 byte: the number of dimensions (Ndim) for the current variable 
* 4 bytes (for each dimension): the number of data points along each dimension for the current variable, in order of how the data should be reshaped (stored as dataSize, in an array/list)
* 4 bytes: the scale factor applied to the current variable (divide the 32-bit scale signed integer by 1000 to convert from integer to the scale factor applied)
* 4 bytes: the offset factor applied to the current variable (again, divide by 1000 to convert to the appropriate value from the signed integer)

To read each variable, the next Nbits * np.prod(dataSize) bits of the file following the variable's header are converted into a one-dimensional array of data before offset and scale are applied, and the data is reshaped using the dataSize variable. 

All data are stored as unsigned integers. The only information in the file stored as signed integers are the offset and scale factors for each variable. The conversions between floating point data (D) and integer-represented data (Dint) are:

Dint = (D + offset) * scale

D = Dint/scale - offset


## Future Work

This project was thrown together for a particular use case but has a wider range of applications! Future work to improve this product includes:

* Supporting a wider range of languages for read/write capabilities (particularly data analysis oriented languages such as MATLAB, FORTRAN, Julia, and R)
* Supporting a wider range of bit-depth for variables. An optimal program would support 1-, 4-, 8-, 12-, 16-, 24-, 32-, and 64-bit data
* Include a wider range of scale and offset values (currently, storing them as 32-bit signed integers with an internal scaling factor of 1E3 limits the range to +/- 2.6E9, with a resolution of 1E-3. 
*  Support variable names being stored as UTF-8 character arrays in the header data for each variable