#!/usr/bin/env python

import re, os
import sys
import numpy as np
from numpy.random import choice
import typer
from typing import Optional, List


def main(
    gztrace_filename: str,
    tracefile_filename: Optional[str] = typer.Argument(None),
    prio: int = typer.Argument(0),
    weights: Optional[List[float]] = typer.Argument(None),
):
    """
    gztrace_filename: gzipped trace file name

    tracefile_filename: output trace file name

    prio: What prios can be given

    weights: Weights for prios
    """
    if tracefile_filename is None:
        tracefile_filename = gztrace_filename[0 : len(sys.argv[1]) - 3]

    if weights is None or len(weights) == 0:
        weights = [1.0 / (prio + 1)] * (prio + 1)


    # Distribute weight...
    if len(weights) <= prio:
        s0 = 1 - sum(weights)

        while len(weights) <= prio:
            weights.append(s0 / (prio))

    if sum(weights) != 1:
        print(
            f"""ERROR: sum of weights not equal to 1.\nDo you wish to augment the probability of zero? y/n"""
        )

        yPattern = re.compile(r"^[yY][eE]?[sS]?$")
        nPattern = re.compile(r"^[nN][oO]?$")
        c = input()
        while yPattern.match(c) is None and nPattern.match(c) is None:
            c = input("Invalid input. Please enter y[es] / n[o]")

        if yPattern.match(c) is not None and nPattern.match(c) is None:
            weights[0] += 1 - sum(weights)
            

    print(f"Weights: {weights}")

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
            linePattern = re.compile(r"(0x[0-9A-F]+)\s+([A-Z_]+)\s+([0-9.,]+)\s+(.*)")
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
                            % (
                                address,
                                command,
                                time,
                                choice(np.arange(prio + 1), p=weights),
                            )
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
