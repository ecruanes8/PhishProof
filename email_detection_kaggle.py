import sqlite3
import subprocess
import shutil
import re

# LLM thresholds
high_risk_threshold = 85
med_risk_threshold = 50

# Check if Ollama is installed
if not shutil.which("ollama"):
    raise EnvironmentError("Ollama is not installed. Please install from https://ollama.com")

# --- Pre-filter for likely phishing ---
def pre_filter(body):
    keywords = [
        "verify", "account", "urgent", "login", "click here", "update info", 
        "security alert", "password reset", "wire transfer", "bank", 
        "invoice attached", "confirm", "suspended", "unauthorized", "limited access"
    ]
    return any(word in body.lower() for word in keywords)

# --- Ask the LLM for a phishing score ---
def score_with_llm(email_body):
    prompt = f"Rate this email on a scale from 0 (completely safe) to 100 (definitely phishing):\n\n{email_body}\n\nRespond with just the number."
    try:
        result = subprocess.run(['ollama', 'run', 'tinyllama'], input=prompt, capture_output=True, text=True)
        match = re.search(r'\d+', result.stdout)
        if match:
            return int(match.group(0))
    except Exception as e:
        print(f"LLM scoring failed: {e}")
    return 0

# --- Translate score to classification ---
def classify(score):
    if score >= high_risk_threshold:
        return "phishing"
    elif score >= med_risk_threshold:
        return "suspicious"
    else:
        return "safe"

# --- Main evaluation on labeled data ---
def evaluate_llm_on_labeled_data():
    conn = sqlite3.connect("Kaggle_emails.db")
    cursor = conn.cursor()

    # Fetch labeled emails
    cursor.execute("SELECT id, body, classification FROM emails WHERE classification IS NOT NULL")
    rows = cursor.fetchall()
    total = len(rows)

    correct = 0
    wrong = 0
    confusion = {
        "safe": {"safe": 0, "suspicious": 0, "phishing": 0},
        "phishing": {"safe": 0, "suspicious": 0, "phishing": 0}
    }

    print(f"\n Evaluating {total} labeled emails using LLM...\n")

    for email_id, body, true_label in rows:
        score = score_with_llm(body if pre_filter(body) else "")
        pred_label = classify(score)

        print(f"{email_id} | TRUE: {true_label.upper()} | PRED: {pred_label.upper()} ({score}%)")

        if true_label == pred_label:
            correct += 1
        else:
            wrong += 1

        # Update confusion matrix (ignores "suspicious" as true label since it doesn’t exist in the dataset)
        if true_label in confusion:
            confusion[true_label][pred_label] += 1

    accuracy = 100 * correct / total if total else 0
    print(f"\n Accuracy: {accuracy:.2f}% ({correct} correct / {total} total)\n")

    print(" Confusion Matrix:")
    print("Actual\\Predicted | SAFE | SUSPICIOUS | PHISHING")
    for true_lbl in ["safe", "phishing"]:
        row = confusion[true_lbl]
        print(f"{true_lbl.upper():<16} {row['safe']:>4}     {row['suspicious']:>10}     {row['phishing']:>8}")

    conn.close()

if __name__ == "__main__":
    evaluate_llm_on_labeled_data()
