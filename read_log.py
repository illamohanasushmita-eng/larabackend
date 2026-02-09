try:
    with open("verify_live_output_4.txt", "r", encoding="utf-16-le") as f:
        print(f.read())
except Exception as e1:
    try:
        with open("verify_live_output_4.txt", "r", encoding="utf-8") as f:
            print(f.read())
    except Exception as e2:
        print(f"Error reading file: {e2}")
