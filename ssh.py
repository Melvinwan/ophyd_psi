import paramiko

class SSH:
    def __init__(self,hostname,username, password, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port=port

        # Create an SSH client
        client = paramiko.SSHClient()
        client.load_system_host_keys()  # Load known host keys from the system
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add unknown hosts

        self.client=client

    def connect(self):
        # Connect to the remote server
        self.client.connect(self.hostname, self.port, self.username, self.password)

    def run_code(self,path_filename):
        # Command to execute on the remote server
        command = 'python '+path_filename+'.py'

        # Execute the command
        stdin, stdout, stderr = self.client.exec_command(command)

        # Get the output and error messages (if any)
        output = stdout.read().decode()
        errors = stderr.read().decode()

        # Print the output and errors
        print('Output:')
        print(output)
        print('Errors:')
        print(errors)

    def transfer_file(self,path_target_file,path_remote_file):
        # Open an SFTP session
        sftp = self.client.open_sftp()

        # Upload the file
        sftp.put(path_target_file, path_remote_file)

        # Close the SFTP session
        sftp.close()

    def download_file(self, remote_path, local_path):
        sftp = self.client.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()

    def disconnect(self):
        # Close the SSH connection
        self.client.close()


# test = SSH("129.129.131.153", "xilinx", "xilinx")
# test.connect()
# test.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/config.json",r"config.json")
# test.transfer_file(r"config.json",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/config.json")
# test.disconnect()
