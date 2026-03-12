import requests

BASE_URL = "http://localhost:8000"
EMAIL = "ashishkumar93040086@gmail.com"
PASSWORD = "agent@123"

def test_login():
    print(f"Testing login for {EMAIL}...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": EMAIL, "password": PASSWORD}
        )
        if response.status_code == 200:
            print("Login successful!")
            token = response.json()
            print(f"Token: {token['access_token'][:10]}...")
            return token['access_token']
        else:
            print(f"Login failed: {response.status_code}")
            print(response.json())
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_logout():
    print("Testing logout...")
    try:
        response = requests.post(f"{BASE_URL}/auth/logout")
        if response.status_code == 200:
            print("Logout successful!")
            print(response.json())
        else:
            print(f"Logout failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure server is running (it should be from previous background command)
    # If not, this will fail
    token = test_login()
    if token:
        test_logout()
