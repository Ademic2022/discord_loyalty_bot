def generate_report(
    date,
    daily_records=None,
    user_record=None,
    session_records=None,
    is_admin=False,
):
    """Generate formatted reports for admin or user."""
    if is_admin:
        # Format admin report
        report = f"📊 **Away Time Report - {date}**\n"
        report += "```\nName             | Total Away(Mins) | Over Limit(Mins) | Fees(%)    \n"
        report += "-----------------|------------------|------------------|--------\n"
        for record in daily_records:
            name, total, over_limit, fee = record
            report += f"{name:<16} | {total:^16} | {over_limit:^16} | {fee:<7}\n"

        report += "```\n**Individual Away Sessions**\n```\n"
        report += "Name             | Start      | End        | Expected  | Actual    | Fees(%)    \n"
        report += "-----------------|------------|------------|-----------|-----------|--------\n"

        for record in session_records:
            name, start, end, expected, actual, fee = record
            report += f"{name:<16} | {start:<10} | {end:<10} | {expected:^9} | {actual:^9} | {fee:<7}\n"
        report += "```"
    else:
        # Format user report
        name, total, over_limit, fee = user_record
        report = f"📊 **Your Away Time Report - {date}**\n```\nTotal minutes: {total}\n"
        report += f"Over limit minutes: {over_limit}\nFee percentage: {fee}%\n```\n"

        if session_records:
            report += "\n**Your Individual Away Sessions**\n```\n"
            report += "Start      | End        | Expected  | Actual    | Fees(%)    \n"
            report += "-----------|------------|-----------|-----------|--------\n"

            for record in session_records:
                start, end, expected, actual, fee = record
                report += f"{start:<10} | {end:<10} | {expected:^9} | {actual:^9} | {fee:<7}\n"
            report += "```"

    return report
