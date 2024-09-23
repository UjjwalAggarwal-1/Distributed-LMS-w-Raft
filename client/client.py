from grpc_client import LMSClient


def display_menu(logged_in):
    """Displays the menu options based on login status."""
    print("\n--- LMS Menu ---")
    if logged_in:
        print("1. Post")
        print("2. Get")
        print("3. Logout")
    else:
        print("1. Login")
    print("0. Exit")


def input_choice(options):
    """Ensure the input is one of the allowed options."""
    choice = input("Enter your choice: ")
    while choice not in options:
        print(f"Invalid choice! Please enter one of {', '.join(options)}")
        choice = input("Enter your choice: ")
    return choice


def post_menu():
    """Handles post type input and validation."""
    print("\nPost Types:")
    print("1. Assignment")
    print("2. Query")
    post_choice = input_choice(["1", "2"])
    post_type = "assignment" if post_choice == "1" else "query"
    content = input("Enter the content: ")
    return post_type, content


def get_menu():
    """Handles get type input and validation."""
    choice_map = {"1": "Course Material", "2": "Assignment", "3": "Query"}

    print("\nGet Types:")
    for key, value in choice_map.items():
        print(f"{key}. {value}")

    get_choice = input_choice(choice_map.keys())
    get_type = choice_map.get(get_choice).lower()

    return get_type


def main():
    client = LMSClient()
    logged_in = False
    token = None

    while True:
        display_menu(logged_in)
        if logged_in:
            choice = input_choice(["1", "2", "3", "0"])
        else:
            choice = input_choice(["1", "0"])

        if choice == "1":
            if not logged_in:
                # Login process
                username = input("Username: ")
                password = input("Password: ")
                try:
                    response = client.login(username, password)
                except Exception as e:
                    print(e)
                    break
                if response.status == "success":
                    token = response.token
                    logged_in = True
                    print(f"Login successful! Token: {token}")
                else:
                    print("Login failed. Please check your credentials and try again.")

            else:
                # Post data
                post_type, content = post_menu()
                try:
                    response = client.post(token, post_type, content)
                except Exception as e:
                    print(e)
                    break
                print(f"Post Status: {response.status}")

        elif choice == "2":
            # Get data
            get_type = get_menu()
            try:
                response = client.get(token, get_type)
            except Exception as e:
                print(e)
                break
            if response.status == "success" and response.data_items:
                print(f"\n--- {get_type.capitalize()} Data ---")
                for item in response.data_items:
                    print(f"ID: {item.id}, Content: {item.content}")
            else:
                print("No data found.")

        elif choice == "3":
            # Logout process
            try:
                response = client.logout(token)
            except Exception as e:
                print(e)
                break
            if response.status == "success":
                logged_in = False
                token = None
                print("Logout successful.")
            else:
                print("Logout failed.")

        elif choice == "0":
            # Exit the program
            try:
                response = client.logout(token)
            except Exception as e:
                pass
            print("Exiting the system.")
            break

        else:
            print("Unknown error, please restart the program")
            break


if __name__ == "__main__":
    main()
