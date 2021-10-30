
import glob
import sys
import hashlib
import os
import time
import threading
from multiprocessing import Process, Pool, Value, cpu_count
import platform


class File:
    def __init__(self, baseName, location):
        self.count = 1
        self.baseName = []
        self.location = []

        self.baseName.append(baseName)
        self.location.append(location)

    def add_file(self, baseName, location):
        self.count += 1
        self.baseName.append(baseName)
        self.location.append(location)

    def __str__(self):
        return f'File {self.baseName}: @{self.location}\n'

    def __repr__(self):
        return f'Files {self.baseName}: @{self.location}\n'


WRITE_FILE = None
BUF_SIZE = 65536
DEBUG = True


def File_Hash(file):
    sha1 = hashlib.sha1()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def Files_Digest(files):
    # hashesDict = {}
    filesDict = {}

    for file in files:
        fileHash = File_Hash(file)
        fileBaseName = os.path.basename(file)
        if fileHash not in filesDict.keys():
            # hashesDict[file] = fileHash
            newFile = File(fileBaseName, file)
            filesDict[fileHash] = newFile
        else:
            oldFile = filesDict.get(fileHash)
            oldFile.add_file(fileBaseName, file)
    print("done")
    return filesDict


def Files_Check_Duplicate(fileLocation, filesDict):
    i = 0
    with open((fileLocation+"/Debugging.txt"), "a+") as w:
        w.write(
            "---Duplicate Files: for Folder ({file})---\n".format(file=fileLocation))
        for file in filesDict.values():
            if file.count > 1:
                w.write(str(file)+"\n")
                i += 1
        w.write("Total of {total} Files were Found\n".format(total=i))


def Files_Compare(firstDict, secondFiles):
    print("Comparing Files")
    with open("FilesNotInSecond.txt", "w") as w:
        for file in secondFiles:
            fileHash = File_Hash(file)
            fileBaseName = os.path.basename(file)
            if fileHash not in firstDict:
                w.write("File: {filebase} \t\tLocation: {location}\n".format(
                    fileBaseName, fileHash))

    return


def console():
    firstFolder = ""
    secondFolder = ""
    firstDig = {}
    secondDig = {}
    usrInput = ""
    Console = '''
    First Folder = ({})
    Second Folder = ({})

    1) Set The First Folder
    2) Set The Second Path
    3) Check For Duplicates on First File
    4) Check For Duplicates on Second File
    5) Compare First Path with Second Path to Find Differnces
    6) Quit
    Please Enter a number:\n
    '''
    MYOS = platform.system()
    while (True):
        if firstFolder != "" and secondFolder != "":
            print(Console.format(firstFolder, secondFolder))
        else:
            print(Console)
        usrInput = input()
        if usrInput == "1":
            print("Enter The First Folder Name:\n")
            firstFolder = input()
            if os.path.exists(firstFolder) != True:
                firstFolder = None
                print("Folder Doesn't exists! Try again\n")
                break
            else:
                print("Folder exists!\n")

        elif usrInput == "2":
            print("Enter The Second Folder Name:\n")
            secondFolder = input()
            if os.path.exists(firstFolder) != True:
                secondFolder = None
                print("Folder Doesn't exists! Try again\n")
                break
            else:
                print("Folder exists!\n")

        elif usrInput == "3":
            # "/Users/samuel/Documents/Python3/FileHandling/**/*.*", recursive=True)
            if firstFolder != "":
                firstFiles = glob.glob(
                    firstFolder + "/**/*.*", recursive=True)
                firstDig = Files_Digest(firstFiles)
                Files_Check_Duplicate(firstFolder, firstDig)
                print("Size is ", sys.getsizeof(firstDig))
            else:
                print("First Folder is empty")
        elif usrInput == "4":
            if secondFolder != "":

                SecondFiles = glob.glob(
                    secondFolder + "/**/*.*", recursive=True)
                # "/Users/samuel/Documents/Python3/FileHandling/**/*.*", recursive=True)
                secondDig = Files_Digest(SecondFiles)
                Files_Check_Duplicate(secondDig)
                print("Size is ", sys.getsizeof(secondDig))
            else:
                print("No Second Folder Name")
        elif usrInput == "5":
            if firstFolder != "" and secondFolder != "":
                print("Working on It")
                Folder_Main(firstFolder, secondFolder)
                print("Done With The Compare")
            else:
                print("Both First Folder and Second Folder need to be filled")

        elif usrInput == "6":
            print("GoodBye!\n")
            break


def log(outputSTR):
    if DEBUG:
        wf = open(os.getcwd()+"/Debugging.txt", "a+")
        wf.write(outputSTR)
        wf.close()


def Process_Dir(mainFolder):
    Folders = glob.glob(mainFolder + "/**/", recursive=True)

    dictFolders = {}
    for folder in Folders:
        if folder in dictFolders:
            log("Error folders are named the same: {}\n".format(folder))
        else:
            dictFolders[os.path.dirname(folder)] = folder

    return dictFolders


def Folder_Main(firstFolderLocation, secondFolderLocation):
    fdictFolders = Process_Dir(firstFolderLocation)
    sdictFolders = Process_Dir(secondFolderLocation)

    folders = []
    for folder in fdictFolders.keys():
        if folder in sdictFolders.keys():
            combined = tuple([fdictFolders[folder], sdictFolders[folder]])
            folders.append(combined)
        else:
            log("NotFound: File Name ({}) was in one Location and not the other. Location: ({})".format(
                folder, sdictFolders[folder]))
    print(folder)
    with Pool() as pool:
        pool.starmap(Folder_Processing, folders)
        # print(res)


def Folder_Processing(fdictFolders, sdictFolders):
    fFiles = glob.glob(fdictFolders + "/*.*")
    sFiles = glob.glob(sdictFolders + "/*.*")

    fdic = Files_Process(fFiles)
    Check_For_Needing_Update(fdic, sFiles)


def Files_Process(Files):
    dicFiles = {}
    for file in Files:
        hash = File_Hash(file)
        baseName = os.path.basename(file)
        if hash not in dicFiles:
            newFile = File(baseName, file)
            dicFiles[hash] = newFile
        else:
            oldFile = dicFiles.get(hash)
            oldFile.add_file(baseName, file)
    return dicFiles


def Check_For_Needing_Update(fDict, sFiles):
    # log("---- Section: Comparing Files with Both Files ----\n")
    sDict = {}  # [base, FileLocation]
    for file in sFiles:
        base = os.path.basename(file)
        sDict[base] = file

    for firstHash, file in fDict.items():
        if file.count > 1:
            log("Duplicate Files: {} Files have the same data but differn't File Names({}) \n".format(
                file.count, file))
        else:
            for base in file.baseName:
                if base in sDict.keys():
                    secondHash = File_Hash(sDict.get(base))
                    if firstHash != secondHash:
                        log("Update: OutDated file might need to be updated ({})".format(
                            file.location))


def main():
    # /Users/samuel/Documents/Python3/FileHandling"
    console()


if __name__ == '__main__':

    print('starting main')
    main()
    print('finishing main')
