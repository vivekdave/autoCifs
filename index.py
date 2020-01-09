author = 'Vivek Dave'
import logging
import cifsShare

import logging
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler('log.log')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


rootLogger.setLevel(logging.DEBUG)


class autoMountCifs():
    import pathlib
    def __init__(self, server,
                 username,
                 password,
                 chmod_user,
                 skip_shares_description = ['Remote Admin', 'Default share', 'Remote IPC'],
                 cred_file_name = ".autocifsmountcredfile",
                 fstab_loc = '/etc/fstab',
                 mount_folder = '/media'
                 ):
        self.server = server
        self.username = username
        self.password = password
        self.user = chmod_user
        self.cred_file = cred_file_name
        self.fstab_file_loc = fstab_loc
        self.mount_folder = mount_folder
        self.skip_shares_disc = skip_shares_description

        self.all_shares = '' #this will be filled with all the shares returned from the server (self.find_all_shares)

    def find_all_shares(self):
        '''
        :return: list of Dict as below

        {
            'filesystem': '',
            'share_name': ''
            'mount_folder': '',
            'mount_type': '',
            'options_string': '',
            'dump_option': 1,
            'pass_option': 1
        },
        '''

        #Creates a command (smbclient to get list of shares from a server) for to use with subprocess
        connection_string = list()
        connection_string.append('smbclient') #Command Name
        connection_string.append('-L=' + self.server) #This option allows you to look at what services are available on a server.
        connection_string.append('-g') # Gerp able list so as we can string process it
        connection_string.append('-U=' + self.username + '%' + self.password) # Username and Password
        connection_string.append('-t=' + '10') #This allows the user to tune the default timeout used for each SMB request. The default setting is 20 seconds.

        #Run the command and get the output to a var output and decode to utf-8 from bytes
        try:
            logging.info("Running the smbclient to list all the shares from a server")
            output = subprocess.check_output(connection_string, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error("Could Not connect to the Server ! while running the smbclient command, Exiting | Returncode= ",e.returncode)
            errorcode = e.returncode
        finally:
            if not 'errorcode' is locals(): #Check if the variable errorcode is set in the except block above
                output = output.decode()
            else:
                sys.exit(1)

        ## store all the shares found on the server
        all_shares = list()

        '''
        search every line of the returned output from smbclient for a '|' character
        it means that its a share that we need to process the line and we split it and create a list
        once we find it we add the share list to the list all_shares
        '''
        # creates a list like ['Type','Sharename','Comment']   e.g.['Disk', '3tb', '']
        for line in output.splitlines():
            if line.find('|') != -1:
                all_shares.append(line.split('|'))



        '''
        the first for loop is for each description that we need to skip (Remove from the collected share lists)
        the second for loop goes through each share in the all_shares list
        in this loop we check of the description of each share matched the skip description and remove it from the mail all_shares list
        '''
        # Remove all shares whose comment matches in one of the self.skip_shares_disc list
        for skip in self.skip_shares_disc:
            for share in all_shares[:]:
                if str(share[2]).upper() == str(skip).upper():
                    all_shares.remove(share)

        '''
        {
            'filesystem': '',
            'share_name': ''
            'mount_folder': '',
            'mount_type': '',
            'options_string': '',
            'dump_option': 1,
            'pass_option': ''
        },
        '''
        # Reformat the list of shares to a Dictonary
        new_all_shares = []

        for share in all_shares:
            shr = cifsShare.cifsShare(server=self.server,
                            share_name=share[1],
                            mount_folder=self.mount_folder,
                            username=self.username,
                            password=self.password,
                            chmod_user=self.user,
                            credential_file=".autocifsmountcredfile"
                            )
            new_all_shares.append(shr)

        self.all_shares = new_all_shares
        return new_all_shares

    def display_share_selection(self,shares):
        print("\n" * 100)
        print("{:<3}".format("Sr: ") + " |  " + "{:>10}".format("Share"))
        print("{:<3}".format("----") + "    " + "{:>10}".format("-----"))
        for share in range(len(shares)):
            print("{:<3}".format(share) + "  |  " + "{:>10}".format(shares[share].share_name))
        print("\n" *2)
        print("Which of the above drives would you like to auto mount ?")
        print("\n" * 1)
        print("Selection can be a comma separated options E.g.: 0,2,3 etc. ")
        selection = input("Your Selection:- ")
        selection = selection.split(',')
        selection = [int(i) for i in selection]
        for sel in selection:
            if not (int(sel) <= (len(shares) - 1) and int(sel) >= 0):
                print("Your Selection out of options displayed ! ")
                if query_yes_no("Do you want to try again ?"):
                    os.system('clear')
                    selection = self.display_share_selection(shares)

        return (selection)

import subprocess
import pprint
import sys
import os

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def ask_query(question):
    print('\n'*5)
    print(str(question)," :")
    return input("$$:-  ")


def Get_Info_and_Create_vars():


    global server
    global username
    global password
    global user #chmod user
    global cred_file
    global mount_folder
    global create_mount_fld_as_sharename
    global fstab_loc

    server = ask_query("Please enter the Sever's Hostname or IP: ")
    username = ask_query("Please enter the username to use for auth: ")
    password = ask_query("Please enter the password to use for auth: ")
    user = ask_query("Please enter the username who needs R/W access to the mounts")
    cred_file = ask_query("please enter the file name for credential file in /home/user/.smbcredentials\n If Left Empty will specify credentials in the fstab file directly")
    create_mount_fld_as_sharename = bool(query_yes_no("Do you wnat to create a folder with the share name and mount"))
    mount_folder = ask_query("please specify the folder where you want to mount the share")
    fstab_loc = ask_query("Enter the fstab file location (Default: /etc/fstab) ")

'''
    server = '192.168.1.2'
    username = "vivek"
    password = "adw31"
    user = 'vivek'
    cred_file = '/home/' + user.strip() + "/.smbcredentials"
'''

def get_info_via_dialog():
    global server
    global username
    global password
    global user  # chmod user
    global cred_file
    global mount_folder
    global create_mount_fld_as_sharename
    global fstab_loc

    from dialog import Dialog
    d = Dialog(dialog="dialog")

    button_names = {d.OK: "OK",
                    d.CANCEL: "Cancel",
                    d.HELP: "Help",
                    d.EXTRA: "Extra"}


    code, tag = d.mixedform("What sandwich toppings do you like?",
                             [("Server", 1, 1, "",1, 10, 20, 20, 0),
                              ("Username", 2, 1, "",2, 10, 20, 20, 0),
                              ("Password", 3, 1, "", 3, 10, 20, 20, 1)
                              ]
                )
    import pprint
    pprint.pprint(code)
    pprint.pprint(tag[1])

    if tag[0] != '' and tag[1] != '' and tag[2] != '':
        server = tag[0]
        username = tag[1]
        password = tag[2]
    else:
        sys.exit("Please specify all the input box's")

    code, tag = d.inputbox("Please enter the username who will have R/W access to the mounts")

    pprint.pprint(code)
    pprint.pprint(tag)

    #need to add checks for user
    user = tag

    code, tag = d.inputbox("Please enter the filename only, it will be edited to add the username and password\n and will be user in fstab or mount cmd")
    if tag != '':
        cred_file = tag


    code, tag = d.fselect('/etc/fstab')
    if tag != '':
        fstab_loc = tag

    import pathlib

    code, tag = d.dselect('/media')
    if tag != '' and pathlib.Path(tag).is_dir():
        mount_folder = tag
    else:
        sys.exit("Please select a folder to mount!")

    pprint.pprint(code)
    pprint.pprint(tag)
    #code, tag = d.inputbox("Please enter the fstab file path ", init="/etc/fstab")

def file_access(self, file, access='r'):
    '''
    :Desc: this function returns if the sprcifies permission is allowed to this script
    :param access: r = read; w=write; f=exists
    :type access: string
    :return: true / false
    :rtype: bool
    '''
    if access == 'r':
        ret = os.access(file, os.R_OK)
        return ret
    elif access == 'f':
        ret = os.access(file, os.F_OK)
        return ret
    elif access == 'w':
        ret = os.access(file, os.W_OK)
        return ret
        # Check if there are entries added by this scritp


def main():
    get_info_via_dialog()

    #Get_Info_and_Create_vars()
    fstab_file = '/home/vivek/test_fstab'
    '''
    cifsmount=autoMountCifs('192.168.1.2', 'vivek', 'password', 'vivek',
                            skip_shares_description = ['Remote Admin', 'Default share', 'Remote IPC'],
                            cred_file_name = '.autocifsmountcredfile', fstab_loc = fstab_file,
                            mount_folder = '/media')
    '''
    print(fstab_file)
    cifsmount = autoMountCifs(server=server,username=username, password=password, chmod_user=user, fstab_loc=fstab_file)

    shares = cifsmount.find_all_shares()

    selection = cifsmount.display_share_selection(shares)


    for sel in selection:
        print("=======")
        #print(shares[sel].add_fstab_entries())
        shares[sel].run_mount_cmd()
        # print(shares[sel].create_cred_file())
        # print(shares[sel].create_mount_cmd())
        print("=======")
        # print(shares[sel].create_fstab_entries())


if __name__ == '__main__':
    main()
