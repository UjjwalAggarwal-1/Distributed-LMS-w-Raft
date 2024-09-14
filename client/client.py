from grpc_client import LMSClient

def main():
    client = LMSClient()

    while True:
        print("\n1. Login\n2. Post\n3. Get\n4. Logout\n5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Username: ")
            password = input("Password: ")
            response = client.login(username, password)
            if response.status == "success":
                token = response.token
                print(f"Login successful. Token: {token}")
            else:
                print("Login failed.")

        elif choice == '2':
            post_type = input("Post Type (assignment/query): ")
            content = input("Content: ")
            response = client.post(token, post_type, content)
            print(response.status)

        elif choice == '3':
            request_type = input("Get Type (material/assignment/query): ")
            response = client.get(token, request_type)
            for item in response.data_items:
                print(f"{item.id}: {item.content}")

        elif choice == '4':
            response = client.logout(token)
            print(response.status)

        elif choice == '5':
            break

if __name__ == "__main__":
    main()
