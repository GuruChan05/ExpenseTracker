from datetime import datetime, timedelta

from database import (
    initialize_database,
    get_last_update
)

from update_expenses import run_update


UPDATE_INTERVAL_DAYS = 14


def should_update():

    last_update = get_last_update()

    if last_update is None:

        print("No previous update found.")

        return True

    try:

        last_datetime = datetime.fromisoformat(
            last_update
        )

    except ValueError:

        print("Invalid previous update date.")

        return True

    next_update = (
        last_datetime +
        timedelta(days=UPDATE_INTERVAL_DAYS)
    )

    now = datetime.now()

    print(
        "Last update:",
        last_datetime
    )

    print(
        "Next update:",
        next_update
    )

    if now >= next_update:

        return True

    return False


def main():

    initialize_database()

    print("=" * 60)
    print("SCHEDULED EXPENSE CHECK")
    print("=" * 60)

    if should_update():

        print("\n14 days have passed.")

        print(
            "Starting expense update..."
        )

        success = run_update()

        if success:

            print(
                "\nScheduled update completed."
            )

        else:

            print(
                "\nScheduled update failed."
            )

    else:

        print(
            "\n14 days have not passed yet."
        )

        print(
            "No update required."
        )


if __name__ == "__main__":

    main()