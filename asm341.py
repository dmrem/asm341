import sys
"""
    Writes a .hex file containing the given data. Currently only supports files up to 256 bytes long, and breaks for anything longer.
    :param blocks: A byte array up to 256 bytes long. 
    :param filename: The file to write to.
"""
def write_hex_file(blocks: bytearray, filename: str) -> None:
    # the intel .hex format is actually really simple for small stuff like this, it's just a super simple text file,
    # the format is well documented, and it's compatible with quartus, so it's perfect for something like this
    # for more info, see https://en.wikipedia.org/wiki/Intel_HEX or https://www.keil.com/support/docs/1584/
    # or just google it, there's tons of info out there
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

"""
    Processes a line to remove comments and extra spaces, changes all chars to lowercase, then splits it into tokens
    :param line: The line of asm to process
"""
def preprocess(line: str) -> list:
    if ';' in line:
        line = line[:line.index(';')] # remove everything to the right of the first semicolon if it exists
    splitline = line.lower().split()  # changes to lowercase, removes all spaces - leaves instruction and params, that's it
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

        elif processed_line[0] == '.block':
            block = 0
            if len(processed_line) < 2:
                print(f'Error: Not enough arguments for .block on line {state["current_line"]}: {" ".join(processed_line)}\nExiting.')
                exit(1)
            try:
                block = int(processed_line[1], 16)
            except ValueError:
                print(f"Error: Could not convert parameter to .block to integer on line {state['current_line']}: {' '.join(processed_line)}\nExiting.")
                exit(1)

            if not (0 <= block <= 15):
                print(f"Error: Parameter to .block out of range on line {state['current_line']}: {' '.join(processed_line)}\nValue must be between 0 and 15 inclusive.\nExiting.")
                exit(1)

            state['current_block'] = block
            return -1

        else:
            print(f"Error: Unknown assembler directive on line {state['current_line']}: {processed_line[0]}\nExiting.")
            exit(1)

    # instructions

    instruction_base_values = {
        'ld' : 0b00000000, # load
        'mov': 0b10000000, # move
        'jmp': 0b11100000, # unconditional jump
        'jnz': 0b11110000, # jump if not zero
        # alu instructions
        'tcm': 0b11000000, # two's complement
        'nop': 0b11001000, # currently nop
        'sub': 0b11000001, # subtract
        'add': 0b11000010, # add
        'muh': 0b11000011, # high 4 bits of x*y
        'mul': 0b11000100, # low 4 bits of x*y
        'xor': 0b11000101, # bitwise xor
        'and': 0b11000110, # bitwise and
        'ocm': 0b11000111 # one's complement
        #'nop2': 0b11001111, # currently nop, no point having two nop instructions so I'll add this one if the previous is overwritten in an exam or something
    }

    register_values = {
        'x0': 0, # general reg / alu operand
        'x1': 1, # general reg / alu operand
        'y0': 2, # general reg / alu operand
        'y1': 3, # general reg / alu operand
        'r' : 4, # alu result
        'o_reg': 4, # mcu output
        'm' : 5, # data memory address auto-increment value
        'i' : 6, # data memory address
        'dm': 7  # data memory value
    }

    instruction_num_params = {
        'ld' : 2,  # load
        'mov': 2,  # move
        'jmp': 1,  # unconditional jump
        'jnz': 1,  # jump if not zero
        # alu instructions
        'tcm': 1,  # two's complement
        'nop': 0,  # currently nop
        'sub': 2,  # subtract
        'add': 2,  # add
        'muh': 2,  # high 4 bits of x*y
        'mul': 2,  # low 4 bits of x*y
        'xor': 2,  # bitwise xor
        'and': 2,  # bitwise and
        'ocm': 1  # one's complement
    }

    # numeric parameters
    p1 = 0
    p2 = 0

    # this part of the parsing would be easier and nicer if I were using a different language or if I didn't want
    # to keep this program all in 1 file, but whatever

    if processed_line[0] == 'ld':
        if len(processed_line) < instruction_num_params['ld']:
            print(f'Error: Not enough arguments for ld on line {state["current_line"]}: {" ".join(processed_line)}\nExiting.')
            exit(1)

        if processed_line[1] not in register_values:
            print(f'Error: Parameter 1 for ld on line {state["current_line"]} is not a register: {" ".join(processed_line)}\nExiting.')
            exit(1)

        if processed_line[1] == 'o_reg':
            print(f"Warning: o_reg used as destination to ld on line {state['current_line']}. Treating like the r register instead.\n")

        p1 = register_values[processed_line[1]] << 4

        try:
            p2 = int(processed_line[2], 16)
        except ValueError:
            print(f"Error: Could not convert parameter 2 of ld to integer on line {state['current_line']}: {' '.join(processed_line)}\nExiting.")
            exit(1)

        if not (0 <= p2 <= 15):
            print(
                f"Error: Parameter 2 of ld out of range on line {state['current_line']}: {' '.join(processed_line)}\nValue must be between 0 and F inclusive.\nExiting.")
            exit(1)

        return instruction_base_values['ld'] | p1 | p2


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

    blocks = bytearray(b'\xc8'*16*16) # fill with nop instructions by default
                                      # one dimension - 16 bytes per block, 16 blocks
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
            if machine_code_instr == -1: # -1 indicates the line was an assembler directive
                continue

            block = assembler_state['current_block']
            addr = assembler_state['current_addr']
            blocks[block * 16 + addr] = machine_code_instr



    # step 5: put hex codes in output file
    write_hex_file(blocks, "out.hex")


if __name__ == "__main__":
    exit(main())