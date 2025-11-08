import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import PeftModel
from datasets import load_dataset, Dataset
from trl import SFTTrainer
from tqdm import tqdm

try:
    from unsloth import FastLanguageModel  # Optional: only needed for full adaptive training
except ImportError:
    FastLanguageModel = None


class SecuritySLMUnsloth:
    """Inference-only wrapper (kept for lightweight classification use)."""

    def __init__(self, adapter_path: Optional[str] = None, base_model_name: Optional[str] = None, max_seq_length: int = 1024):
        self.available = True
        repo_root = Path(__file__).resolve().parent
        self.adapter_path = Path(adapter_path) if adapter_path else (repo_root / "lora_adapters" / "best")
        self.base_model_name = base_model_name or os.getenv("UNSLOTH_BASE_MODEL", "meta-llama/Llama-3.2-1B")
        self.max_seq_length = max_seq_length

        # Device selection
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name, use_fast=True)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )
            self.model = PeftModel.from_pretrained(base_model, str(self.adapter_path))
            self.model.to(self.device)
            self.model.eval()

            self.terminators = [self.tokenizer.eos_token_id]
            try:
                eot = self.tokenizer.convert_tokens_to_ids("<|eot_id|>")
                if isinstance(eot, int) and eot != self.tokenizer.eos_token_id:
                    self.terminators.append(eot)
            except Exception:
                pass
        except Exception as e:
            self.available = False
            self.model = None
            self.tokenizer = None
            self.terminators = None
            print(f"[SecuritySLMUnsloth] Inference wrapper unavailable: {e}")

    @staticmethod
    def _parse_label(text: str) -> Optional[str]:
        match = re.search(r"classification:\s*\"(ACCEPT|FLAG|BLOCK)\"", text)
        return match.group(1) if match else None

    def classify(self, prompt_text: str) -> str:
        if not self.available or self.model is None:
            return "NOT_AVAILABLE"
        classification_prompt = f"prompt: \"{prompt_text}\"\nclassification: \""
        inputs = self.tokenizer([classification_prompt], return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=5,
                eos_token_id=self.terminators,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=False,
            )
        result_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        label = self._parse_label(result_text)
        return label if label else "FAILED_TO_CLASSIFY"


class SecuritySLMUnslothFirewall:
    """
    Full adaptive firewall (fine-tuning + evaluation + rollback) modeled after notebook AegisLocalFirewall.
    Requires `unsloth` + GPU for practical speed. On non-GPU systems retraining is disabled gracefully.
    """

    def __init__(self, initial_adapter_path: str, model_name: str = "meta-llama/Llama-3.2-1B",
                 master_dataset_path: str = "data/live_training_data.jsonl",
                 test_dataset_path: str = "data/test_eval_data_unsloth.json"):
        self.model_name = model_name
        self.current_best_path = initial_adapter_path
        self.master_dataset_path = master_dataset_path
        self.test_dataset_path = test_dataset_path
        self.current_best_score: Optional[float] = None
        self.available = True

        # Check hardware & unsloth availability
        if FastLanguageModel is None:
            print("[SecuritySLMUnslothFirewall] 'unsloth' not installed. Adaptive retraining disabled.")
            self.available = False
            return
        if not torch.cuda.is_available():
            print("[SecuritySLMUnslothFirewall] CUDA GPU not available. Adaptive retraining disabled (inference only).")
            self.available = False
            return

        print(f"[Firewall] Loading base model '{self.model_name}' once...")
        self.base_model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=1024,
            dtype=None,
            load_in_4bit=True,
        )
        self.model = PeftModel.from_pretrained(self.base_model, self.current_best_path)
        self.model.eval()

        self.terminators = [
            self.tokenizer.eos_token_id,
            self.tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        # Load test set
        with open(self.test_dataset_path, 'r') as f:
            test_data_list = json.load(f)['data']
        self.test_set = Dataset.from_list(test_data_list)

        self.current_best_score = self._evaluate_model_from_path(self.current_best_path)
        print(f"[Firewall] Initial accuracy cached: {self.current_best_score:.2f}%")

    @staticmethod
    def formatting_func(example: Dict[str, Any]) -> Dict[str, str]:
        text = f"prompt: \"{example['text']}\"\nclassification: \"{example['label']}\""
        return {"text": text}

    def classify(self, prompt_text: str) -> str:
        if not self.available:
            return "NOT_AVAILABLE"
        classification_prompt = f"prompt: \"{prompt_text}\"\nclassification: \""
        inputs = self.tokenizer([classification_prompt], return_tensors="pt").to("cuda")
        self.model.eval()
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=5,
            eos_token_id=self.terminators,
            pad_token_id=self.tokenizer.eos_token_id
        )
        result_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        m = re.search(r"classification: \"(ACCEPT|FLAG|BLOCK)\"", result_text)
        return m.group(1) if m else "FAILED_TO_CLASSIFY"

    def reload_adapters(self, adapter_path: str):
        try:
            self.model = PeftModel.from_pretrained(self.base_model, adapter_path)
            self.model.eval()
            self.current_best_path = adapter_path
            print(f"[Firewall] Adapters reloaded: {adapter_path}")
        except Exception as e:
            print(f"[Firewall] Reload failed: {e}")

    def retrain_and_evaluate(self, new_prompt: str, new_verdict: str) -> Dict[str, Any]:
        if not self.available:
            return {"status": "disabled", "reason": "Adaptive retraining not available on this host."}

        print("[Firewall] Adaptive immunity loop starting...")
        current_score = self.current_best_score

        # Append new data
        entry = {"text": new_prompt, "label": new_verdict}
        with open(self.master_dataset_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        master_df = Dataset.from_json(self.master_dataset_path) if False else None  # Placeholder if needed

        # In-place fine-tune on single example
        self.model.train()
        for name, param in self.model.named_parameters():
            if 'lora' in name.lower():
                param.requires_grad = True
        self.model.enable_input_require_grads()

        singular_train_dataset = Dataset.from_list([entry])
        singular_train_dataset = singular_train_dataset.map(self.formatting_func, remove_columns=["text", "label"])

        args = TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            max_steps=3,
            learning_rate=2e-5,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            output_dir="outputs",
            optim="adamw_8bit",
            seed=3407,
            report_to="none",
        )

        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=singular_train_dataset,
            dataset_text_field="text",
            max_seq_length=1024,
            args=args,
        )
        trainer.train()
        self.model.eval()
        candidate_score = self._evaluate_live_model()

        if candidate_score >= current_score:
            self.model.save_pretrained(self.current_best_path)
            self.current_best_score = candidate_score
            action = "promoted"
        else:
            self.reload_adapters(self.current_best_path)
            action = "rolled_back"

        status = {
            "last_action": action,
            "candidate_score": candidate_score,
            "previous_best_score": current_score,
            "current_best_score": self.current_best_score,
        }
        with open("data/model_registry.json", 'w') as f:
            json.dump(status, f, indent=2)
        return status

    def _evaluate_model_from_path(self, adapter_path: str) -> float:
        eval_base_model, eval_tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=1024,
            dtype=None,
            load_in_4bit=True,
            disable_log_stats=True,
        )
        eval_model = PeftModel.from_pretrained(eval_base_model, adapter_path)
        eval_model.eval()
        terminators = [eval_tokenizer.eos_token_id, eval_tokenizer.convert_tokens_to_ids("<|eot_id|>")]
        correct = 0
        total = len(self.test_set)
        for item in tqdm(self.test_set, desc="Eval (path)", leave=False):
            prompt = item['text']
            gt = item['label']
            classification_prompt = f"prompt: \"{prompt}\"\nclassification: \""
            inputs = eval_tokenizer([classification_prompt], return_tensors="pt").to("cuda")
            outputs = eval_model.generate(
                **inputs,
                max_new_tokens=5,
                eos_token_id=terminators,
                pad_token_id=eval_tokenizer.eos_token_id
            )
            txt = eval_tokenizer.decode(outputs[0], skip_special_tokens=True)
            m = re.search(r"classification: \"(ACCEPT|FLAG|BLOCK)\"", txt)
            if m and m.group(1) == gt:
                correct += 1
        return (correct / total) * 100

    def _evaluate_live_model(self) -> float:
        self.model.eval()
        correct = 0
        total = len(self.test_set)
        for item in tqdm(self.test_set, desc="Eval (live)", leave=False):
            prompt = item['text']
            gt = item['label']
            classification_prompt = f"prompt: \"{prompt}\"\nclassification: \""
            inputs = self.tokenizer([classification_prompt], return_tensors="pt").to("cuda")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=5,
                eos_token_id=self.terminators,
                pad_token_id=self.tokenizer.eos_token_id
            )
            txt = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            m = re.search(r"classification: \"(ACCEPT|FLAG|BLOCK)\"", txt)
            if m and m.group(1) == gt:
                correct += 1
        return (correct / total) * 100


def conservative_merge(a: str, b: str) -> str:
    """Return the more conservative label among ACCEPT < FLAG < BLOCK."""
    order = {"ACCEPT": 0, "FLAG": 1, "BLOCK": 2}
    # Normalize any unexpected values
    a = a if a in order else "ACCEPT"
    b = b if b in order else "ACCEPT"
    return max((a, b), key=lambda x: order[x])
