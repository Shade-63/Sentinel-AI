import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight

# Load dataset
df = pd.read_csv("sentinel_dataset_audited.csv")

# Basic cleaning
df = df.dropna()
df["text"] = df["text"].astype(str)

# Train-test split
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["text"].tolist(),
    df["label"].tolist(),
    test_size=0.2,
    random_state=42,
    stratify=df["label"].tolist()  # Ensure balanced split
)

# Compute class weights for balanced training
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(train_labels),
    y=train_labels
)
class_weights = torch.tensor(class_weights, dtype=torch.float)
print(f"Class weights: {class_weights}")
print(f"Training set - SAFE: {train_labels.count(0)}, SCAM: {train_labels.count(1)}")

# Tokenizer
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)

train_dataset = Dataset.from_dict({
    "input_ids": train_encodings["input_ids"],
    "attention_mask": train_encodings["attention_mask"],
    "labels": train_labels
})

val_dataset = Dataset.from_dict({
    "input_ids": val_encodings["input_ids"],
    "attention_mask": val_encodings["attention_mask"],
    "labels": val_labels
})

# Model with class weights
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2
)

# Custom trainer class to use class weights
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fct = torch.nn.CrossEntropyLoss(weight=class_weights.to(logits.device))
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

# Metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        "accuracy": acc,
        "f1": f1,
        "precision": precision,
        "recall": recall
    }

# Training args - improved parameters
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,  # Increased from 3 to 5
    per_device_train_batch_size=16,  # Increased from 8 to 16
    per_device_eval_batch_size=16,
    warmup_steps=200,  # Increased warmup
    weight_decay=0.01,
    learning_rate=2e-5,  # Explicit learning rate
    logging_dir="./logs",
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,  # Load best model after training
    metric_for_best_model="f1",  # Use F1 score for best model
    save_total_limit=2  # Keep only 2 best checkpoints
)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

print("\n" + "="*60)
print("Starting training...")
print("="*60)
trainer.train()

print("\n" + "="*60)
print("Evaluating model...")
print("="*60)
eval_results = trainer.evaluate()
print(f"\nFinal Evaluation Results:")
print(f"  Accuracy: {eval_results['eval_accuracy']:.4f}")
print(f"  F1 Score: {eval_results['eval_f1']:.4f}")
print(f"  Precision: {eval_results['eval_precision']:.4f}")
print(f"  Recall: {eval_results['eval_recall']:.4f}")

# Save model (use absolute path to avoid nested directories)
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
save_path = os.path.join(script_dir, "sentinel_model")
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print(f"\n{'='*60}")
print(f"Model training complete and saved to: {save_path}")
print("="*60)