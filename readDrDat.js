
/* This function reads data from an ArrayBuffer that was previously read in from a File or Blob
    object in javascript, identifies the variables and returns all variables in the file in a list */


readDrDatFile = function(fileBuffer) { //passed ArrayBuffer from FileReader
    var rawData = [];
    
    //reading initial file data
    let dv = new DataView(fileBuffer, 0); 
    const useLittle = true; //true for little-endian, false for big-endian
    const validator = dv.getInt8(0, useLittle); //getting first number (should convert to 69 in decimal format, from 8-bit int)
    const nvars = dv.getInt8(1, useLittle); //getting number of variables (8-bit int)
    
    let head = 2; //start reading through file data at third byte (second index)
    
    if (validator != 69) { //first 8 bits should work out to decimal code 69
        alert("Invalid input file selected!");
        settings.isGood = 0;
        return([[], [], []]);
    }
    
    //iterating through each variable
    for (let varnum = 0; varnum < nvars; varnum++) {
        
        //getting number of bits (in 8-bit number) and number of dimensions (8-bit number)
        let nbits = dv.getInt8(head, useLittle);
        let nbytes = nbits / 8;
        head++;
        let ndims = dv.getInt8(head, useLittle);
        head++;
        
        //getting number of values in each dimension (32-bit number each)
        let dataSize = [];
        for (let cdim = 0; cdim < ndims; cdim++) {
            let cdimsize = dv.getInt32(head, useLittle);
            head += 4;
            dataSize.push(cdimsize);
        }
        
        //getting/converting variable scale and then offset (conversion factor is 1E3, each is a 32-bit number)
        let scale = dv.getInt32(head, useLittle);
        scale /= 1E3;
        head += 4;
        let offset = dv.getInt32(head, useLittle);
        offset /= 1E3;
        head += 4;
        
        //creating 1D of data from file
        let npoints = 1;
        for (let i = 0; i < dataSize.length; i++) {
            npoints *= dataSize[i]; //total number of datapoints across all dimensions
        }
        
        let dataArray = []
        if (nbits == 8) {
            for (let i = head; i < head + npoints * nbytes; i += nbytes) {
                dataArray.push(dv.getUint8(i, useLittle)/scale - offset);
            }
        } else if (nbits == 16) {
            for (let i = head; i < head + npoints * nbytes; i += nbytes) {
                dataArray.push(dv.getUint16(i, useLittle)/scale - offset);
            }
        } else if (nbits == 32) {
            for (let i = head; i < head + npoints * nbytes; i += nbytes) {
                dataArray.push(dv.getUint32(i, useLittle)/scale - offset);
            }
        } else {
            alert("Invalid bit length provided in file!");
        }
        
        head += npoints * nbytes;
        
        //resizing data from file to match appropriate dimensions
        let cdataNd = [];
        if (ndims > 1) {
            cdataNd = math.reshape(dataArray, dataSize);
        } else {
            cdataNd = dataArray;
        }
        
        rawData.push(cdataNd);
    }
    
    return(rawData);
    
}

