#!/usr/bin/python

import re, os
import sys
import random
import typer
from typing import Optional


def main(
    gztrace_filename: str,
    tracefile_filename: Optional[str] = typer.Argument(None),
    prio: int = typer.Argument(0),
):
    """
    gztrace_filename: gzipped trace file name

    tracefile_filename: output trace file name

    prio: What prios can be given
    """
    #  gztrace_filename = sys.argv[1]
    #  tracefile_filename = sys.argv[1][0:len(sys.argv[1])-3]
    if tracefile_filename is None:
        tracefile_filename = gztrace_filename[0 : len(sys.argv[1]) - 3]

    prios = list(range(0, prio+1))

    with open(tracefile_filename, "w") as outfile:
        temp_trace = tracefile_filename + ".temp"

        zcat_cmd = "zcat"
        # accomodate OSX
        if os.uname()[0] == "Darwin":
            print("Detected OSX, using gzcat...")
            zcat_cmd = "gzcat"

        if not os.path.exists(gztrace_filename):
            print("Could not find gzipped tracefile either")
            quit()
        else:
            print("Unzipping gz trace...")
            os.system("%s %s > %s" % (zcat_cmd, gztrace_filename, temp_trace))
        if not os.path.exists(tracefile_filename):
            print("FAILED")
            quit()
        else:
            print("OK")

        print("Parsing ")
        tracefile = open(temp_trace, "r")

        if gztrace_filename.startswith("k6"):
            print("k6 trace ...")
            linePattern = re.compile(
                r"(0x[0-9A-F]+)\s+([A-Z_]+)\s+([0-9.,]+)\s+(.*)"
            )
            for line in tracefile:
                searchResult = linePattern.search(line)
                if searchResult:
                    (address, command, time, units) = searchResult.groups()

                    length = len(time)
                    time = time[0 : length - 5]
                    temp = len(time)
                    if temp == 0:
                        time = "0"
                    time = time.replace(",", "")
                    time = time.replace(".", "")
                    if command != "BOFF" and command != "P_INT_ACK":
                        outfile.write(
                            "%s %s %s %s\n"
                            % (address, command, time, random.choice(prios))
                        )

        elif gztrace_filename.startswith("mase"):
            print("mase trace ...")
            os.system("cp %s %s" % (temp_trace, tracefile_filename))
            print("OK")

        else:
            print("Unknown trace file!!!")
            quit()

        os.system("rm %s" % temp_trace)


if __name__ == "__main__":
    typer.run(main)
