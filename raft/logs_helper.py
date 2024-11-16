def find_logs_after_timestamp(file_path, given_timestamp):
    """
    Read the logs in reverse to find entries after a given timestamp.
    """
    logs_after = []
    last_index_ = -1  # The term after which sync is pending

    with open(file_path, 'r') as file:
        # Move to the end of the file
        file.seek(0, 2)
        position = file.tell()

        # Read backwards line by line
        while position > 0:
            # Move one character back and read it
            position -= 1
            file.seek(position)

            if file.read(1) == '\n':
                # Read the entire line
                line = file.readline().strip()
                if not line:
                    continue  # Skip any empty lines

                parts = line.split(' ', 2)
                if len(parts) != 3:
                    print("-Wrong format in log file entry")
                    print(line)
                    break

                timestamp = float(parts[0])
                last_index_ = timestamp
                
                # Check if this log is after the given timestamp
                if timestamp > given_timestamp:
                    logs_after.append(line)
                else:
                    break  # Stop if we have reached entries before the timestamp

        # Check if the first line is needed
        file.seek(0)
        first_line = file.readline().strip()
        if first_line:
            parts = first_line.split(' ', 2)
            if len(parts) != 3:
                print("[]Wrong format in log file entry")
                print(first_line)
                return last_index_, []

            timestamp = float(parts[0])
            last_index_ = timestamp
            if timestamp > given_timestamp:
                logs_after.append(first_line)

    # Since we read backwards, reverse the results to keep chronological order
    return last_index_, logs_after[::-1]



def get_last_log_timestamp(file_path):
    with open(file_path, 'rb') as file:
        # Seek to the end of the file
        file.seek(0, 2)
        position = file.tell()

        while position > 0:
            position -= 1
            file.seek(position)
            char = file.read(1)
            
            if char == b'\n':
                line = file.readline().decode().strip()
                if line:  # Check if the line is not empty
                    parts = line.strip().split(' ', 2)  # Split into [timestamp] [term_id] [command]
                    if len(parts) != 3:
                        print("Wrong format in log file entry")
                        print(line)
                        return -1

                    timestamp = float(parts[0])
                    return timestamp
        return -1

def get_last_log_term(file_path):
    with open(file_path, 'rb') as file:
        # Seek to the end of the file
        file.seek(0, 2)
        position = file.tell()

        while position > 0:
            position -= 1
            file.seek(position)
            char = file.read(1)
            
            if char == b'\n':
                line = file.readline().decode().strip()
                if line:  # Check if the line is not empty
                    parts = line.strip().split(' ', 2)  # Split into [timestamp] [term_id] [command]
                    if len(parts) != 3:
                        print("Wrong format in log file entry")
                        print(line)
                        return -1

                    timestamp = int(parts[1])
                    return timestamp
        return -1


def append_logs_to_file(file_path, logs):
    with open(file_path, 'a') as file: 
        for log in logs:
            file.write(log)
            file.write("\n") 

if __name__=="__main__":
    print(f"{get_last_log_timestamp('logs/40053.txt')=}")
    # print(f"{get_last_log_timestamp('logs/40052.txt')=}")
    # print(f"{get_last_log_timestamp('logs/40051.txt')=}")
    print(f"{find_logs_after_timestamp('logs/40051.txt', 1731694699.9758599)=}")
    # print(f"{find_logs_after_timestamp('logs/40052.txt', -1)=}")
    # print(f"{find_logs_after_timestamp('logs/40051.txt', -1)=}")