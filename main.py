
import sys

"""
    Writes a .hex file containing the given data. Currently only supports files up to 256 bytes long, and breaks for anything longer.
    :param blocks: A byte array up to 256 bytes long. 
    :param filename: The file to write to.
"""
def write_hex_file(blocks: bytearray, filename: str) -> None:
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


def main():
    # step 1: get line of code
    # step 2: remove comments and multiple spaces
    # step 3: parse preprocessed line
    # step 4: store hex code in proper location in array
    # repeat until end of file
    # step 5: put hex codes in output file

    blocks = bytearray(b'\x00'*16*16) # one dimension - 16 bytes per block, 16 blocks - access with blocks[16*block + addr]
    for i in range(256):
        blocks[i] = i
    write_hex_file(blocks, "out.hex")
    pass

if __name__ == "__main__":
    main()