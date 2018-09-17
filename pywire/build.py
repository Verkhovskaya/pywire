from .ast_logic import generate_vhdl, generate_timing
import os
import datetime
import subprocess


def build(notes=""):
    frequency = 50
    clock_pin = "P56"
    base_address = "/Users/2017-A/Dropbox/fpga/fpga_builds"
    timestamp = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_").replace("-", "_")[:-7]
    directory = base_address + "/" + timestamp
    os.mkdir(directory)
    os.chdir(directory)
    os.mkdir("src")
    top = open(directory + "/src/generated_top.vhd", "w")
    new_vhdl = generate_vhdl()
    print(new_vhdl)
    top.write(new_vhdl)
    top.close()
    if notes:
        notes_file = open(directory + "/build_notes.txt", "w")
        notes_file.write(notes)
    ucf = open(directory + "/src/generated_top.ucf", "w")
    new_ucf = generate_timing(frequency, clock_pin)
    print("")
    print(new_ucf)
    ucf.write(new_ucf)
    ucf.close()
    build_files = ["generated_top.vhd", "generated_top.ucf"]
    top_file = "generated_top"
    args = timestamp + " " + top_file + " " + " ".join(build_files)
    print("bash /Users/2017-A/Dropbox/tools/fpga_builds/build_fpga.sh " + args)
    subprocess.call("bash /Users/2017-A/Dropbox/fpga/fpga_builds/build_fpga.sh " + args, shell=True)