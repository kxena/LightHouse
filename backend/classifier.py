import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple
import argparse
import joblib
from pathlib import Path
from datetime import datetime

class DisasterClassifier:
    """
    Multi-model classifier for disaster tweet classification.
    Supports Logistic Regression, Random Forest, and XGBoost.
    Optimized to minimize false positives (maximize precision).
    """
    
    def __init__(self, max_features=5000, random_state=42):
        """
        Initialize the classifier with three models.
        
        Args:
            max_features: Maximum number of features for TF-IDF vectorizer
            random_state: Random seed for reproducibility
        """
        self.max_features = max_features
        self.random_state = random_state
        
        # Initialize vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            stop_words='english'
        )
        
        # Initialize label encoder
        self.label_encoder = LabelEncoder()
        
        # Initialize models with parameters optimized to reduce false positives
        self.models = {
            'logistic_regression': LogisticRegression(
                max_iter=2000,
                random_state=random_state,
                solver='lbfgs',
                C=10.0, # more conservative decision boundaries, decrease positive borderline cases
                class_weight='balanced', # adjusts for class imbalance
                penalty='l2' # less regularization, preventd overfitting
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=300,
                max_depth=25, # limits tree depth to prevent overfitting
                min_samples_split=10,
                min_samples_leaf=4,
                min_impurity_decrease=0.0001, # avoids splits that capture noise
                max_features='sqrt',
                class_weight='balanced', # adjusts for class imbalance
                random_state=random_state,
                n_jobs=-1,
                bootstrap=True,
                oob_score=True
            ),
            'xgboost': xgb.XGBClassifier(
                n_estimators=300,
                max_depth=8,
                learning_rate=0.05,
                min_child_weight=5, # minimum sum of weights in a leaf (higher = more conservative)
                gamma=0.1, # Minimum loss reduction to split (higher = fewer splits)
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1, # L1 regularization (feature selection), prevents overfitting
                reg_lambda=1.0, # L2 regularization (smoothing), prevents overfitting
                scale_pos_weight=1,
                random_state=random_state,
                tree_method='hist',
                eval_metric='mlogloss'
            )
        }
        
        self.trained = False
        self.optimal_thresholds = {}
        self.model_configs = {}
    
    def load_jsonl(self, filepath: str) -> pd.DataFrame:
        """
        Load JSONL file into a pandas DataFrame.
        
        Args:
            filepath: Path to JSONL file
            
        Returns:
            DataFrame with tweet data
        """
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        
        df = pd.DataFrame(data)
        print(f"Loaded {len(df)} entries from {filepath}")
        return df
    
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Extract text and disaster labels from DataFrame.
        
        Args:
            df: DataFrame with tweet data
            
        Returns:
            Tuple of (texts, labels)
        """
        # Get text column (try common column names)
        text_columns = ['tweet_text', 'text', 'tweet', 'message']
        text_col = None
        for col in text_columns:
            if col in df.columns:
                text_col = col
                break
        
        if text_col is None:
            raise ValueError(f"Could not find text column. Available columns: {df.columns.tolist()}")
        
        texts = df[text_col].fillna('').astype(str)
        labels = df['disaster'].fillna('unknown')
        
        # Filter out unknown disasters
        mask = labels != 'unknown'
        texts = texts[mask]
        labels = labels[mask]
        
        print(f"Text column: {text_col}")
        print(f"Label distribution:\n{labels.value_counts()}\n")
        
        return texts, labels
    
    def find_optimal_thresholds(self, model, X_val, y_val_encoded, model_name):
        """
        Find optimal classification thresholds to maximize precision.
        
        Args:
            model: Trained model
            X_val: Validation features
            y_val_encoded: Validation labels (encoded)
            model_name: Name of the model
            
        Returns:
            Dictionary of optimal thresholds per class
        """
        print(f"\nFinding optimal thresholds for {model_name} to maximize precision...")
        
        # Get prediction probabilities
        y_proba = model.predict_proba(X_val)
        
        # For each class, find threshold that maximizes precision while maintaining reasonable recall
        thresholds = {}
        
        for class_idx, class_name in enumerate(self.label_encoder.classes_):
            best_threshold = 0.5
            best_precision = 0
            
            # Try different thresholds
            for threshold in np.arange(0.3, 0.9, 0.05):
                # Create predictions based on this threshold
                temp_pred = np.zeros(len(y_proba))
                for i in range(len(y_proba)):
                    if y_proba[i, class_idx] >= threshold:
                        temp_pred[i] = class_idx
                    else:
                        # Assign to next highest probability class
                        probs_copy = y_proba[i].copy()
                        probs_copy[class_idx] = -1
                        temp_pred[i] = np.argmax(probs_copy)
                
                # Calculate precision for this class
                mask = y_val_encoded == class_idx
                if mask.sum() > 0:
                    pred_mask = temp_pred == class_idx
                    if pred_mask.sum() > 0:
                        precision = (temp_pred[mask] == class_idx).sum() / pred_mask.sum()
                        recall = (temp_pred[mask] == class_idx).sum() / mask.sum()
                        
                        # We want high precision but not at the cost of very low recall
                        if precision > best_precision and recall > 0.7:
                            best_precision = precision
                            best_threshold = threshold
            
            thresholds[class_name] = best_threshold
            print(f"  {class_name}: threshold = {best_threshold:.2f}")
        
        return thresholds
    
    def predict_with_threshold(self, model, X, thresholds=None):
        """
        Make predictions using custom thresholds.
        
        Args:
            model: Trained model
            X: Features
            thresholds: Dictionary of thresholds per class
            
        Returns:
            Predictions
        """
        y_proba = model.predict_proba(X)
        
        if thresholds is None:
            return model.predict(X)
        
        predictions = []
        for i in range(len(y_proba)):
            # Check if any class exceeds its threshold
            above_threshold = []
            for class_idx, class_name in enumerate(self.label_encoder.classes_):
                if y_proba[i, class_idx] >= thresholds[class_name]:
                    above_threshold.append((class_idx, y_proba[i, class_idx]))
            
            if above_threshold:
                # Choose the class with highest probability among those above threshold
                predictions.append(max(above_threshold, key=lambda x: x[1])[0])
            else:
                # If none above threshold, choose highest probability
                predictions.append(np.argmax(y_proba[i]))
        
        return np.array(predictions)
    
    def train(self, train_path: str, dev_path: str = None):
        """
        Train all three models.
        
        Args:
            train_path: Path to training JSONL file
            dev_path: Optional path to validation JSONL file for monitoring
        """
        print("=" * 60)
        print("LOADING AND PREPROCESSING TRAINING DATA")
        print("=" * 60)
        
        # Load training data
        train_df = self.load_jsonl(train_path)
        X_train_text, y_train = self.preprocess_data(train_df)
        
        # Fit vectorizer and transform training text
        print("Fitting TF-IDF vectorizer...")
        X_train = self.vectorizer.fit_transform(X_train_text)
        print(f"Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        print(f"Training matrix shape: {X_train.shape}\n")
        
        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        print(f"Classes: {self.label_encoder.classes_}\n")
        
        # Load validation data if provided
        X_dev = None
        y_dev_encoded = None
        if dev_path:
            print("Loading validation data...")
            dev_df = self.load_jsonl(dev_path)
            X_dev_text, y_dev = self.preprocess_data(dev_df)
            X_dev = self.vectorizer.transform(X_dev_text)
            y_dev_encoded = self.label_encoder.transform(y_dev)
            print()
        
        # Train each model
        print("=" * 60)
        print("TRAINING MODELS (Optimized for High Precision)")
        print("=" * 60)
        
        self.optimal_thresholds = {}
        
        for name, model in self.models.items():
            print(f"\nTraining {name.replace('_', ' ').title()}...")
            
            if name == 'xgboost' and dev_path:
                # XGBoost with early stopping
                model.fit(
                    X_train, y_train_encoded,
                    eval_set=[(X_dev, y_dev_encoded)],
                    verbose=False
                )
            else:
                model.fit(X_train, y_train_encoded)
            
            # Evaluate on training data
            train_pred = model.predict(X_train)
            train_acc = accuracy_score(y_train_encoded, train_pred)
            train_precision = precision_score(y_train_encoded, train_pred, average='weighted', zero_division=0)
            print(f"  Training accuracy: {train_acc:.4f}")
            print(f"  Training precision: {train_precision:.4f}")
            
            # Find optimal thresholds and evaluate on validation data if available
            if dev_path:
                # Find optimal thresholds
                thresholds = self.find_optimal_thresholds(model, X_dev, y_dev_encoded, name)
                self.optimal_thresholds[name] = thresholds
                
                # Evaluate with standard thresholds
                dev_pred = model.predict(X_dev)
                dev_acc = accuracy_score(y_dev_encoded, dev_pred)
                dev_precision = precision_score(y_dev_encoded, dev_pred, average='weighted', zero_division=0)
                dev_recall = recall_score(y_dev_encoded, dev_pred, average='weighted', zero_division=0)
                dev_f1 = f1_score(y_dev_encoded, dev_pred, average='weighted', zero_division=0)
                
                print(f"  Validation (standard thresholds):")
                print(f"    Accuracy: {dev_acc:.4f}")
                print(f"    Precision: {dev_precision:.4f}")
                print(f"    Recall: {dev_recall:.4f}")
                print(f"    F1-score: {dev_f1:.4f}")
                
                # Evaluate with optimized thresholds
                dev_pred_opt = self.predict_with_threshold(model, X_dev, thresholds)
                dev_acc_opt = accuracy_score(y_dev_encoded, dev_pred_opt)
                dev_precision_opt = precision_score(y_dev_encoded, dev_pred_opt, average='weighted', zero_division=0)
                dev_recall_opt = recall_score(y_dev_encoded, dev_pred_opt, average='weighted', zero_division=0)
                dev_f1_opt = f1_score(y_dev_encoded, dev_pred_opt, average='weighted', zero_division=0)
                
                print(f"  Validation (optimized thresholds):")
                print(f"    Accuracy: {dev_acc_opt:.4f}")
                print(f"    Precision: {dev_precision_opt:.4f} (↑{dev_precision_opt - dev_precision:+.4f})")
                print(f"    Recall: {dev_recall_opt:.4f} ({dev_recall_opt - dev_recall:+.4f})")
                print(f"    F1-score: {dev_f1_opt:.4f} ({dev_f1_opt - dev_f1:+.4f})")
        
        self.trained = True
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
    
    def evaluate(self, test_path: str, output_dir: str = './results', use_optimal_thresholds: bool = True):
        """
        Evaluate all models on test data and generate reports.
        
        Args:
            test_path: Path to test JSONL file
            output_dir: Directory to save results
            use_optimal_thresholds: Whether to use optimized thresholds
        """
        if not self.trained:
            raise ValueError("Models must be trained before evaluation")
        
        print("\n" + "=" * 60)
        print("EVALUATING ON TEST DATA")
        print("=" * 60)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load test data
        test_df = self.load_jsonl(test_path)
        X_test_text, y_test = self.preprocess_data(test_df)
        X_test = self.vectorizer.transform(X_test_text)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        results = {}
        
        # Evaluate each model
        for name, model in self.models.items():
            print(f"\n{'=' * 60}")
            print(f"{name.replace('_', ' ').title().upper()}")
            print('=' * 60)
            
            # Make predictions with standard and optimized thresholds
            y_pred_standard = model.predict(X_test)
            
            if use_optimal_thresholds and name in self.optimal_thresholds:
                y_pred = self.predict_with_threshold(model, X_test, self.optimal_thresholds[name])
                print("\nUsing optimized thresholds for maximum precision")
            else:
                y_pred = y_pred_standard
            
            # Calculate metrics
            accuracy = accuracy_score(y_test_encoded, y_pred)
            
            # Weighted averages
            precision_weighted = precision_score(y_test_encoded, y_pred, average='weighted', zero_division=0)
            recall_weighted = recall_score(y_test_encoded, y_pred, average='weighted', zero_division=0)
            f1_weighted = f1_score(y_test_encoded, y_pred, average='weighted', zero_division=0)
            
            # Macro averages
            precision_macro = precision_score(y_test_encoded, y_pred, average='macro', zero_division=0)
            recall_macro = recall_score(y_test_encoded, y_pred, average='macro', zero_division=0)
            f1_macro = f1_score(y_test_encoded, y_pred, average='macro', zero_division=0)
            
            # Calculate false positive rate per class
            cm = confusion_matrix(y_test_encoded, y_pred)
            fpr_per_class = {}
            for i, class_name in enumerate(self.label_encoder.classes_):
                # False positives: predicted as this class but actually other classes
                fp = cm[:, i].sum() - cm[i, i]
                # True negatives: correctly predicted as other classes
                tn = cm.sum() - cm[i, :].sum() - cm[:, i].sum() + cm[i, i]
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
                fpr_per_class[class_name] = fpr
            
            results[name] = {
                'accuracy': accuracy,
                'precision_weighted': precision_weighted,
                'recall_weighted': recall_weighted,
                'f1_weighted': f1_weighted,
                'precision_macro': precision_macro,
                'recall_macro': recall_macro,
                'f1_macro': f1_macro,
                'fpr_per_class': fpr_per_class
            }
            
            print(f"\nAccuracy: {accuracy:.4f}")
            print(f"\nWeighted Averages (accounts for class imbalance):")
            print(f"  Precision: {precision_weighted:.4f}")
            print(f"  Recall: {recall_weighted:.4f}")
            print(f"  F1-Score: {f1_weighted:.4f}")
            print(f"\nMacro Averages (treats all classes equally):")
            print(f"  Precision: {precision_macro:.4f}")
            print(f"  Recall: {recall_macro:.4f}")
            print(f"  F1-Score: {f1_macro:.4f}")
            print(f"\nFalse Positive Rate per class:")
            for class_name, fpr in fpr_per_class.items():
                print(f"  {class_name}: {fpr:.4f}")
            
            # Classification report
            print("\nDetailed Classification Report:")
            report = classification_report(
                y_test_encoded, 
                y_pred,
                target_names=self.label_encoder.classes_,
                digits=4
            )
            print(report)
            
            # Save classification report with all metrics
            with open(output_path / f'{name}_classification_report.txt', 'w') as f:
                f.write(f"Model: {name}\n")
                f.write(f"{'=' * 60}\n\n")
                f.write(f"Overall Metrics:\n")
                f.write(f"  Accuracy: {accuracy:.4f}\n\n")
                f.write(f"Weighted Averages (accounts for class imbalance):\n")
                f.write(f"  Precision: {precision_weighted:.4f}\n")
                f.write(f"  Recall: {recall_weighted:.4f}\n")
                f.write(f"  F1-Score: {f1_weighted:.4f}\n\n")
                f.write(f"Macro Averages (treats all classes equally):\n")
                f.write(f"  Precision: {precision_macro:.4f}\n")
                f.write(f"  Recall: {recall_macro:.4f}\n")
                f.write(f"  F1-Score: {f1_macro:.4f}\n\n")
                f.write(f"False Positive Rate per class:\n")
                for class_name, fpr in fpr_per_class.items():
                    f.write(f"  {class_name}: {fpr:.4f}\n")
                f.write(f"\n{'=' * 60}\n\n")
                f.write("Per-Class Metrics:\n\n")
                f.write(report)
            
            # Confusion matrix
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                cm, 
                annot=True, 
                fmt='d', 
                cmap='Blues',
                xticklabels=self.label_encoder.classes_,
                yticklabels=self.label_encoder.classes_
            )
            plt.title(f'Confusion Matrix - {name.replace("_", " ").title()}')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
            plt.tight_layout()
            plt.savefig(output_path / f'{name}_confusion_matrix.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # Compare models
        print("\n" + "=" * 60)
        print("MODEL COMPARISON")
        print("=" * 60)
        
        # Create comparison dataframe without fpr_per_class
        comparison_data = {}
        for model_name, metrics in results.items():
            comparison_data[model_name] = {k: v for k, v in metrics.items() if k != 'fpr_per_class'}
        
        comparison_df = pd.DataFrame(comparison_data).T
        comparison_df = comparison_df.round(4)
        print("\n", comparison_df)
        
        # Save detailed comparison
        comparison_df.to_csv(output_path / 'model_comparison.csv')
        
        # Create a more readable comparison table
        print("\n" + "=" * 60)
        print("SUMMARY TABLE")
        print("=" * 60)
        summary_table = comparison_df[['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']]
        summary_table.columns = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        print("\n", summary_table)
        summary_table.to_csv(output_path / 'model_comparison_summary.csv')
        
        # Save FPR data separately
        fpr_data = {}
        for model_name, metrics in results.items():
            for class_name, fpr in metrics['fpr_per_class'].items():
                if class_name not in fpr_data:
                    fpr_data[class_name] = {}
                fpr_data[class_name][model_name] = fpr
        
        fpr_df = pd.DataFrame(fpr_data).T
        fpr_df.to_csv(output_path / 'false_positive_rates.csv')
        print(f"\nFalse Positive Rates by Class:")
        print(fpr_df.round(4))
        
        # Plot comprehensive comparison
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Model Performance Comparison', fontsize=16, fontweight='bold')
        
        metrics = [
            ('accuracy', 'Accuracy'),
            ('precision_weighted', 'Precision (Weighted)'),
            ('recall_weighted', 'Recall (Weighted)'),
            ('f1_weighted', 'F1-Score (Weighted)')
        ]
        
        axes = axes.flatten()
        
        for idx, (metric, title) in enumerate(metrics):
            ax = axes[idx]
            values = [results[model][metric] for model in self.models.keys()]
            model_names = [name.replace('_', ' ').title() for name in self.models.keys()]
            
            bars = ax.bar(model_names, values, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
            ax.set_ylabel('Score', fontsize=11)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_ylim([0, 1])
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.4f}',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path / 'model_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create additional comparison plot for macro vs weighted metrics
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Weighted vs Macro Averages Comparison', fontsize=16, fontweight='bold')
        
        metric_pairs = [
            ('precision', 'Precision'),
            ('recall', 'Recall'),
            ('f1', 'F1-Score')
        ]
        
        x = np.arange(len(self.models))
        width = 0.35
        
        for idx, (metric_base, title) in enumerate(metric_pairs):
            ax = axes[idx]
            
            weighted_values = [results[model][f'{metric_base}_weighted'] for model in self.models.keys()]
            macro_values = [results[model][f'{metric_base}_macro'] for model in self.models.keys()]
            model_names = [name.replace('_', '\n').title() for name in self.models.keys()]
            
            bars1 = ax.bar(x - width/2, weighted_values, width, label='Weighted', color='#2ca02c')
            bars2 = ax.bar(x + width/2, macro_values, width, label='Macro', color='#d62728')
            
            ax.set_ylabel('Score', fontsize=11)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(model_names, fontsize=10)
            ax.set_ylim([0, 1])
            ax.legend(fontsize=10)
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                           f'{height:.3f}',
                           ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_path / 'weighted_vs_macro_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot False Positive Rates
        fig, ax = plt.subplots(figsize=(12, 6))
        fpr_df.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax.set_title('False Positive Rate by Class and Model', fontsize=14, fontweight='bold')
        ax.set_ylabel('False Positive Rate', fontsize=11)
        ax.set_xlabel('Disaster Class', fontsize=11)
        ax.legend(title='Model', labels=[name.replace('_', ' ').title() for name in self.models.keys()])
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path / 'false_positive_rates.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nResults saved to: {output_path}")
        print(f"\nGenerated files:")
        print(f"  - model_comparison.csv (all metrics)")
        print(f"  - model_comparison_summary.csv (main metrics)")
        print(f"  - false_positive_rates.csv (FPR by class)")
        print(f"  - model_comparison.png (accuracy, precision, recall, F1)")
        print(f"  - weighted_vs_macro_comparison.png (weighted vs macro averages)")
        print(f"  - false_positive_rates.png (FPR visualization)")
        print(f"  - *_classification_report.txt (detailed per-model reports)")
        print(f"  - *_confusion_matrix.png (confusion matrices)")
        
        return results
    
    def save_models(self, output_dir: str = './models'):
        """
        Save trained models in the 3-file structure per model:
        - model.joblib (the trained model)
        - vectorizer.joblib (shared vectorizer)
        - config.json (model configuration and metadata)
        
        Args:
            output_dir: Directory to save models
        """
        if not self.trained:
            raise ValueError("Models must be trained before saving")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSaving models to: {output_path}")
        
        # Get timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save shared label encoder (all models use the same one)
        label_encoder_file = f"label_encoder_{timestamp}.joblib"
        joblib.dump(self.label_encoder, output_path / label_encoder_file)
        print(f"  ✓ Saved {label_encoder_file}")
        
        # Save each model with its own 3-file structure
        for model_name, model in self.models.items():
            print(f"\n  Saving {model_name.replace('_', ' ').title()}:")
            
            # File names with timestamp
            model_file = f"{model_name}_model_{timestamp}.joblib"
            vectorizer_file = f"{model_name}_vectorizer_{timestamp}.joblib"
            config_file = f"{model_name}_config_{timestamp}.json"
            
            # Save the model
            joblib.dump(model, output_path / model_file)
            print(f"    ✓ {model_file}")
            
            # Save the vectorizer (each model gets its own copy for independence)
            joblib.dump(self.vectorizer, output_path / vectorizer_file)
            print(f"    ✓ {vectorizer_file}")
            
            # Get average threshold for this model
            avg_threshold = 0.5
            thresholds_dict = {}
            if model_name in self.optimal_thresholds:
                thresholds_dict = self.optimal_thresholds[model_name]
                avg_threshold = np.mean(list(thresholds_dict.values()))
            
            # Create config dictionary
            config = {
                "threshold": float(avg_threshold),
                "thresholds_per_class": {k: float(v) for k, v in thresholds_dict.items()},
                "model_file": model_file,
                "vectorizer_file": vectorizer_file,
                "label_encoder_file": label_encoder_file,
                "created_at": timestamp,
                "model_type": type(model).__name__,
                "classes": self.label_encoder.classes_.tolist(),
                "max_features": self.max_features,
                "random_state": self.random_state,
                "model_params": model.get_params() if hasattr(model, 'get_params') else {}
            }
            
            # Save config
            with open(output_path / config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"    ✓ {config_file}")
            
            # Store config reference for later use
            self.model_configs[model_name] = config
        
        # Save a master index file that lists all models
        master_index = {
            "timestamp": timestamp,
            "label_encoder_file": label_encoder_file,
            "models": {}
        }
        
        for model_name in self.models.keys():
            master_index["models"][model_name] = {
                "model_file": f"{model_name}_model_{timestamp}.joblib",
                "vectorizer_file": f"{model_name}_vectorizer_{timestamp}.joblib",
                "config_file": f"{model_name}_config_{timestamp}.json"
            }
        
        with open(output_path / f"models_index_{timestamp}.json", 'w') as f:
            json.dump(master_index, f, indent=2)
        print(f"\n  ✓ Saved models_index_{timestamp}.json")
        
        print(f"\n{'=' * 60}")
        print("All models saved successfully!")
        print(f"{'=' * 60}")
        print(f"\nEach model has 3 files:")
        print(f"  1. *_model_*.joblib - The trained classifier")
        print(f"  2. *_vectorizer_*.joblib - The TF-IDF vectorizer")
        print(f"  3. *_config_*.json - Configuration and metadata")
    
    def load_single_model(self, model_path: str, vectorizer_path: str, config_path: str, model_key: str = None):
        """
        Load a single model from the 3-file structure.
        
        Args:
            model_path: Path to model .joblib file
            vectorizer_path: Path to vectorizer .joblib file
            config_path: Path to config .json file
            model_key: Optional key to store the model under (if None, uses model_type from config)
        """
        print(f"Loading model from:")
        print(f"  Model: {model_path}")
        print(f"  Vectorizer: {vectorizer_path}")
        print(f"  Config: {config_path}")
        
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Load model
        model = joblib.load(model_path)
        print(f"  ✓ Loaded model: {config['model_type']}")
        
        # Load vectorizer
        vectorizer = joblib.load(vectorizer_path)
        print(f"  ✓ Loaded vectorizer")
        
        # Determine the key to store this model under
        if model_key is None:
            model_type = config['model_type'].lower()
            if 'logistic' in model_type:
                model_key = 'logistic_regression'
            elif 'random' in model_type or 'forest' in model_type:
                model_key = 'random_forest'
            elif 'xgb' in model_type or 'xgboost' in model_type:
                model_key = 'xgboost'
            else:
                model_key = 'custom_model'
        
        # Store the model
        self.models[model_key] = model
        self.vectorizer = vectorizer
        self.model_configs[model_key] = config
        
        # Load label encoder if specified and not already loaded
        if 'label_encoder_file' in config and self.label_encoder is None:
            label_encoder_path = Path(config_path).parent / config['label_encoder_file']
            if label_encoder_path.exists():
                self.label_encoder = joblib.load(label_encoder_path)
                print(f"  ✓ Loaded label encoder")
        
        # Load thresholds if available
        if 'thresholds_per_class' in config:
            self.optimal_thresholds[model_key] = config['thresholds_per_class']
            print(f"  ✓ Loaded optimal thresholds")
        
        self.trained = True
        print(f"  ✓ Model loaded as '{model_key}'")
        
        return model_key
    
    def load_models_from_directory(self, models_dir: str, timestamp: str = None):
        """
        Load all models from a directory using the master index file.
        
        Args:
            models_dir: Directory containing saved models
            timestamp: Optional timestamp to load specific model set (if None, loads most recent)
        """
        models_path = Path(models_dir)
        
        if not models_path.exists():
            raise ValueError(f"Models directory '{models_dir}' does not exist")
        
        # Find master index file
        if timestamp:
            index_file = models_path / f"models_index_{timestamp}.json"
        else:
            # Find the most recent index file
            index_files = sorted(models_path.glob("models_index_*.json"), reverse=True)
            if not index_files:
                raise ValueError(f"No model index files found in '{models_dir}'")
            index_file = index_files[0]
        
        print(f"Loading models from index: {index_file.name}")
        
        # Load master index
        with open(index_file, 'r') as f:
            master_index = json.load(f)
        
        # Load label encoder
        label_encoder_path = models_path / master_index['label_encoder_file']
        self.label_encoder = joblib.load(label_encoder_path)
        print(f"  ✓ Loaded {master_index['label_encoder_file']}")
        
        # Load each model
        for model_name, files in master_index['models'].items():
            print(f"\nLoading {model_name.replace('_', ' ').title()}:")
            
            model_path = models_path / files['model_file']
            vectorizer_path = models_path / files['vectorizer_file']
            config_path = models_path / files['config_file']
            
            self.load_single_model(
                str(model_path),
                str(vectorizer_path),
                str(config_path),
                model_key=model_name
            )
        
        print(f"\n{'=' * 60}")
        print("All models loaded successfully!")
        print(f"{'=' * 60}")
    
    def predict(self, texts, model_name='xgboost', use_optimal_threshold=True):
        """
        Predict disaster types for new texts.
        
        Args:
            texts: List of text strings or single text string
            model_name: Which model to use for prediction
            use_optimal_threshold: Whether to use optimized thresholds
            
        Returns:
            Predicted disaster types
        """
        if not self.trained:
            raise ValueError("Models must be trained before prediction")
        
        if isinstance(texts, str):
            texts = [texts]
        
        X = self.vectorizer.transform(texts)
        
        if use_optimal_threshold and self.optimal_thresholds and model_name in self.optimal_thresholds:
            y_pred_encoded = self.predict_with_threshold(
                self.models[model_name], 
                X, 
                self.optimal_thresholds[model_name]
            )
        else:
            y_pred_encoded = self.models[model_name].predict(X)
        
        y_pred = self.label_encoder.inverse_transform(y_pred_encoded)
        
        return y_pred
    
    def predict_proba(self, texts, model_name='xgboost'):
        """
        Get prediction probabilities for new texts.
        
        Args:
            texts: List of text strings or single text string
            model_name: Which model to use for prediction
            
        Returns:
            Probability matrix (n_samples, n_classes) and class names
        """
        if not self.trained:
            raise ValueError("Models must be trained before prediction")
        
        if isinstance(texts, str):
            texts = [texts]
        
        X = self.vectorizer.transform(texts)
        probabilities = self.models[model_name].predict_proba(X)
        
        return probabilities, self.label_encoder.classes_


def load_disaster_classifier(model_path: str, vectorizer_path: str, config_path: str):
    """
    Convenience function to load a single disaster classifier.
    
    Args:
        model_path: Path to model .joblib file
        vectorizer_path: Path to vectorizer .joblib file
        config_path: Path to config .json file
        
    Returns:
        DisasterClassifier instance with loaded model
    """
    classifier = DisasterClassifier()
    classifier.load_single_model(model_path, vectorizer_path, config_path)
    return classifier


def main():
    parser = argparse.ArgumentParser(description='Train and evaluate disaster tweet classifiers')
    parser.add_argument('--train', required=True, help='Path to training JSONL file')
    parser.add_argument('--dev', required=True, help='Path to validation JSONL file')
    parser.add_argument('--test', required=True, help='Path to test JSONL file')
    parser.add_argument('--output', default='./results', help='Output directory for results')
    parser.add_argument('--models-dir', default='./models', help='Directory to save/load models')
    parser.add_argument('--load-models', action='store_true', help='Load previously trained models')
    parser.add_argument('--load-timestamp', type=str, help='Specific timestamp to load (YYYYMMDD_HHMMSS)')
    parser.add_argument('--max-features', type=int, default=5000, help='Max features for TF-IDF')
    parser.add_argument('--no-optimal-thresholds', action='store_true', help='Disable optimal threshold tuning')
    
    args = parser.parse_args()
    
    # Initialize classifier
    print("Initializing Disaster Classifier...")
    print("Note: Models optimized to minimize false positives (maximize precision)")
    classifier = DisasterClassifier(max_features=args.max_features)
    
    if args.load_models:
        # Load existing models
        classifier.load_models_from_directory(args.models_dir, args.load_timestamp)
    else:
        # Train models
        classifier.train(args.train, args.dev)
        
        # Save models automatically after training
        classifier.save_models(args.models_dir)
    
    # Evaluate models
    use_thresholds = not args.no_optimal_thresholds
    results = classifier.evaluate(args.test, args.output, use_optimal_thresholds=use_thresholds)
    
    # Example predictions
    print("\n" + "=" * 60)
    print("EXAMPLE PREDICTIONS")
    print("=" * 60)
    
    example_tweets = [
        "Earthquake hits California, buildings collapsed",
        "Hurricane warning issued for the coast",
        "Massive wildfire spreading through the forest",
        "Severe flooding in the city streets"
    ]
    
    for model_name in classifier.models.keys():
        print(f"\n{model_name.replace('_', ' ').title()}:")
        predictions = classifier.predict(example_tweets, model_name, use_optimal_threshold=use_thresholds)
        probabilities, classes = classifier.predict_proba(example_tweets, model_name)
        
        for tweet, pred, proba in zip(example_tweets, predictions, probabilities):
            max_prob = proba.max()
            print(f"  '{tweet[:50]}...' -> {pred} (confidence: {max_prob:.3f})")
    
    # Print loading instructions
    print("\n" + "=" * 60)
    print("USAGE INSTRUCTIONS")
    print("=" * 60)
    print("\nTo load a single model in your code:")
    print("```python")
    print("from classifier import load_disaster_classifier")
    print("")
    print("classifier = load_disaster_classifier(")
    print("    model_path='models/logistic_regression_model_TIMESTAMP.joblib',")
    print("    vectorizer_path='models/logistic_regression_vectorizer_TIMESTAMP.joblib',")
    print("    config_path='models/logistic_regression_config_TIMESTAMP.json'")
    print(")")
    print("")
    print("# Make predictions")
    print("predictions = classifier.predict(['Earthquake in California'])")
    print("```")
    print("\nTo load all models:")
    print("```python")
    print("from classifier import DisasterClassifier")
    print("")
    print("classifier = DisasterClassifier()")
    print("classifier.load_models_from_directory('./models')")
    print("```")


if __name__ == "__main__":
    main()