from inference import predict

# Test with scam examples
scam_tests = [
    "FBI warrant arrest immediate payment",
    "You have won $1,000,000! Click here now!",
    "Your account will be suspended unless you verify immediately",
    "URGENT: IRS tax payment required or face legal action"
]

# Test with safe examples
safe_tests = [
    "meeting agenda for tomorrow",
    "Hello, how are you doing today?",
    "The project deadline is next Friday",
    "Can we schedule a call this week?"
]

print("=" * 60)
print("TESTING SCAM MESSAGES (should predict SCAM)")
print("=" * 60)
for text in scam_tests:
    result = predict(text)
    print(f"\nText: {text}")
    print(f"Prediction: {result['label']}")
    print(f"Scam prob: {result['scam_probability']:.4f}, Safe prob: {result['safe_probability']:.4f}")

print("\n" + "=" * 60)
print("TESTING SAFE MESSAGES (should predict SAFE)")
print("=" * 60)
for text in safe_tests:
    result = predict(text)
    print(f"\nText: {text}")
    print(f"Prediction: {result['label']}")
    print(f"Scam prob: {result['scam_probability']:.4f}, Safe prob: {result['safe_probability']:.4f}")
