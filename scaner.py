#! /usr/bin/python3
from config import *
import sys,re,json, os,subprocess


def create_directory(directory):
    print("Creating directory:", bcolors.OKBLUE, directory, bcolors.ENDC)
    while os.path.exists(directory):
        c = input(f"source file direct already exists, replace it, save as another name or {bcolors.WARNING}cancel{bcolors.ENDC}?(r/s/{bcolors.WARNING}C{bcolors.ENDC})")
        if c == 'r':
            shutil.rmtree(directory)
        elif c == 's':
            directory = directory + "_1"
            print("Creating directory:", bcolors.OKBLUE, directory, bcolors.ENDC)
        else:
            sys.exit(bcolors.FAIL + "cancel" + bcolors.ENDC)
    os.makedirs(directory)

def write_files(codes, contract_name, base_dir):
    if (codes[0] == '{'):
        if codes[1] == '{':
            codes = json.loads(codes[1:-1])['sources']
        else:
            codes = json.loads(codes)

        for i in codes:
            raw_code = codes[i]['content']
            data = re.sub(r".*import.*['\"](?P<filename>.*\.sol)['\"]", import_replace, raw_code)

            filename = os.path.join(base_dir, os.path.basename(i))
            print("Writing file:", bcolors.OKBLUE, filename, bcolors.ENDC)
            with open(filename, "w") as f:
                f.write(data)
    else:
        each_files = re.findall(r"\/\/ File ([\s\S]*?\.sol)(?:.*)([\s\S]*?)(?=\/\/ File|$)", codes)
        each_parts = re.findall(r"pragma\s+solidity([\s\S]*?)(?=\/\/ File|$)", codes)


        if len(each_files) != len(each_parts):
            print(bcolors.FAIL + "Something error, writing as single file" + bcolors.ENDC)
        if len(each_files) == 0 or len(each_files) != len(each_parts):
            full_filename = os.path.join(base_dir, contract_name+".sol")
            print("Writing file:", bcolors.OKBLUE, full_filename, bcolors.ENDC)
            with open(full_filename, "w") as f:
                f.write(codes)
            return

        last_file = ""
        for (filename, code) in each_files:
            full_filename = os.path.join(base_dir, os.path.basename(filename))
            print("Writing file:", bcolors.OKBLUE, full_filename, bcolors.ENDC)
            with open(full_filename, "w") as f:
                f.write((f"import \"./{last_file}\";\r\n" if last_file else "") + code.strip("\r\n"))

            last_file = os.path.basename(filename)


def ScanCode(contract):

    global contract_address
    global chain_id

    chain_id = ChainId.ETHEREUM
    contract_address = contract

#Get Data
    curlurl = RPC_ENDPOINTS['getsourcecode'].format(BROWSER_URL[chain_id], contract_address, API_KEY[chain_id])
    curl = "curl '"+ curlurl +"'"

    output = subprocess.check_output(curl, shell=True)

    json_object = json.loads(output)

#Compiler 
    CompilerVersion = json_object['result'][0]['CompilerVersion']

    if(CompilerVersion == ""):
        print("Not Source code")
        return 0

    NumRegex = re.compile(r'[0-9]\.?[0-9]*\.?[0-9]*')
    GetCompiler = NumRegex.search(CompilerVersion)

    CompilerVersion = GetCompiler.group()

#SetCompiler
    solc = "solc-select use " + CompilerVersion
    os.system(solc)

#Download
    contract_name = json_object['result'][0]['ContractName']
    codes = json_object['result'][0]['SourceCode']
    base_dir = os.path.join(os.getcwd(), "contracts", contract_name)

    create_directory(base_dir)  # create directory: ./contracts/{contract name}
    write_files(codes, contract_name, base_dir)

#RunScaner
    postRun = 'cd contracts/' + contract_name + ' && '
    detect =' --detect reentrancy-eth'
    slither = postRun + "slither ." + detect
    os.system(slither)

#Clear
    os.system('rm -rf contracts/*')

def main():
    Live = False
    fp = open('datadump.json')
    data = json.load(fp)

    for id  in data['data']:
        platform = id['platform']
        if(platform != None):
            if(platform['name'] == "Ethereum"):
                address = platform['token_address']
                if(address == '0x6ba460ab75cd2c56343b3517ffeba60748654d26' or Live == True):
                    Live = True
                    print(address)
                    ScanCode(address)
    fp.close()

if __name__=="__main__":
    main()
