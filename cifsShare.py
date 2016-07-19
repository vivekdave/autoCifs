import os
import sys
import subprocess
import pathlib
class cifsShare():
    def __init__(self, server = '',
                 share_name = '',
                 mount_folder = '',
                 username = '',
                 password = '',
                 chmod_user = '',
                 credential_file = '', # will be created in the chmod users homedir
                 mount_type='cifs',
                 dump_option=0,
                 pass_option=0,
                 create_mount_fld_as_sharename = True,
                 fstab_file_loc='/etc/fstab'
                ):
        self.server = server
        self.share_name = share_name
        self.mount_folder = mount_folder
        self.username = username
        self.password = password
        self.chmod_user = chmod_user
        self.mount_type = mount_type
        self.dump_option = dump_option
        self.pass_option = pass_option
        self.credential_file = credential_file
        self.fstab_file_loc = fstab_file_loc
        self.create_mount_fld_as_sharename = create_mount_fld_as_sharename
        self.start_comment_line = '#-start- Lines added below are added by the script named viv'
        self.end_comment_line = '#-end- Lines added below are added by the script named viv'

        if self.credential_file != '':
             self.create_cred_file()
        #self.verify_create_mount_folder()



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

    '''
    def verify_create_mount_folder(self):
        import pathlib
        mount_fld = pathlib.Path(self.mount_folder)
        print("1" + str(mount_fld))
        if self.create_mount_fld_as_sharename:
            if mount_fld.name == self.share_name:
                mount_fld = mount_fld.parent
            else:
                pass
        print("1" + str(mount_fld))
        if mount_fld.exists():
            if mount_fld.is_dir():
                if self.create_mount_fld_as_sharename and self.file_access(str(mount_fld), 'w'):
                    print("2 =" + str(mount_fld))
                    mount_fld = mount_fld.joinpath(self.share_name)
                    print("after join" + str(mount_fld))

                    if not mount_fld.exists():
                        mount_fld.mkdir()
                        self.mount_folder = str(mount_fld)
                        print("2 =" + str(mount_fld))
                        return True
                    else:
                        print("The Mount folder {0}, Exists".format(str(mount_fld)))
                        self.mount_folder = str(mount_fld)
                        return True
                else:
                    sys.exit("Cannot create directories inside :-" + str(mount_fld))
            else:
                sys.exit("The selected mount folder isin't a folder! :-" + str(mount_fld))
        else:
            sys.exit("The selected mount folder dosn't Exist! :-" + str(mount_fld))
    '''

    def verify_create_mount_folder(self):
        import pathlib
        mount_fld = pathlib.Path(self.mount_folder)
        print("mount_fld="+str(mount_fld))
        if self.create_mount_fld_as_sharename:
            if mount_fld.name == self.share_name:
                pass
            else:
                mount_fld = mount_fld.joinpath(self.share_name)
        print("after create share name check mount_fld=" + str(mount_fld))
        if mount_fld.exists():
            print("inside mount_fld.exists mount_fld=" + str(mount_fld))
            if not os.path.ismount(str(mount_fld)):
                return True
            else:
                print("inside else (ismount is true) mount_fld=" + str(mount_fld))
                print("Something already mounted on the mount folder!! Unmounting and retrying")
                connection_string = list()
                connection_string.append('umount')
                connection_string.append(str(mount_fld))

                try:
                    output = subprocess.check_call(connection_string, stderr=subprocess.STDOUT, timeout=4)
                except subprocess.CalledProcessError as e:
                    print("returncode: --: " + str(e.returncode))
                    print("output:  " + output)
                    errorcode = e.returncode

                print(output)
                if output == 0:
                    print("UMount Sucessful!!!!, mounting")
                    return True
                else:
                    return False
        else:
            try:
                mount_fld.mkdir()
            except exception as e:
                print("Cannot Create the Mount Folder")
                sys.exit(1)
            finally:
                return True

    def get_mount_folder(self):
        mount_fld = pathlib.Path(self.mount_folder)
        if self.create_mount_fld_as_sharename:
            return str(mount_fld.joinpath(self.share_name))
        else:
            return self.share_name

    def create_options_string(self):
        op_str = list()
        if self.chmod_user != '':
            op_str.append('uid='+self.chmod_user)

        if self.credential_file == '':
            if self.username != '' and self.password != '':
                op_str.append('username='+self.username+',password='+self.password)
        else:
            op_str.append('credentials='+self.create_cred_file())

        return ",".join(op_str)

    def create_cred_file(self):
        if self.credential_file != '':
            import pathlib, pwd, stat
            try:
                usr = pwd.getpwnam(self.chmod_user)
            except Exception as e:
                sys.exit("The user: "+self.chmod_user+" was not found in the user database")

            user_home_dir = usr.pw_dir
            user_home_dir = pathlib.Path(user_home_dir)
            user_home_dir = user_home_dir.joinpath(self.credential_file)

            try:
                f = open(str(user_home_dir), 'w')
                f.write('username=' + self.username)
                f.write('\n')
                f.write('password=' + self.password)
                f.write('\n')
                f.write('domain=workgroup')
                f.write('\n')
            finally:
                f.close()

            try:
                os.chown(str(user_home_dir), usr.pw_uid, usr.pw_gid)
                os.chmod(str(user_home_dir),600)
            except Exception as e:
                print("Could not alter the credentials files permissions")
                print(e)
                sys.exit(1)

            return str(user_home_dir)
        else:
            sys.exit("The Credential file to create and use not supplied!")

    def create_fstab_entries(self):
        strin = ""
        strin += "//" + self.server + "/" + self.share_name
        strin += "\t" + str(self.get_mount_folder())
        strin += "\t" + self.mount_type
        strin += "\t" + self.create_options_string()
        strin += "\t" + str(self.dump_option) + "\t" + str(self.pass_option)
        return strin

    def add_fstab_entries(self):

        '''
            Checks of the file self.fstab_file_loc has the entries of start and end lines that the script add
            when it edits the file.
            :return: if both the start and end text comment lines are found
            :rtype: int(startline#) , int(endline#)
            '''
        ''' True DO
        get all lines from fstab
        search for start line and end line comments
        get a hold of other lines asto readd them safely

        get ll the entries of shares between the comment lines
        compare and check of the current share is added in the fstab shares and remeve it and re add it
        '''
        # -Start- Get the start comment line# and the End Comment line#
        print("inside add_fstab_entries")
        startline = int()  # records the line# where the start comments is
        endline = int()  # records the line# where the end comments is
        if self.file_access(self.fstab_file_loc, 'w'):
            print("inside inside file access check")
            # open the file and read all the lines in the lines var
            try:
                f = open(self.fstab_file_loc, 'r')
                lines = f.readlines()
            except Exception as e:
                sys.exit("cannot open fstab for reading!!")
            finally:
                f.close()

            # loop through the lines and search for the start comment and end comment and record the line #
            # in the startline and endline vars
            for line in range(len(lines)):
                str_line = lines[line]
                str_line = str_line.strip('\n')
                if str_line == self.start_comment_line:
                    startline = line
                elif str_line == self.end_comment_line:
                    endline = line

                line = line + 1
            # -End- Get the start comment line# and the End Comment line#

            # -start- remove the lines between start an end comment including the comment

            if startline >= 0 and endline > 0:
                fstab_shares = list()
                for shr in range(startline+1,endline):
                    share = lines[shr].split(sep='\t', maxsplit=6)
                    fstab_shares.append(share)
                    if share[1] == self.get_mount_folder():
                        print("Fstab already includes a mountpoint at: " + self.mount_folder + "updating the entry ")
                        lines[shr] = self.create_fstab_entries()
                        print("inside if " + str(fstab_shares))
                    else:
                        print("didnt find the entry in the fstab between comments, hence adding new")
                        lines.insert(endline -1, self.create_fstab_entries() +'\n')
                        print("inside else " + str(fstab_shares))
                #lines.insert(endline, self.create_fstab_entries())
            else:
                fstab_shares = list()
                lines.append('\n\n')
                lines.append(self.start_comment_line+'\n')
                lines.append(self.create_fstab_entries()+'\n')
                lines.append(self.end_comment_line+'\n')
                print("no comment line found hence adding with comments" + str(lines))

            # write the new fstab file

            try:
                f = open(self.fstab_file_loc, 'w')
                f.writelines(lines)
                '''
                for ln in range(len(lines)):
                    f.write(lines[ln])
                    f.write('\n')
                '''
            except Exception as e:
                sys.exit("cannot open fstab for Writing !!:- "+str(e))
            finally:
                f.close()

            # -End- remove the lines between start an end comment including the comment
        else:
            print("write access denied to fstab file: - " + self.fstab_file_loc)

    def create_mount_cmd(self):
        #sudo mount -t cifs -o username=yourusername,password=yourpassword //WindowsPC/share1 /mnt/mountfoldername
        # Creates a command for to use with subprocess
        connection_string = list()
        connection_string.append('mount')
        connection_string.append('-t')
        connection_string.append(self.mount_type)
        connection_string.append('-o')
        connection_string.append(self.create_options_string())
        connection_string.append("//" + self.server + "/" + self.share_name)
        connection_string.append(self.get_mount_folder())
        return connection_string

    def run_mount_cmd(self):
        if self.verify_create_mount_folder():
            print("inside verify mount folder")
            '''
                Run the command and get the output to a var output and decode to utf-8 from bytes
                '''
            process_mount_cmdlets = self.create_mount_cmd()
            try:
                print("inside try block")
                output = subprocess.check_call(process_mount_cmdlets, stderr=subprocess.STDOUT, timeout=4)
            except subprocess.CalledProcessError as e:
                print("inside except block")
                print("returncode: --: " + e.returncode)
                print("output:  " + output)
                errorcode = e.returncode

            print("compleate try-except block   ")
            if output == 0:
                print("Mount Sucessful!!!!")
            else:
                print("could not mount th Filesystem !!!!")
        else:
            print("could not verify_create mount Diectory!")
            sys.exit(1)