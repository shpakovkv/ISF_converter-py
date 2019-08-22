isfreader
=========

This script is intended to convert .isf binary files generated by Tektronix MDO and MSO series oscilloscopes to simple text csv files with ASCii data.

##### Key features:
* Supports binary data encoding only
* Supports standard Y (YT) format and envelope (when Y data consists of min/max pairs)
* Outputs comma delimited ASCii data (one data point per line)

#### Simple usage:

`python isfreader.py inputfile.isf > outpufile.csv`


#### Author: 

Konstantin Shpakov, august 2019.



#### Based on:

1) [**isfread-py** by Gustavo Pasquevich, Universidad Nacional de La Plata - Argentina](https://github.com/gpasquev/isfread-py)

2) [Tektronix MDO4000C, MDO4000B, MDO4000, MSO4000B, DPO4000B and MDO3000 Series Oscilloscopes Programmer Manual. Revision A, 077-0510-09](https://www.tek.com/oscilloscope/mso4000-dpo4000-manual/mdo4000c-mdo4000b-mdo4000-mso4000b-dpo4000b-and-mdo3000-0)

-------------------------------------------------------------------------

isfconverter
============

This script adds command line interface (CLI) to the isfreader.

##### Usage: 
```
python ISFConverter.py -f filename
python ISFConverter.py -d path/to/input/files
python ISFConverter.py -d path/to/input/files -o path/to/output/dir
python ISFConverter.py @file_with_options
```

##### Optional arguments:


`-h, --help`  show this help message and exit 

`-d DIR, --directory DIR`  specify the directory containing data files. Default= the folder containing this code. 
                    
`-f FILE [FILE ...], --files FILE [FILE ...]` specify one or more (space separated) input file names after the flag.
                    
`--head, --include-header` adds header lines to the output files.

`-o DIR, --output-dir DIR` specify the output directory.
                    
`-s FILE [FILE ...], --save_as FILE [FILE ...]` specify one or more (space separated) output file names after the flag. The number of the output file names must be equal to the number of the input file names.
                    
`-v, --verbose` shows more information during the process.


##### Keywords

Tektronix, isf, csv, isfreader, python