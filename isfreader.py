#!/usr/bin/env python
# coding: utf-8

"""This script is intended to convert .isf binary files generated by
tektronix MDO and MSO series oscilloscopes to simple text csv files with ASCii data.

Simple usage:
python isfreader.py inputfile.isf > outputfile.csv


Author: Konstantin Shpakov, august 2019.



REFERENCE:
1) https://github.com/gpasquev/isfread-py by Gustavo Pasquevich, Universidad Nacional de La Plata - Argentina
2) Tektronix MDO4000C, MDO4000B, MDO4000, MSO4000B, DPO4000B and MDO3000 Series Oscilloscopes Programmer Manual
   Revision A, 077-0510-09
   https://www.tek.com/oscilloscope/mso4000-dpo4000-manual/mdo4000c-mdo4000b-mdo4000-mso4000b-dpo4000b-and-mdo3000-0




=============================== ISF file HEADER REFERENCE ==============================================================
ENCODING FORMAT --------------------------------------------------------------------------------------------------------
NR_PT:          [int] This value indicates the number of data points recorded in the file.
BYT_NR:         [int] This value specifies the number of bytes per data point in the waveform data.
BIT_NR:         [int] This value specifies the number of bits per data point in the waveform data.

ENCDG:          [str] This value specifies the encoding of the waveform data. Possible values:
                "ASCii",
                "BIN" or "BINARY"

BN_FMT:         [str] This value specifies the binary format.
                "RI" specifies signed integer data point representation.
                "RP" specifies positive integer data point representation.
                "FP" specifies floating point data representation.

BYT_OR:         [str] This value specifies the byte order for the BINARY encoding. Possible values:
                "MSB" (most significant byte first),
                "LSB" (least significant byte first).

PT_FMT:         [str] This value indicates the format of the data points in the waveform record. The values can be:
                "Y" for YT format,
                "ENV" for envelope format (min/max pairs).

CONVERSION FACTORS -----------------------------------------------------------------------------------------------------
X[i] = XZERO + XINCR * (i - 1)
Y[i] = YZERO + YMULT * DataPoint[i]

XINCR:          [float] This value indicates the time, in seconds, or frequency, in hertz, between data points
                in the waveform record.

XZERO:          [float] This value indicates the time, in seconds, or frequency, in hertz, of the first data point
                in the waveform record.

YMULT:          [float] This value indicates the multiplying factor to convert the data point values
                from digitizing levels to the units

YZERO:          [float] This value indicates the vertical offset of the source waveform in units.

SECONDARY INFO ---------------------------------------------------------------------------------------------------------
XUNIT:          ["str"] This value indicates the units of the x-axis of the waveform record. Possible values: "s", "Hz".

YUNIT:          ["str"] This value indicates the vertical units of data points in the waveform record.
                This can be any of several string values, depending upon the vertical units of the source waveform

YOFF:           [float] This value indicates the vertical position of the source waveform (on the screen) in digitizing
                levels.

WFID:           ["str"] This quoted string represents information about the source waveform,
                that was written to the file: number of channel, coupling, scales, etc.

DOMAIN:         [str] This value indicates the domain in which the source waveform is displayed and stored.
                For RF time domain traces, the domain is Time and waveform transfer information is treated as
                integer information.
                For RF frequency domain traces, the domain is Frequency and waveform transfer information is treated as
                floating point information.

WFMTYPE         [str] This value indicates the type of the source waveform.
                ANALOG indicates an RF time domain trace.
                RF_FD indicates an RF frequency domain trace (frequency domain waveform).

CENTERFREQUENCY:This value indicates the center frequency, in hertz, of the source waveform.

SPAN:           [float] This value indicates the frequency span, in hertz, of the source waveform.
REFLEVEL:       [float] This value indicates the reference level, in watts, of the source waveform.

VSCALE:         [float] The nominal value, in volts per division, used to vertically scale the input channels
                for a user-defined custom mask.

HSCALE:         [float] The nominal timing resolution, in time/division, used to draw
                a user-defined custom mask pulse shape.

VPOS:           [float] The nominal value, in divisions, used to vertically position the input channels
                for a user-defined custom mask.

VOFFSET:        [float] The nominal value, in volts, used to vertically offset the input channels
                for a user-defined custom mask.

HDELAY:         [float] No description found.

USELESS ----------------------------------------------------------------------------------------------------------------
PT_OFF:         [int] This value is always 0.
PT_ORDER:       [str] This value is always "LINear".

"""

from __future__ import print_function
import os
import re
import numpy

# ENCODING = 'utf-8'
ENCODING = 'latin-1'

fmt = {"MSB": ">",      # most significant byte first (big-endian)
       "LSB": "<",      # least significant byte first (little-endian)
       "RP": "u",       # unsigned integer
       "RI": "i",       # signed integer
       "FP": "f"}       # float


def get_head(raw_string):
    """Gets parameters (header) from string.
    Returns a dictionary with name-value pairs from header
    as well as data_size and data_start parameters.

    :param raw_string:  first few bytes from isf file
    :return:            (head, data_start, data_size)
    """
    head = dict()
    data_start = 0
    data_size = 0

    # gets (param_name, param_val) pairs:
    param_iter = re.finditer(r'(?:[:;])([\w]+)(?:\s)(?:")?([^;"]+)', raw_string.decode(ENCODING))

    for param in param_iter:
        name = param.groups()[0]
        if name != "CURVE":
            val = param.groups()[1]
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            head[name] = val
        else:
            # after ":CURVE " we have "#nxxxxxx"
            # where n is the number of 'x',
            # and 'xxxxxx' is the size in bytes of binary data that follows
            n = int(param.groups()[1][1])              # used 0-based index of match group
            data_size = int(param.groups()[1][2:n+2])
            data_start = param.start(2) + 2 + n        # used 1-based index of match group

    # data size check
    calc_data_size = head["BYT_NR"] * head["NR_PT"]
    if calc_data_size != data_size:
        print("Warning! BYT_NR * NR_PT != CURVE data size!!\n {} != {}".format(calc_data_size, data_size))
    return head, data_start, data_size


def get_numpy_fmt(header):
    """Converts isf file y-data points format to numpy.dtype, which consist from 3 chars:
    1) byte order
    2) type (int/float/etc.)
    3) size in bytes

    :param header:  dict with isf file parameters
    :return:        numpy.dtype
    """
    data_format = ""
    data_format += fmt[header["BYT_OR"]]
    data_format += fmt[header["BN_FMT"]]
    data_format += str(header["BYT_NR"])
    return data_format


def read_isf(filename):
    """Reads data from isf file and returns (x_array, y_array, header).
    Where x_array: numpy.ndarray with x axis points
    y_array: numpy.ndarray with y axis points

    For "Y" data format, x_array.size == y_array.size
    Each (x_array[i], y_array[i]) pair is the data point

    For "ENV" data format (min/max pairs): x_array.size * 2 == y_array.size
    Each y_array[i * 2] is the minimum value recorded by oscilloscope
    and y_array[i * 2 + 1] is the maximum value recorded by oscilloscope

    header: dict with name-value pairs of the isf file data parameters

    :param filename:    the path/name of an isf file
    :return:            (x_array, y_array, header)
    """
    assert os.path.isfile(filename), "Cannot find file {}".format(filename)
    raw_data = None
    with open(filename, "rb") as fid:
        raw_data = fid.read(1024)
        head, y_start, y_size = get_head(raw_data)

        # not all possible formats are supported yet
        assert head["PT_FMT"] in ("Y", "ENV"), "Unsupported data format '{}'.".format(head["PT_FMT"])
        assert head["ENCDG"] in ("BIN", "BINARY"), "Unsupported data encoding '{}'.".format(head["ENCDG"])

        fid.seek(y_start)
        raw_data = fid.read(y_size)
        if len(raw_data) != y_size:
            print("y_size = {}\nlen(raw_data) = {}".format(y_size, len(raw_data)))
            raise EOFError("Not enough bytes in file. EOF reached while reading.")

        numpy_type = get_numpy_fmt(head)
        y_data = numpy.ndarray(shape=(head["NR_PT"],), dtype=numpy_type, buffer=raw_data)
        y_data = ((y_data - head["YOFF"]) * head["YMULT"]) + head["YZERO"]

        head["XSTOP"] = head["XZERO"] + head["XINCR"] * head["NR_PT"]       # last x data point (not included)
        # x_data = numpy.arange(head["XZERO"], head["XSTOP"], head["XINCR"], dtype=y_data.dtype)
        x_data = None
        if head["PT_FMT"] == "Y":
            x_data = numpy.linspace(head["XZERO"], head["XSTOP"] - head["XINCR"],
                                    num=head["NR_PT"], dtype=y_data.dtype)

        elif head["PT_FMT"] == "ENV":
            x_data = numpy.linspace(head["XZERO"], head["XSTOP"] - head["XINCR"],
                                    num=(head["NR_PT"] / 2), dtype=y_data.dtype)
        return x_data, y_data, head


def main():
    """Reads input isf file and outputs (print) x,y data line by line
    Usage: python isfreader.py inpytfile.isf > outpufile.csv
           python isfreader.py --head inpytfile.isf > outpufile.csv
    :return: None
    """
    import sys

    print_head = False

    # check
    assert len(sys.argv) > 1, "Please specify file path/name."

    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("Usage: python isfreader.py inpytfile.isf > outpufile.csv\n"
              "       python isfreader.py --head inpytfile.isf > outpufile.csv")
        return

    if len(sys.argv) > 2:
        assert len(sys.argv) == 3, "Too many input arguments!"
        assert sys.argv[1] == "--head", "Unknown parameter {}".format(sys.argv[1])
        print_head = True

    # read
    x_data, y_data, head = read_isf(sys.argv[1])

    # save
    if print_head:
        # TODO: check print with head
        for line in head:
            print(line)
    if head["PT_FMT"] == "Y":
        for val in zip(x_data, y_data):
            print("{}, {}".format(val[0], val[1]))
    elif head["PT_FMT"] == "ENV":
        for idx in range(head["NR_PT"] / 2):
            print("{}, {}, {}".format(x_data[idx], y_data[idx * 2], y_data[idx * 2 + 1]))


if __name__ == "__main__":
    main()
