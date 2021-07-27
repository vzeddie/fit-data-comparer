#!/usr/bin/python3

import fitdecode
import argparse

def main():
    pass

# Ask what field you want to chart over?
if __name__ == "__main__":
    fit1 = "Run20210721072634.fit"
    fit2 = "Run20210727072255.fit"

    limit = 100
    counter = 0
    counter2 = 0
    with fitdecode.FitReader(fit1) as f1:
        for frame in f1:
            if counter < limit:
                if isinstance(frame, fitdecode.FitDataMessage):
                    print("-----")
                    print(hex(frame.global_mesg_num))
                    if frame.global_mesg_num == 0x14:
                        for field in frame.fields:
                            print(field.name, field.value, field.units)
                    else:
                        print(frame.def_mesg.name)
                        for field in frame.fields:
                            print(field.name, field.value, field.units)
                    
                        
                counter += 1
                counter2 += 1
            else:
                break

