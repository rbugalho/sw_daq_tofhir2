#!/usr/bin/env python

import os
import argparse

parser = argparse.ArgumentParser(description='convert raw data')
parser.add_argument("--config", type=str, required=True, help="Configuration file")
parser.add_argument("-r", type=str, dest="run", required=True, help = "Run number")
parser.add_argument("--mode", type=str, required=True, choices=["r", "s", "c", "e"], help = "reconstruction mode (singles, coincicences or event)")
parser.add_argument("--refChannel", type=str, required=False, help = "reference channel")
parser.add_argument("--pedestals", dest="pedestals", action="store_true", help="Enable the acquisition of pedestals")

args = parser.parse_args()

if args.mode == 'r':
    command = "./convert_raw_to_raw --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+" -o /data/TOFHIR2/reco/run"+args.run+"_r.root"
    os.system(command)

if args.mode == 's':
    mainCommand = "./convert_raw_to_singles --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+" --writeRoot"
    if args.pedestals:
        command = "./convert_raw_to_singles --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+"_ped1 -o /data/TOFHIR2/reco/run"+args.run+"_ped1_s.root --writeRoot"
        os.system(command)
        command = "./convert_raw_to_singles --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+"_ped2 -o /data/TOFHIR2/reco/run"+args.run+"_ped2_s.root --writeRoot"
        os.system(command)
        command = "./analyze_pedestals.exe /data/TOFHIR2/reco/run"+args.run+"_ped1_s.root /data/TOFHIR2/reco/run"+args.run+"_ped2_s.root /data/TOFHIR2/reco/run"+args.run+"_pedestals.root"
        os.system(command)
        mainCommand += " --pedestals -o /data/TOFHIR2/reco/run"+args.run+"_ped_s.root"
    else:
        mainCommand += " -o /data/TOFHIR2/reco/run"+args.run+"_s.root"
    os.system(mainCommand)

if args.mode == 'c':
    command = "./convert_raw_to_coincidence --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+" -o /data/TOFHIR2/reco/run"+args.run+"_c.root --writeRoot"
    os.system(command)

if args.mode == 'e':
    mainCommand = "./convert_raw_to_event --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+" --writeRoot"
    if args.pedestals:
        command = "./convert_raw_to_singles --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+"_ped1 -o /data/TOFHIR2/reco/run"+args.run+"_ped1_s.root --writeRoot"
        os.system(command)
        command = "./convert_raw_to_singles --config "+args.config+" -i /data/TOFHIR2/raw/run"+args.run+"_ped2 -o /data/TOFHIR2/reco/run"+args.run+"_ped2_s.root --writeRoot"
        os.system(command)
        command = "./analyze_pedestals.exe /data/TOFHIR2/reco/run"+args.run+"_ped1_s.root /data/TOFHIR2/reco/run"+args.run+"_ped2_s.root /data/TOFHIR2/reco/run"+args.run+"_pedestals.root"
        os.system(command)
        mainCommand += " --pedestals -o /data/TOFHIR2/reco/run"+args.run+"_ped_e.root"
    else:
        mainCommand += " -o /data/TOFHIR2/reco/run"+args.run+"_e.root"
    if args.refChannel :
        mainCommand += " --refChannel "+args.refChannel
    os.system(mainCommand)
