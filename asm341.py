import sys
"""
    Writes a .hex file containing the given data. Currently only supports files up to 256 bytes long, and breaks for anything longer.
    :param blocks: A byte array up to 256 bytes long. 
    :param filename: The file to write to.
"""
def write_hex_file(blocks: bytearray, filename: str) -> None:
    # the intel .hex format is actually really simple for small stuff like this, it's just a text file
    # and it's compatible with quartus, so it's perfect for something like this
    # for more info, see https://en.wikipedia.org/wiki/Intel_HEX or https://www.keil.com/support/docs/1584/
    with open(filename, 'w') as f:
        for addr, inst in enumerate(blocks):
            addrhex = hex(addr)[2:].zfill(4)
            insthex = hex(inst)[2:].zfill(2)

            f.write(":")             # start code
            f.write('01')            # number of bytes in data
            f.write(addrhex)         # address
            f.write('00')            # data type of record - for this file it's always numeric data
            f.write(insthex)         # data
            checksum = (~(1 + addr + 0 + inst) + 1) & 0xFF
            f.write(hex(checksum)[2:].zfill(2) + '\n') # checksum - see https://en.wikipedia.org/wiki/Intel_HEX#Checksum_calculation
        f.write(':00000001FF')       # end of file marker

def preprocess(line: str) -> list:
    if ';' in line:
        line = line[:line.index(';')]  # remove everything to the right of the first semicolon if it exists
    splitline = line.split()  # removes all spaces - leaves instruction and params, that's it
    return splitline

def parse(processed_line: list, state: dict):

    # assembler directives
    if processed_line[0][0] == '.':
        if processed_line[0] == '.define':
            if len(processed_line) < 3:
                print(f'Error: Not enough arguments for .define on line {state["current_line"]}: {" ".join(processed_line)}\nExiting.')
                exit(1)
            state['defines'][processed_line[1]] = processed_line[2]
            return -1

        elif processed_line[0] == '.blk':
            blk = 0
            if len(processed_line) < 2:
                print(f'Error: Not enough arguments for .blk on line {state["current_line"]}: {" ".join(processed_line)}\nExiting.')
                exit(1)
            try:
                blk = int(processed_line[1], 16)
            except ValueError:
                print(f"Error: Could not convert parameter to .blk to integer on line {state['current_line']}: {' '.join(processed_line)}\nExiting.")
                exit(1)

            if not (0 <= blk <= 15):
                print(f"Error: Parameter to .blk out of range on line {state['current_line']}: {' '.join(processed_line)}\nValue must be between 0 and 15 inclusive.\nExiting.")
                exit(1)

            state['current_block'] = blk
            return -1

        else:
            print(f"Error: Unknown assembler directive on line {state['current_line']}: {processed_line[0]}\nExiting.")
            exit(1)



def main():

    if len(sys.argv) != 3:
        print("Wrong number of arguments.\nSyntax: python asm341.py <infile> <outfile>")
        return 1

    infilename = sys.argv[1]
    outfilename = sys.argv[2]

    # code is stored in one of 16 blocks, each 16 bytes long, for 256 instructions total
    # jump instuctions can only jump to the beginning of a block,
    # so file can only have up to 16 labels to jump to, less if there are more than
    # 16 instructions between two labels

    blocks = bytearray(b'\x00'*16*16) # one dimension - 16 bytes per block, 16 blocks
                                      # access with blocks[16*block + addr]
                                      # values that are not set are filled with 0 for now, might change to a nop when done

    assembler_state = {
        'defines':{}, # macros similar to c/c++'s #define - just text replacement though, no fancy function-like macros
        'current_line':0,  # the actual line in the file
        'current_block':0,
        'current_addr':0
    }

    # step 4: store hex code in proper location in array
    # repeat until end of file

    with open(infilename, 'r') as f:
        # step 1: get next line
        for line in f:
            assembler_state['current_line'] += 1

            # step 2: remove comments and multiple spaces
            processed = preprocess(line)

            # step 3: parse preprocessed line
            if len(processed) == 0:
                continue  # empty line, so there's nothing to do

            machine_code_instr = parse(processed, assembler_state)

    # step 5: put hex codes in output file
    write_hex_file(blocks, "out.hex")


if __name__ == "__main__":
    exit(main())