import glob
import zipfile
import binascii
import shutil
import time
from PIL import Image
import os
import numpy as np


# Header- und Spacer-Werte definieren
header1 = '4247726d0302'
header2 = '008f00642f626c6120626c6120626c61205649502d4841434b2064616d61723173745c2773205453544f20476f6420444c432047656e657261746f72202d204d6573732077697468207468652062657374202d20646965206c696b652074686520726573742f31000001000802310001'
spacer2 = '00010000'
zeSi = '00010203'
duCrc = '33333333'

def list_directories(base_path):
    dir_list = []
    for root, dirs, _ in os.walk(base_path):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            dir_list.append(dir_path)
    return dir_list


def update_timestamps(directory):
    current_time = time.time()
    for root, dirs, files in os.walk(directory):
        for name in files:
            file_path = os.path.join(root, name)
            os.utime(file_path, (current_time, current_time))


def save_header(header, header_file_path):
    with open(header_file_path, 'wb') as file:
        file.write(header)
    print(f"Header saved at {header_file_path}")


def load_header(header_file_path):
    with open(header_file_path, 'rb') as file:
        header = file.read(8)
    print(f"Header loaded from {header_file_path}")
    return header


def convert_rgba_to_png(rgb_file_path, output_png_path):
    with open(rgb_file_path, 'rb') as file:
        header_file_path = "header/" + os.path.basename(rgb_file_path) + ".hdr"
        print(rgb_file_path)
        # Lese den 8-Byte-Header
        header = file.read(8)

        h_int = int(header[7]) * 256 + int(header[6])
        print('height=%d' % h_int)
        height = h_int

        w_int = int(header[5]) * 256 + int(header[4])
        print('height=%d' % w_int)
        width = w_int

        # Lese den Rest der Datei
        rgb_data = file.read()

        # Bestimme die Anzahl der Pixel basierend auf RGBA (4 Bytes pro Pixel)
        total_pixels = len(rgb_data) // 4
        print("Total Pixels:", total_pixels)

        # Berechne die Breite
        #width = total_pixels // height
        #print('width=%d' % width)

        print(f"Breite: {width}, Höhe: {height}")
        abgr_data = np.frombuffer(rgb_data, dtype=np.uint8).reshape(height, width, 4)
        image = Image.fromarray(abgr_data, 'RGBA')
        image.save(output_png_path)
        print(f"Saved PNG at {output_png_path} with dimensions {width}x{height}")

        save_header(header, header_file_path)

def convert_png_to_rgb(png_file_path, rgb_output_path):
    header_file_path = "header/" + os.path.basename(rgb_output_path) + ".hdr"
    header = load_header(header_file_path)
    img = Image.open(png_file_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    data = np.array(img)
    flat_data = data.flatten()
    with open(rgb_output_path, 'wb') as file:
        file.write(header)  # Schreibe den gespeicherten Header
        file.write(flat_data)
    print(f"Saved RGB at {rgb_output_path}")
    os.remove(png_file_path)  # Delete the PNG file after conversion
    print(f"Deleted {png_file_path}")



def delete_hdr_files(header_dir):
    hdr_files = glob.glob(os.path.join(header_dir, "*.hdr"))
    for hdr_file in hdr_files:
        os.remove(hdr_file)
        print(f"Deleted header file {hdr_file}")

def unpack_zip(source_zip, target_folder):
    with zipfile.ZipFile(source_zip, 'r') as zip_ref:
        zip_ref.extractall(target_folder)
    print(f"Extracted {source_zip} to {target_folder}")

def create_zero_file(directory):
    # Temporäre Dateien löschen
    print("Removing temp files")
    for temp_file in ["build1", "build2", "build3", "0", "1"]:
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass

    # Update timestamps of files in 'xml' directory
    update_timestamps(os.path.join(directory))

    # Archiv erstellen
    print("Creating ZIP archive from 'xml' directory")
    shutil.make_archive('1', format="zip", root_dir=os.path.join(directory, "one"))
    os.rename('1.zip', '1')

    # CRC32 des Archivs berechnen
    with open('1', 'rb') as file:
        filedata = file.read()
    crc = binascii.crc32(filedata) & 0xFFFFFFFF
    crcHex = format(crc, '08x')
    crcAsc = binascii.a2b_hex(crcHex.encode())

    # Metadaten berechnen
    xml_directory = os.path.join(directory, "one")
    count = len([item for item in os.listdir(xml_directory) if os.path.isfile(os.path.join(xml_directory, item))])
    countHex = format(count, '04x')
    countAsc = binascii.a2b_hex(countHex.encode())
    header1Asc = binascii.a2b_hex(header1.encode())
    header2Asc = binascii.a2b_hex(header2.encode())
    ducrcAsc = binascii.a2b_hex(duCrc.encode())

    # Dateien verarbeiten und build1 erstellen
    print("Creating build1 file")
    with open('build1', 'wb') as build1_file:
        for file in glob.glob(os.path.join(xml_directory, '*.*')):
            files = os.path.basename(file)  # Nur den Dateinamen ohne Pfad verwenden
            sfile = files.split(".")
            fsize = os.path.getsize(file)

            leng = len(files) + 1
            fileHex = format(leng, '02x')
            fileAsc = binascii.a2b_hex(fileHex.encode())

            file2Hex = format(leng, '04x')
            file2Asc = binascii.a2b_hex(file2Hex.encode())

            att = len(sfile[1]) + 1
            attHex = format(att, '04x')
            attAsc = binascii.a2b_hex(attHex.encode())

            sizeHex = format(fsize, '010x')
            sizeAsc = binascii.a2b_hex(sizeHex.encode())
            spacer2Asc = binascii.a2b_hex(spacer2.encode())
            zeSiAsc = binascii.a2b_hex(zeSi.encode())

            build = fileAsc + files.encode() + attAsc + sfile[1].encode() + files.encode() + sizeAsc + spacer2Asc
            buildlen = len(build) + 2
            buildHex = format(buildlen, '04x')
            buildAsc = binascii.a2b_hex(buildHex.encode())
            build1 = buildAsc + fileAsc + files.encode() + attAsc + sfile[1].encode() + file2Asc + files.encode() + sizeAsc + spacer2Asc

            build1_file.write(build1)

    # build2 erstellen
    print("Creating build2 file")
    with open('build1', 'rb') as build1_file:
        red = build1_file.read()
    build2 = header1Asc + zeSiAsc + header2Asc + crcAsc + countAsc + red + ducrcAsc
    with open('build2', 'wb') as build2_file:
        build2_file.write(build2)

    # build3 erstellen
    print("Creating build3 file")
    bsize = os.path.getsize('build2')
    bsizeHex = format(bsize, '08x')
    bsizeAsc = binascii.a2b_hex(bsizeHex.encode())
    build3 = header1Asc + bsizeAsc + header2Asc + crcAsc + countAsc + red
    with open('build3', 'wb') as build3_file:
        build3_file.write(build3)

    # CRC32 des gesamten build3 berechnen und hinzufügen
    print("Finalizing Zero File")
    with open('build3', 'rb') as filedata2:
        filedata2 = filedata2.read()
    crc2 = binascii.crc32(filedata2) & 0xFFFFFFFF
    crc2Hex = format(crc2, '08x')
    crc2Asc = binascii.a2b_hex(crc2Hex.encode())
    with open('build3', 'ab') as f2:
        f2.write(crc2Asc)

    # build3 in die finale Datei 0 kopieren
    shutil.copy('build3', '0')
    os.remove(directory + "/0")
    os.remove(directory + "/1")
    shutil.copy('0', directory + '/0')
    shutil.copy('1', directory + '/1')

    print("Zero File '0' created successfully")

def helper():
    print("\n\nCopy your 0 and 1 files into the core folder\n1 -> Unpack one file\n2 -> convert it to png\n  -- edit your files --\n3 -> convert it back to rgb\n4 -> create zero file\n5 -> delete Temp files and directory")

def delete_one_directories():
    print("Removing temp files")
    for temp_file in ["build1", "build2", "build3", "0", "1"]:
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass
    header_dir = 'header'
    delete_hdr_files(header_dir)
    for root, dirs, files in os.walk("core"):
        for dir in dirs:
            if dir == 'one':
                dir_path = os.path.join(root, dir)
                shutil.rmtree(dir_path)
                print(f"Deleted directory: {dir_path}")

def main_menu():
    while True:
        print("1. Unpack ZIP Archive")
        print("2. Convert Core/Splash RGB to PNG")
        print("3. Convert Core/Splash PNG to RGB")
        print("4. Create Zero File")
        print("5. Delete Temp Files and Directories")
        print("9. Exit")
        print("10. Help")
        choice = input("Enter your choice: ")

        selected_dir = "core/"
        selected_dir2 = "core/one"

        if choice == '2':
            for name in glob.glob(os.path.join(selected_dir2, '*.rgb')):
                output_png_path = os.path.join(selected_dir2, os.path.splitext(os.path.basename(name))[0] + '.png')
                convert_rgba_to_png(name, output_png_path)
        elif choice == '3':
            for name in glob.glob(os.path.join(selected_dir2, '*.png')):
                rgb_output_path = os.path.join(selected_dir2, os.path.splitext(os.path.basename(name))[0] + '.rgb')
                convert_png_to_rgb(name, rgb_output_path)
        elif choice == '1':
            zip_path = os.path.join(selected_dir, "1")  # Path to the specific zip file
            unpack_zip(zip_path, os.path.join(selected_dir, "one"))
        elif choice == '4':
            create_zero_file(selected_dir)
        elif choice == '5':
            delete_one_directories()
        elif choice == '10':
            helper()
        elif choice == '9':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == '__main__':
    main_menu()
