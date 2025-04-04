
import sqlite3
import subprocess # ollama 
import shutil
import re


high_risk_threshold = 85
med_risk_threshold = 50

#check is ollama is installed 
if not shutil.which("ollama"):
    raise EnvironmentError("Ollama is not installed. Please install from https://ollama.com")

# to install ollama: 
    # --> brew install ollama 
    # --> ollama run mistral 

def pre_filter(body):
    keywords = [
        "verify", "account", "urgent", "login", "click here", "update info", 
        "security alert", "password reset", "wire transfer", "bank", "invoice attached",
        "confirm", "suspended", "unauthorized", "limited access"
    ]
    return any(word in body.lower() for word in keywords)

# run LLM locally via Ollama (Mistral model)
def score_with_mistral(email_body):
    prompt = f"Rate this email on a scale from 0 (completely safe) to 100 (definitely phishing):\n\n{email_body}\n\nRespond with just the number."
    try:
        result = subprocess.run(
            ['ollama', 'run', 'mistral'],
            input=prompt,
            capture_output=True,
            text=True
        )
        # Extract score from the model output
        score_match = re.search(r'\d+', result.stdout)
        if score_match:
            return int(score_match.group(0))
    except Exception as e:
        print(f"LLM scoring failed: {e}")
    return 0  # Default to safe if something fails

# classify score into labels
def classify(score):
    if score >= high_risk_threshold:
        return "phishing"
    elif score >= med_risk_threshold:
        return "suspicious"
    else:
        return "safe"

#main 
def analyze_emails():
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute("PRAGMA table_info(emails)")
    columns = [col[1] for col in cursor.fetchall()]

    # Fetch unprocessed emails
    cursor.execute("SELECT id, body FROM emails WHERE suspicion_score IS NULL")
    emails = cursor.fetchall()

    print(f"\n🔍 Analyzing {len(emails)} unprocessed emails...\n")

    for email_id, body in emails:
        if pre_filter(body):
            score = score_with_mistral(body)
        else:
            score = 0

        label = classify(score)
        print(f"{email_id} => {label.upper()} ({score}%)")

        cursor.execute("""
            UPDATE emails
            SET suspicion_score = ?, classification = ?
            WHERE id = ?
        """, (score, label, email_id))
        conn.commit()

    conn.close()
    print("\n Analysis complete. All scores updated.")

if __name__ == '__main__':
    analyze_emails()