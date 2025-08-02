import sys
import os
import zlib
import struct
from PIL import Image

def convert_rgb565_to_rgba(data):
    pixels = []
    for i in range(0, len(data), 2):
        val = (data[i] << 8) | data[i+1]
        r = (val >> 11) & 0x1F
        g = (val >> 5) & 0x3F
        b = val & 0x1F
        r = (r << 3) | (r >> 2)
        g = (g << 2) | (g >> 4)
        b = (b << 3) | (b >> 2)
        pixels.append(bytes([r, g, b, 255]))
    return b''.join(pixels)

def convert_grayscale_to_rgba(data):
    return b''.join(bytes([v, v, v, 255]) for v in data)

def convert_rgb888_to_rgba(data):
    pixels = []
    for i in range(0, len(data), 3):
        r, g, b = data[i], data[i+1], data[i+2]
        pixels.append(bytes([r, g, b, 255]))
    return b''.join(pixels)

def ask_for_format():
    print("Select pixel format to use for all .cim files:")
    print("0 - RGBA8888 (4 bytes per pixel)")
    print("1 - RGB888 (3 bytes per pixel)")
    print("2 - RGB565 (2 bytes per pixel)")
    print("3 - Grayscale 8-bit (1 byte per pixel)")
    choice = input("Enter your choice (0-3): ").strip()
    if choice in ('0', '1', '2', '3'):
        return int(choice)
    print("Invalid input, defaulting to RGBA8888.")
    return 0

def read_cim(file_path, fmt):
    try:
        with open(file_path, "rb") as f:
            compressed_data = f.read()
        data = zlib.decompress(compressed_data)
    except zlib.error:
        print(f"Error: Failed to decompress '{file_path}'. Is this a valid .cim file?")
        return

    if len(data) < 12:
        print(f"Error: File too short to contain header '{file_path}'.")
        return

    width, height, file_fmt = struct.unpack(">III", data[:12])
    pixels = data[12:]

    # Ignore file_fmt, use fmt passed from batch prompt
    bpp_map = {0:4, 1:3, 2:2, 3:1}
    bpp = bpp_map.get(fmt, 4)

    expected_len = width * height * bpp
    if len(pixels) < expected_len:
        print(f"Warning: pixel data shorter than expected in '{file_path}' ({len(pixels)} < {expected_len}), adjusting height.")
        height = len(pixels) // (width * bpp)
        pixels = pixels[:width * height * bpp]

    try:
        if fmt == 0:
            img = Image.frombytes("RGBA", (width, height), pixels)
        elif fmt == 1:
            img = Image.frombytes("RGBA", (width, height), convert_rgb888_to_rgba(pixels))
        elif fmt == 2:
            img = Image.frombytes("RGBA", (width, height), convert_rgb565_to_rgba(pixels))
        elif fmt == 3:
            img = Image.frombytes("RGBA", (width, height), convert_grayscale_to_rgba(pixels))
        else:
            print(f"Unsupported format {fmt} for '{file_path}'")
            return

        output_path = os.path.splitext(file_path)[0] + ".png"
        img.save(output_path)
        print(f"Converted CIM -> PNG: {file_path} -> {output_path}")
    except Exception as e:
        print(f"Failed to create image for '{file_path}': {e}")

def write_cim(file_path):
    try:
        img = Image.open(file_path).convert("RGBA")
    except Exception as e:
        print(f"Failed to open image '{file_path}': {e}")
        return

    width, height = img.size
    raw_data = img.tobytes()

    header = struct.pack(">III", width, height, 0)  # format 0 = RGBA8888

    compressed = zlib.compress(header + raw_data)

    out_path = os.path.splitext(file_path)[0] + ".cim"
    try:
        with open(out_path, "wb") as f:
            f.write(compressed)
        print(f"Converted PNG -> CIM: {file_path} -> {out_path}")
    except Exception as e:
        print(f"Failed to save CIM file '{out_path}': {e}")

def main():
    if len(sys.argv) < 2:
        print("Please drag & drop one or more .cim or .png files onto this script.")
        input("Press Enter to exit.")
        return

    files = sys.argv[1:]

    # Detect if any .cim files exist, ask format once
    has_cim = any(f.lower().endswith(".cim") for f in files)
    fmt = 0
    if has_cim:
        fmt = ask_for_format()

    for file_path in files:
        ext = file_path.lower()
        if ext.endswith(".cim"):
            read_cim(file_path, fmt)
        elif ext.endswith(".png"):
            write_cim(file_path)
        else:
            print(f"Skipping unsupported file '{file_path}'")

    input("Batch done. Press Enter to exit.")

if __name__ == "__main__":
    main()
