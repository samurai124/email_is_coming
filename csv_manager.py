import csv
import os
import re
from datetime import datetime
from pathlib import Path
from config import Config

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class CSVManager:
    def __init__(self, csv_path: Path = None, log_path: Path = None):
        self.csv_path = csv_path or Config.CSV_PATH
        self.log_path = log_path or Config.LOG_PATH

    def initialize_sample_csv_if_missing(self) -> bool:
        """Creates a sample companies.csv if none exists."""
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["company_name", "email", "contact_name", "role", "company_notes"])
                writer.writerow([
                    "Acme Technologies",
                    "careers@acmetech-sample.com",
                    "Alex Smith",
                    "Python Developer",
                    "Building AI cloud tooling, recently raised Series A"
                ])
                writer.writerow([
                    "Apex Global Labs",
                    "hiring@apexlabs-sample.org",
                    "Sarah Connor",
                    "Software Engineer",
                    "Focuses on scalable backend architectures and API development"
                ])
            return True
        return False

    def get_already_sent_emails(self) -> set[str]:
        """Returns a set of lowercased emails that were already successfully sent."""
        if not self.log_path.exists():
            return set()

        sent = set()
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get("status", "").strip().upper()
                email = row.get("email", "").strip().lower()
                if status == "SENT" and email:
                    sent.add(email)
        return sent

    def load_companies(self) -> tuple[list[dict], list[str]]:
        """
        Loads and validates companies from the CSV.
        Returns: (valid_pending_companies, validation_warnings)
        """
        self.initialize_sample_csv_if_missing()
        if not self.csv_path.exists():
            return [], [f"CSV file not found at: {self.csv_path}"]

        already_sent = self.get_already_sent_emails()
        companies = []
        warnings = []

        with open(self.csv_path, "r", encoding="utf-8", errors="replace") as f:
            # Sniff or default delimiter
            sample = f.read(2048)
            f.seek(0)
            delimiter = ","
            if ";" in sample and sample.count(";") > sample.count(","):
                delimiter = ";"
            elif "\t" in sample and sample.count("\t") > sample.count(","):
                delimiter = "\t"

            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Map headers dynamically
            header_map = {}
            for col in reader.fieldnames or []:
                clean_col = col.strip().lower()
                if "company" in clean_col and ("name" in clean_col or clean_col == "company"):
                    header_map["company_name"] = col
                elif "email" in clean_col:
                    header_map["email"] = col
                elif "contact" in clean_col or "name" in clean_col:
                    header_map["contact_name"] = col
                elif "role" in clean_col or "position" in clean_col or "title" in clean_col or "job" in clean_col:
                    header_map["role"] = col
                elif "note" in clean_col or "detail" in clean_col or "pitch" in clean_col:
                    header_map["company_notes"] = col

            for idx, row in enumerate(reader, start=2):
                email = row.get(header_map.get("email", "email"), "").strip()
                company_name = row.get(header_map.get("company_name", "company_name"), "").strip()
                contact_name = row.get(header_map.get("contact_name", "contact_name"), "").strip() or "Hiring Team"
                role = row.get(header_map.get("role", "role"), "").strip() or "Software Engineer"
                notes = row.get(header_map.get("company_notes", "company_notes"), "").strip()

                if not email:
                    warnings.append(f"Row {idx} ({company_name or 'Unknown'}): Empty email address. Skipped.")
                    continue

                if not EMAIL_REGEX.match(email):
                    warnings.append(f"Row {idx} ({company_name}): Invalid email format '{email}'. Skipped.")
                    continue

                if email.lower() in already_sent:
                    warnings.append(f"Row {idx} ({company_name}): Email '{email}' was already sent previously. Skipped.")
                    continue

                companies.append({
                    "row_number": idx,
                    "company_name": company_name or "your company",
                    "email": email,
                    "contact_name": contact_name,
                    "role": role,
                    "company_notes": notes
                })

        return companies, warnings

    def log_result(self, company_data: dict, status: str, error_message: str = ""):
        """Logs the sending outcome to sent_log.csv."""
        is_new_file = not self.log_path.exists()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if is_new_file:
                writer.writerow(["timestamp", "company_name", "email", "role", "status", "error_message"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                company_data.get("company_name", ""),
                company_data.get("email", ""),
                company_data.get("role", ""),
                status.upper(),
                error_message
            ])

    def get_summary(self) -> dict:
        """Returns statistics from the current log."""
        if not self.log_path.exists():
            return {"sent": 0, "failed": 0}

        counts = {"sent": 0, "failed": 0}
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                st = row.get("status", "").upper()
                if st == "SENT":
                    counts["sent"] += 1
                elif st == "FAILED":
                    counts["failed"] += 1
        return counts
