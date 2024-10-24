def find_logs_after_timestamp(file_path, given_timestamp):
    """
    read the logs in reverse, linearly
    """

    logs_after = []
    last_term = -1 ## the term after which sync is pending
    
    with open(file_path, 'r') as file:

        # Move to the end of the file
        file.seek(0, 2)
        position = file.tell()

        while position > 0:
            file.seek(position - 1)
            char = file.read(1)

            # If we find a newline, read the line
            if char == '\n':
                line = file.readline().strip()
                if line=="":
                    position -=1
                    continue
                parts = line.split(' ', 2) 
                if len(parts) != 3:
                    print("Wrong format in log file entry")
                    print(line)
                    break

                timestamp = float(parts[0]) 
                
                if timestamp > given_timestamp:
                    logs_after.append(line)
                else:
                    last_term = int(parts[1])
                    break

            position -= 1

    # Since we read backwards, we need to reverse the result
    return last_term, logs_after[::-1]


def get_last_log_timestamp(file_path):
    with open(file_path, 'rb') as file:
        file.seek(0, 2)  # Move to the end of the file
        if file.tell() == 0:
            return None
        file.seek(-2, 2)  # Move the pointer to the second last byte (skip EOF)
        while file.read(1) != b'\n':  # Move backwards until you find the newline character
            file.seek(-2, 1)  # Move pointer backwards by 2 bytes

        last_line = file.readline().decode()  # Read the last line
        parts = last_line.strip().split(' ', 2)  # Split the line into [timestamp] [term_id] [command]
        if len(parts) != 3:
            print("Wrong format in log file entry")
            print(last_line)
            return
        timestamp = float(parts[0]) 
        return timestamp


def append_logs_to_file(file_path, logs):
    with open(file_path, 'a') as file: 
        for log in logs:
            file.write(log) 