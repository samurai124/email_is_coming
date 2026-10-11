import argparse
import os
import random
import sys
import time
from pathlib import Path
from config import Config
from ai_generator import AIEmailGenerator
from csv_manager import CSVManager
from email_sender import EmailSender

# Terminal color helper (ANSI)
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}===============================================================
       JOB APPLICATION AUTO-MAILER (CLI)
       AI-Powered Cold Outreach with Resume Attachment
==============================================================={Colors.RESET}
"""
    print(banner)

def check_environment():
    """Validates configuration and prints any setup warnings."""
    csv_mgr = CSVManager()
    created_sample = csv_mgr.initialize_sample_csv_if_missing()
    if created_sample:
        print(f"{Colors.YELLOW}[!] Created sample companies list at: {Config.CSV_PATH}{Colors.RESET}")

    issues = Config.validate_setup()
    if issues:
        print(f"\n{Colors.YELLOW}[Configuration Notice]:{Colors.RESET}")
        for issue in issues:
            print(f"  {Colors.RED}- {issue}{Colors.RESET}")
        print(f"{Colors.DIM}Please update your .env file in the project folder.{Colors.RESET}\n")
        return False
    return True

def do_test_connection():
    """Tests SMTP connection and credentials."""
    print(f"\n{Colors.CYAN}[1/2] Checking SMTP credentials...{Colors.RESET}")
    print(f"Server: {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
    print(f"Sender: {Config.SENDER_EMAIL}")

    sender = EmailSender()
    success, msg = sender.test_connection()
    if success:
        print(f"{Colors.GREEN}[SUCCESS] {msg}{Colors.RESET}")
    else:
        print(f"{Colors.RED}[ERROR] {msg}{Colors.RESET}")

    print(f"\n{Colors.CYAN}[2/2] Checking Resume Attachment...{Colors.RESET}")
    if Config.RESUME_PATH.exists():
        size_kb = Config.RESUME_PATH.stat().st_size / 1024
        print(f"{Colors.GREEN}[SUCCESS] Found resume '{Config.RESUME_PATH.name}' ({size_kb:.1f} KB){Colors.RESET}")
    else:
        print(f"{Colors.RED}[ERROR] Resume not found at: {Config.RESUME_PATH}{Colors.RESET}")
        print(f"Please place your resume PDF in: {Config.RESUMES_DIR}")

def do_validate_csv():
    """Inspects companies.csv and reports ready/pending counts."""
    csv_mgr = CSVManager()
    pending, warnings = csv_mgr.load_companies()
    summary = csv_mgr.get_summary()

    print(f"\n{Colors.CYAN}--- CSV & Application Status ---{Colors.RESET}")
    print(f"Total Sent in History: {Colors.GREEN}{summary.get('sent', 0)}{Colors.RESET}")
    print(f"Total Failed in History: {Colors.RED}{summary.get('failed', 0)}{Colors.RESET}")
    print(f"Pending Companies to Email: {Colors.BOLD}{len(pending)}{Colors.RESET}")

    if warnings:
        print(f"\n{Colors.YELLOW}Warnings / Skipped entries ({len(warnings)}):{Colors.RESET}")
        for w in warnings[:10]:
            print(f"  {Colors.DIM}- {w}{Colors.RESET}")
        if len(warnings) > 10:
            print(f"  {Colors.DIM}... and {len(warnings) - 10} more.{Colors.RESET}")

    if pending:
        print(f"\n{Colors.CYAN}Next up to receive emails:{Colors.RESET}")
        for i, comp in enumerate(pending[:5], 1):
            print(f"  {i}. {comp['company_name']} ({comp['role']}) -> {comp['email']} [Contact: {comp['contact_name']}]")
        if len(pending) > 5:
            print(f"  ... and {len(pending) - 5} more.")

def do_preview(limit: int = 1):
    """Generates and previews AI-crafted emails without sending."""
    csv_mgr = CSVManager()
    pending, _ = csv_mgr.load_companies()

    if not pending:
        print(f"{Colors.YELLOW}No pending companies found in {Config.CSV_PATH}. All might have already been sent!{Colors.RESET}")
        return

    ai_gen = AIEmailGenerator()
    to_preview = pending[:limit]

    print(f"\n{Colors.CYAN}Generating preview for {len(to_preview)} company(s)...{Colors.RESET}")

    for idx, comp in enumerate(to_preview, 1):
        print(f"\n{Colors.BOLD}{'=' * 60}")
        print(f"PREVIEW #{idx}: {comp['company_name']} ({comp['role']})")
        print(f"Recipient: {comp['email']} | Contact: {comp['contact_name']}")
        print(f"{'=' * 60}{Colors.RESET}")

        result = ai_gen.generate(comp)
        ai_badge = f"{Colors.GREEN}[AI Generated]{Colors.RESET}" if result.get("used_ai") else f"{Colors.YELLOW}[Template Fallback]{Colors.RESET}"
        
        print(f"Mode: {ai_badge}")
        if not result.get("used_ai") and result.get("fallback_reason"):
            print(f"{Colors.DIM}Reason: {result.get('fallback_reason')}{Colors.RESET}")

        print(f"\n{Colors.BOLD}Subject:{Colors.RESET} {result['subject']}\n")
        print(f"{Colors.DIM}--- Email Body ---{Colors.RESET}")
        print(result["body"])
        print(f"{Colors.DIM}--- End of Body ---{Colors.RESET}")
        print(f"Attachment: {Config.RESUME_PATH.name} (from {Config.RESUME_PATH})")

def do_send_batch():
    """Sends personalized emails with safety checks and rate-limiting."""
    if not check_environment():
        print(f"{Colors.RED}Please fix configuration issues before sending live emails.{Colors.RESET}")
        return

    sender = EmailSender()
    conn_ok, conn_err = sender.test_connection()
    if not conn_ok:
        print(f"{Colors.RED}Cannot send: SMTP connection test failed: {conn_err}{Colors.RESET}")
        return

    csv_mgr = CSVManager()
    pending, _ = csv_mgr.load_companies()

    if not pending:
        print(f"{Colors.YELLOW}No pending companies to email. Everything in your CSV is already sent or invalid.{Colors.RESET}")
        return

    batch_size = min(len(pending), Config.DAILY_MAX_EMAILS)
    targets = pending[:batch_size]

    print(f"\n{Colors.BOLD}Target Batch Summary:{Colors.RESET}")
    print(f"- Ready to send: {Colors.CYAN}{batch_size} email(s){Colors.RESET}")
    print(f"- Sender Email: {Colors.CYAN}{Config.SENDER_EMAIL}{Colors.RESET}")
    print(f"- Resume Attachment: {Colors.CYAN}{Config.RESUME_PATH.name}{Colors.RESET}")
    print(f"- Safety Delay: {Config.MIN_DELAY_SECONDS} to {Config.MAX_DELAY_SECONDS} seconds between sends\n")

    confirm = input(f"{Colors.YELLOW}{Colors.BOLD}Are you sure you want to SEND these {batch_size} emails? Type 'yes' to proceed: {Colors.RESET}").strip().lower()
    if confirm != "yes":
        print(f"{Colors.YELLOW}Sending aborted by user.{Colors.RESET}")
        return

    ai_gen = AIEmailGenerator()
    print(f"\n{Colors.GREEN}Starting email dispatch... Press Ctrl+C at any time to pause.{Colors.RESET}\n")

    for idx, comp in enumerate(targets, 1):
        print(f"\n[{idx}/{batch_size}] Generating message for {Colors.BOLD}{comp['company_name']}{Colors.RESET} ({comp['email']})...")
        
        email_data = ai_gen.generate(comp)
        
        try:
            msg = sender.build_message(
                to_email=comp["email"],
                subject=email_data["subject"],
                body_text=email_data["body"],
                resume_path=Config.RESUME_PATH
            )
            
            success, send_msg = sender.send_message(msg)
            if success:
                print(f"  {Colors.GREEN}[✓] Sent successfully! Subject: '{email_data['subject']}'{Colors.RESET}")
                csv_mgr.log_result(comp, "SENT")
            else:
                print(f"  {Colors.RED}[✗] Failed to send: {send_msg}{Colors.RESET}")
                csv_mgr.log_result(comp, "FAILED", send_msg)
        except Exception as e:
            print(f"  {Colors.RED}[✗] Error: {str(e)}{Colors.RESET}")
            csv_mgr.log_result(comp, "FAILED", str(e))

        # If not the last email, apply anti-spam jitter delay
        if idx < batch_size:
            delay = random.randint(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
            print(f"  {Colors.DIM}Anti-spam cooldown: Waiting {delay}s before next email...{Colors.RESET}", end="", flush=True)
            for remaining in range(delay, 0, -1):
                time.sleep(1)
                print(f"\r  {Colors.DIM}Anti-spam cooldown: Waiting {remaining}s before next email...{Colors.RESET} ", end="", flush=True)
            print()

    print(f"\n{Colors.GREEN}{Colors.BOLD}Batch complete! Check 'data/sent_log.csv' for the full delivery log.{Colors.RESET}")

def interactive_menu():
    """Interactive CLI menu when run without CLI arguments."""
    while True:
        print_banner()
        print("Select an action:")
        print(f"  {Colors.BOLD}1{Colors.RESET}. Test Connection & Resume Setup")
        print(f"  {Colors.BOLD}2{Colors.RESET}. Inspect CSV & View Pending Companies")
        print(f"  {Colors.BOLD}3{Colors.RESET}. Preview AI-Generated Email (Dry-Run)")
        print(f"  {Colors.BOLD}4{Colors.RESET}. Send Emails (Live Batch)")
        print(f"  {Colors.BOLD}5{Colors.RESET}. Exit\n")

        choice = input(f"{Colors.CYAN}Enter choice (1-5): {Colors.RESET}").strip()
        if choice == "1":
            do_test_connection()
        elif choice == "2":
            do_validate_csv()
        elif choice == "3":
            try:
                num = input("How many previews to generate? (default: 1): ").strip()
                count = int(num) if num.isdigit() else 1
            except ValueError:
                count = 1
            do_preview(limit=count)
        elif choice == "4":
            do_send_batch()
        elif choice == "5" or choice.lower() in ("exit", "quit", "q"):
            print("Goodbye and good luck with your job hunt!")
            break
        else:
            print(f"{Colors.YELLOW}Invalid choice, please enter 1, 2, 3, 4, or 5.{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Press Enter to return to main menu...{Colors.RESET}")

def main():
    parser = argparse.ArgumentParser(description="Job Application Auto-Mailer CLI")
    parser.add_argument("--test", action="store_true", help="Test SMTP server connection and credentials")
    parser.add_argument("--status", action="store_true", help="Show CSV status and pending counts")
    parser.add_argument("--preview", type=int, nargs="?", const=1, help="Preview AI-crafted email without sending (e.g. --preview 2)")
    parser.add_argument("--send", action="store_true", help="Start sending emails to pending companies")

    args = parser.parse_args()

    # If any CLI flag provided, execute it directly
    if args.test:
        print_banner()
        do_test_connection()
    elif args.status:
        print_banner()
        do_validate_csv()
    elif args.preview is not None:
        print_banner()
        do_preview(limit=args.preview)
    elif args.send:
        print_banner()
        do_send_batch()
    else:
        # Otherwise open interactive menu
        interactive_menu()

if __name__ == "__main__":
    main()
