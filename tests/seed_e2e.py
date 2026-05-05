import sys

# Add root directory to sys.path so we can import from database
from vpack import database


def seed_e2e_data():
    database.init_db()

    # 1. Create E2E Admin if not exists, or update password to known
    # Check if e2e_admin exists
    admin_user = database.get_user_by_username("e2e_admin")
    if not admin_user:
        new_id = database.create_user("e2e_admin", "admin123", "ADMIN", "E2E Admin")
        database.clear_must_change_password(new_id)
        print("Created e2e_admin")
    else:
        database.update_user_password(admin_user["id"], "admin123")
        database.clear_must_change_password(admin_user["id"])
        print("Updated e2e_admin")

    # 2. Create E2E Operator
    op_user = database.get_user_by_username("e2e_operator")
    if not op_user:
        new_id = database.create_user("e2e_operator", "operator123", "OPERATOR", "E2E Operator")
        database.clear_must_change_password(new_id)
        print("Created e2e_operator")
    else:
        database.update_user_password(op_user["id"], "operator123")
        database.clear_must_change_password(op_user["id"])
        print("Updated e2e_operator")

    # 3. Create E2E Station
    # Ensure there's a station for testing
    stations = database.get_stations()
    e2e_station = next((s for s in stations if s["name"].startswith("e2e_station")), None)
    if not e2e_station:
        station_id = database.add_station(
            {
                "name": "e2e_station_1",
                "ip_camera_1": "192.168.1.99",
                "ip_camera_2": "",
                "safety_code": "e2e_code",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        print(f"Created e2e_station_1 with ID {station_id}")
    else:
        print("e2e_station already exists")


def cleanup_e2e_data():
    database.init_db()

    # Remove e2e users
    for username in ["e2e_admin", "e2e_operator"]:
        u = database.get_user_by_username(username)
        if u:
            database.delete_user(u["id"])
            print(f"Deleted {username}")

    # Remove e2e stations
    stations = database.get_stations()
    for s in stations:
        if s["name"].startswith("e2e_station"):
            database.delete_station(s["id"])
            print(f"Deleted {s['name']}")

    # Remove e2e packing_videos
    # Actually, we should just let them stay or delete by waybill
    with database.get_connection() as conn:
        conn.execute("DELETE FROM packing_video WHERE waybill_code LIKE 'E2E_WAYBILL_%'")
        conn.commit()
    print("Deleted e2e packing_videos")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_e2e_data()
    else:
        seed_e2e_data()
