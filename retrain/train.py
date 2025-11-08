from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    TrainingArguments,
    Trainer
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from logic import combine
from safetensors.torch import load_file
import os


def train_model(
    model_path="betModel",
    dataset1_path="data/betStart.json",
    dataset2_path="data/trainSample.json",
    output_path="betModel",
    num_epochs=75,
    batch_size=8,
    weight_decay=5e-4,
    label_map=None
):
    """
    Train a sequence classification model.

    Args:
        model_path: Path to the pre-trained model to fine-tune
        dataset1_path: Path to first JSON dataset
        dataset2_path: Path to second JSON dataset
        output_path: Path to save the trained model (will overwrite)
        num_epochs: Number of training epochs
        batch_size: Training and evaluation batch size
        weight_decay: Weight decay for regularization
        label_map: Dictionary mapping label strings to integers.
                   Defaults to {"SAFE": 0, "FLAG": 1, "BLOCKED": 2}

    Returns:
        trainer: The trained Trainer object
    """
    if label_map is None:
        label_map = {"SAFE": 0, "FLAGGED": 1, "BLOCKED": 2}

    # Resolve paths to absolute paths
    dataset1_path = os.path.abspath(dataset1_path)
    dataset2_path = os.path.abspath(dataset2_path)

    # Load tokenizer and model
    print(f"Loading tokenizer and model from {model_path}...")
    #cfg = AutoConfig.from_pretrained("/home/jas/Projects/betModel")
    #model = AutoModelForSequenceClassification.from_config(cfg)


    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, )
    classifier = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)

    #from safetensors.torch import load_file

    #state = load_file("/home/jas/Projects/betModel/model.safetensors")
    #model.load_state_dict(state, strict=False)


    # Load and combine datasets
    print("Loading datasets...")
    df_train, df_eval = combine(dataset1_path, dataset2_path)

    # Check unique labels before mapping
    print(f"Unique labels in training: {df_train['label'].unique()}")
    print(f"Unique labels in eval: {df_eval['label'].unique()}")

    
    # Map string labels to numeric values
    df_train['label'] = df_train['label'].map(label_map)
    df_eval['label'] = df_eval['label'].map(label_map)

    # Check for NaN values after mapping
    if df_train['label'].isna().any():
        print("WARNING: Some training labels didn't map correctly!")
        print(f"Unmapped values: {df_train[df_train['label'].isna()]['label'].unique()}")
    if df_eval['label'].isna().any():
        print("WARNING: Some eval labels didn't map correctly!")

    # Convert to int
    df_train['label'] = df_train['label'].astype(int)
    df_eval['label'] = df_eval['label'].astype(int)

    print(f"Training samples: {len(df_train)}")
    print(f"Evaluation samples: {len(df_eval)}")
    print(f"Label distribution in training: {df_train['label'].value_counts().to_dict()}")

    # Convert to HuggingFace datasets (reset_index to avoid index issues)
    train_dataset = Dataset.from_pandas(df_train[['text', 'label']].reset_index(drop=True))
    eval_dataset = Dataset.from_pandas(df_eval[['text', 'label']].reset_index(drop=True))

    # Tokenization function
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, max_length=512)

    # Tokenize datasets
    print("Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True, remove_columns=["text"])

    # Rename label to labels (Trainer expects "labels")
    tokenized_train = tokenized_train.rename_column("label", "labels")
    tokenized_eval = tokenized_eval.rename_column("label", "labels")

    # Padding for batch of data
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Training args
    training_args = TrainingArguments(
        output_dir="./output",
        num_train_epochs=num_epochs,
        eval_strategy="epoch",
        weight_decay=weight_decay,
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        report_to="none",
        logging_steps=10,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        push_to_hub=False,
    )

    # Metric for validation
    def compute_metrics(eval_preds):
        logits, labels = eval_preds
        predictions = np.argmax(logits, axis=-1)

        # Calculate accuracy and F1-score
        accuracy = accuracy_score(labels, predictions)
        f1 = f1_score(labels, predictions, average='weighted')

        return {"accuracy": accuracy, "f1": f1}

    # Define trainer
    print("Initializing trainer...")
    trainer = Trainer(
        classifier,
        training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )

    # Train the model
    print("Starting training...")
    trainer.train()

    # Save the final model
    print(f"Saving final model to {output_path}")
    trainer.save_model(output_path)
    tokenizer.save_pretrained(output_path)

    print(f"Training complete! Model saved to {output_path}")

    return trainer


if __name__ == "__main__":
    # Run training when script is executed directly
    train_model()