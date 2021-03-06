import types
import paramiko
import argparse

from paramiko.client import SSHClient


def exec_command(client: SSHClient):
    """
    Executes commands on the server
    :param client: SSH Connection Object
    """

    _, stdout, stderr = client.exec_command(args.cmd)
    output = stdout.readlines() + stderr.readlines()

    # client._host_keys._entries[0].hostnames[0]

    if output:
        print(f"OUTPUT:")
        for line in output:
            print(line)


def upload_file(client: SSHClient):
    """
    Uploads the file to the server
    :param client: SSH Connection Object
    """

    sftp_client = client.open_sftp()
    sftp_client.put(localpath=args.file, remotepath=args.file)
    sftp_client.close()
    print("File uploaded")


def download_file(client: SSHClient, file_number: int):
    """
    Downloads the file from the server
    :param client: SSH Connection Object
    :param file_number: File number
    """
    sftp_client = client.open_sftp()

    try:
        sftp_client.get(localpath=f"{file_number}{args.file}", remotepath=args.file)
        file_number += 1
    except FileNotFoundError:
        print("File not found")

    sftp_client.close()


def connect():
    """Connects to the server"""

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if args.hosts_file:
        with open(args.hosts_file, "r") as file:
            for line in file:
                host_info = line.split(":")

                if len(host_info) == 3:  # If port isn't specified
                    client.connect(
                        hostname=host_info[0], port=args.port, username=host_info[1], password=host_info[2].rstrip('\n')
                    )
                if len(host_info) == 4:  # If port is specified
                    client.connect(
                        hostname=host_info[0], port=int(host_info[1]), username=host_info[2],
                        password=host_info[3].rstrip('\n')
                    )

                print(f"Connected to {host_info[0]}")
                yield client
    else:
        client.connect(
            hostname=args.ip, port=args.port, username=args.username, password=args.password.rstrip('\n')
        )

        print(f"Connected to {args.ip}")
        yield client


if __name__ == "__main__":
    usage_example = """
    Usage Example:
        python3 ssh_cmd.py -hf hosts.txt -f test.txt -m upload
        python3 ssh_cmd.py -i 192.168.80.128 -u username -p password -f test.txt -m upload
        python3 ssh_cmd.py -hf hosts.txt -c whoami -m exec
        python3 ssh_cmd.py -i 192.168.80.128 -u username -p password -c whoami -m exec
    """

    # TODO: Argparse using subparsers
    parser = argparse.ArgumentParser(epilog=usage_example, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hosts_file", "-hf", help="File with servers and credentials.\n"
                                                    "Hosts file example: ip:username:password")
    parser.add_argument("--cmd", "-c", help="Command that will be executed on the server")
    parser.add_argument("--port", help="SSH Port (Default: 22)", default=22)
    parser.add_argument("--mode", "-m", help="Action", choices=["exec", "upload", "download"])

    args, _ = parser.parse_known_args()

    if args.hosts_file is None:
        parser.add_argument("--ip", "-i", help="Server IP", required=True)
        parser.add_argument("--username", "-u", help="User on the server", required=True)
        parser.add_argument("--password", "-p", help="Password for the user on the server", required=True)

    if args.mode == "upload" or args.mode == "download":
        parser.add_argument("--file", "-f", help="File to upload to the server", required=True)

    args = parser.parse_args()
    ssh_connection = connect()

    if args.mode == "exec":
        if isinstance(ssh_connection, types.GeneratorType):
            for connection in ssh_connection:
                exec_command(client=connection)

    elif args.mode == "upload":
        if isinstance(ssh_connection, types.GeneratorType):
            for connection in ssh_connection:
                upload_file(client=connection)

    elif args.mode == "download":
        if isinstance(ssh_connection, types.GeneratorType):
            for number, connection in enumerate(ssh_connection):
                download_file(client=connection, file_number=number)
