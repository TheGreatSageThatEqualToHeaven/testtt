import os
import time

# Time interval in seconds (e.g., 600 seconds = 10 minutes)
time_interval = 20

def git_push():
    try:
        # Add all changes
        os.system("git add .")

        # Commit changes with a message
        os.system('git commit -m "Auto commit from Replit"')

        # Push to the remote repository
        os.system("git push origin main")

        print("Changes pushed successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the auto commit every X seconds
while True:
    git_push()
    time.sleep(time_interval)
