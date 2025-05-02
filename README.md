# PhishProof
A Security Framework for Detecting Business Impersonation Emails

This project strives to understand phishing emails and detect them through pre-filtering and LLMs. The repository contains the kaggle database of 80k emails containing safe and phishing emails. 

The file email_detection_kaggle.py initializes a LLM using ollama to filter through these emails and rates them from 0-100% chance of phishing. 

We also set up a gmail API to a fake account to receive real phishing emails and detect them using email_capture.py. 

Prompts.txt are used for prompt engineering for the LLM. 

To run the project use python email_detection_kaggle.py
