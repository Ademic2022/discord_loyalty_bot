from fpdf import FPDF


class ReportGenerator(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "Away Time Report", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def generate_report(
        self,
        date,
        daily_records=None,
        user_record=None,
        session_records=None,
        is_admin=False,
    ):
        is_pdf = False
        if len(session_records) <= 15:
            report = self.generate_txt_report(
                date=date,
                daily_records=daily_records,
                session_records=session_records,
                user_record=user_record,
                is_admin=is_admin,
            )
        else:
            report = self.generate_pdf_report(
                date=date,
                daily_records=daily_records,
                session_records=session_records,
                user_record=user_record,
                is_admin=is_admin,
            )
            is_pdf = True

        return report, is_pdf

    def generate_pdf_report(
        self,
        date,
        daily_records=None,
        user_record=None,
        session_records=None,
        is_admin=False,
        output_filename="report.pdf",
    ):
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)

        # Add date
        self.set_font("Arial", "B", 12)
        if is_admin:
            self.cell(0, 10, f"Admin Report - {date}", 0, 1, "C")
        else:
            self.cell(0, 10, f"Your Away Time Report - {date}", 0, 1, "C")
        self.ln(5)

        if is_admin:
            self.generate_admin_report(daily_records, session_records)
        else:
            self.generate_user_report(user_record, session_records)

        self.output(output_filename)
        return output_filename

    def generate_admin_report(self, daily_records, session_records):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Daily Summary", 0, 1, "L")

        # Table header
        self.set_font("Arial", "B", 10)
        self.set_fill_color(200, 200, 200)
        col_widths = [50, 35, 35, 30]
        self.cell(col_widths[0], 10, "Name", 1, 0, "C", True)
        self.cell(col_widths[1], 10, "Total Away (Mins)", 1, 0, "C", True)
        self.cell(col_widths[2], 10, "Over Limit (Mins)", 1, 0, "C", True)
        self.cell(col_widths[3], 10, "Fees (%)", 1, 1, "C", True)

        # Table data
        self.set_font("Arial", "", 10)
        for record in daily_records:
            name, total, over_limit, fee = record
            self.cell(col_widths[0], 10, str(name), 1, 0, "L")
            self.cell(col_widths[1], 10, str(total), 1, 0, "C")
            self.cell(col_widths[2], 10, str(over_limit), 1, 0, "C")
            self.cell(col_widths[3], 10, str(fee), 1, 1, "C")

        self.ln(5)

        # Individual sessions
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Individual Away Sessions", 0, 1, "L")

        # Table header
        self.set_font("Arial", "B", 10)
        session_col_widths = [40, 25, 25, 30, 30, 25]
        self.cell(session_col_widths[0], 10, "Name", 1, 0, "C", True)
        self.cell(session_col_widths[1], 10, "Start", 1, 0, "C", True)
        self.cell(session_col_widths[2], 10, "End", 1, 0, "C", True)
        self.cell(session_col_widths[3], 10, "Expected", 1, 0, "C", True)
        self.cell(session_col_widths[4], 10, "Actual", 1, 0, "C", True)
        self.cell(session_col_widths[5], 10, "Fees (%)", 1, 1, "C", True)

        # Table data
        self.set_font("Arial", "", 10)
        for record in session_records:
            name, start, end, expected, actual, fee = record
            self.cell(session_col_widths[0], 10, str(name), 1, 0, "L")
            self.cell(session_col_widths[1], 10, str(start), 1, 0, "C")
            self.cell(session_col_widths[2], 10, str(end), 1, 0, "C")
            self.cell(session_col_widths[3], 10, str(expected), 1, 0, "C")
            self.cell(session_col_widths[4], 10, str(actual), 1, 0, "C")
            self.cell(session_col_widths[5], 10, str(fee), 1, 1, "C")

    def generate_user_report(self, user_record, session_records):
        name, total, over_limit, fee = user_record

        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Your Away Time Summary", 0, 1, "L")

        # Summary table
        self.set_font("Arial", "", 10)
        self.cell(60, 8, "Total minutes:", 1, 0, "L", True)
        self.cell(60, 8, str(total), 1, 1, "L")
        self.cell(60, 8, "Over limit minutes:", 1, 0, "L", True)
        self.cell(60, 8, str(over_limit), 1, 1, "L")
        self.cell(60, 8, "Fee percentage:", 1, 0, "L", True)
        self.cell(60, 8, f"{fee}%", 1, 1, "L")

        self.ln(5)

        if session_records:
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Your Individual Away Sessions", 0, 1, "L")

            # Table header
            self.set_font("Arial", "B", 10)
            user_col_widths = [30, 30, 35, 35, 30]
            self.cell(user_col_widths[0], 10, "Start", 1, 0, "C", True)
            self.cell(user_col_widths[1], 10, "End", 1, 0, "C", True)
            self.cell(user_col_widths[2], 10, "Expected", 1, 0, "C", True)
            self.cell(user_col_widths[3], 10, "Actual", 1, 0, "C", True)
            self.cell(user_col_widths[4], 10, "Fees (%)", 1, 1, "C", True)

            self.set_font("Arial", "", 10)
            for record in session_records:
                start, end, expected, actual, fee = record
                self.cell(user_col_widths[0], 10, str(start), 1, 0, "C")
                self.cell(user_col_widths[1], 10, str(end), 1, 0, "C")
                self.cell(user_col_widths[2], 10, str(expected), 1, 0, "C")
                self.cell(user_col_widths[3], 10, str(actual), 1, 0, "C")
                self.cell(user_col_widths[4], 10, str(fee), 1, 1, "C")

    def generate_txt_report(
        self,
        date,
        daily_records=None,
        user_record=None,
        session_records=None,
        is_admin=False,
    ):
        """Generate formatted text reports for admin or user."""
        if is_admin:
            return self.generate_admin_txt_report(date, daily_records, session_records)
        else:
            return self.generate_user_txt_report(date, user_record, session_records)

    def generate_admin_txt_report(self, date, daily_records, session_records):
        report = f"📊 **Away Time Report - {date}**\n"
        report += "```\nName             | Total Away(Mins) | Over Limit(Mins) | Fees(%)    \n"
        report += "-----------------|------------------|------------------|--------\n"
        for record in daily_records:
            name, total, over_limit, fee = record
            report += f"{name:<16} | {total:^16} | {over_limit:^16} | {round(fee, 4):<7}\n"

        report += "```\n**Individual Away Sessions**\n```\n"
        report += "Name             | Start      | End        | Expected  | Actual    | Fees(%)    \n"
        report += "-----------------|------------|------------|-----------|-----------|--------\n"

        for record in session_records:
            name, start, end, expected, actual, fee = record
            report += f"{name:<16} | {start:<10} | {end:<10} | {expected:^9} | {actual:^9} | {round(fee, 4):<7}\n"
        report += "```"
        return report

    def generate_user_txt_report(self, date, user_record, session_records):
        name, total, over_limit, fee = user_record

        report = f"📊 **Your Away Time Report - {date}**\n"
        report += "```\nTotal minutes away:         {}\n".format(total)
        report += "Over limit minutes:         {}\n".format(over_limit)
        report += "Fee percentage:             {}%\n".format(round(fee, 4))
        report += "```\n"

        if session_records:
            report += "**Your Individual Away Sessions**\n```\n"
            report += "Start       | End         | Expected   | Actual     | Fees (%)\n"
            report += "------------|-------------|------------|------------|--------\n"
            for record in session_records:
                start, end, expected, actual, fee = record
                report += f"{start:<11} | {end:<11} | {expected:^10} | {actual:^10} | {round(fee, 4):<7}\n"
            report += "```"
        return report
