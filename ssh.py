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
        # Create a new SSH session using "sudo -i" command
        # Invoke an interactive shell session
        shell = self.client.invoke_shell()

        # Send the "sudo -i" command to start a root shell
        shell.send('sudo -i\n')

        # Wait for the login process to complete
        import time
        time.sleep(1)  # Adjust the delay as needed
        output = shell.recv(65535).decode('utf-8')
        while 'password' in output.lower():
            password = 'xilinx\n'
            shell.send(password)
            time.sleep(1)  # Adjust the delay as needed
            output = shell.recv(65535).decode('utf-8')

        shell.send(f'source /etc/profile.d/pynq_venv.sh\n')

        # Wait for the command execution to complete
        time.sleep(1)  # Adjust the delay as needed
        output = shell.recv(65535).decode('utf-8')

        # Print the command output
        print(output)

        shell.send("cd /home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control\n")

        # Wait for the command execution to complete
        time.sleep(1)  # Adjust the delay as needed
        output = shell.recv(65535).decode('utf-8')

        # Print the command output
        print(output)

        # Execute commands with administrative privileges
        command = 'python '+path_filename+'.py'
        shell.send(f'{command}\n')

        # Wait for the command execution to complete
        time.sleep(10)  # Adjust the delay as needed
        output = shell.recv(65535).decode('utf-8')

        # Print the command output
        print(output)

        shell.close()

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
