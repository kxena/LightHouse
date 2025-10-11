import joblib
import json
import pandas as pd
import re
import string
from langdetect import detect, LangDetectException

class DisasterClassifier:
    """
    A reusable disaster tweet classifier that loads a pre-trained model.
    """
    
    def __init__(self, model_path, vectorizer_path, config_path):
        """
        Initialize the classifier by loading saved model components.
        
        Parameters:
        - model_path: Path to saved model file (.joblib)
        - vectorizer_path: Path to saved vectorizer file (.joblib)
        - config_path: Path to configuration file (.json)
        """
        print("Loading model components...")
        
        # Load model
        self.model = joblib.load(model_path)
        print(f"✓ Model loaded from: {model_path}")
        
        # Load vectorizer
        self.vectorizer = joblib.load(vectorizer_path)
        print(f"✓ Vectorizer loaded from: {vectorizer_path}")
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.threshold = self.config['threshold']
        print(f"✓ Configuration loaded. Threshold: {self.threshold:.3f}")
        
        print("Classifier ready to use!")
    
    def preprocess_text(self, text):
        """
        Preprocess a single tweet text.
        (Same preprocessing as training)
        """
        import re
        import string
        
        if pd.isna(text):
            return ""
        
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#', '', text)
        
        # Remove emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FAFF"
            "\U00002500-\U00002BEF"
            "\U0001F000-\U0001F02F"
            "\U0001F0A0-\U0001F0FF"
            "\U00002300-\U000023FF"
            "\U00002B00-\U00002BFF"
            "\U0000FE00-\U0000FE0F"
            "\U0001F200-\U0001F2FF"
            "]+", 
            flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
        
        text = re.sub(r'\b\d+\.?\d*\b', '', text)
        text = re.sub(r'\d{4}-\d{2}-\d{2}', '', text)
        text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ' '.join(text.split())
        
        return text
    
    def detect_language(self, text):
        """
        Detect the language of the text.
        """
        from langdetect import detect, LangDetectException
        
        if pd.isna(text) or text.strip() == '':
            return 'unknown'
        
        try:
            return detect(text)
        except LangDetectException:
            return 'unknown'
    
    def predict_single(self, text):
        """
        Predict if a single tweet is about a natural disaster.
        
        Parameters:
        - text: Tweet text (string)
        
        Returns:
        - Dictionary with prediction results
        """
        # Detect language
        language = self.detect_language(text)
        
        # Auto-classify non-English as non-disaster
        if language != 'en':
            return {
                'text': text,
                'language': language,
                'is_disaster': False,
                'confidence': 0.0,
                'reason': 'Non-English tweet (auto-classified as non-disaster)'
            }
        
        # Preprocess text
        cleaned_text = self.preprocess_text(text)
        
        # Transform using vectorizer
        text_vector = self.vectorizer.transform([cleaned_text])
        
        # Get prediction probability
        probability = self.model.predict_proba(text_vector)[0, 1]
        
        # Apply threshold
        is_disaster = probability >= self.threshold
        
        return {
            'text': text,
            'language': language,
            'is_disaster': bool(is_disaster),
            'confidence': float(probability),
            'threshold': self.threshold
        }
    
    def predict_batch(self, texts):
        """
        Predict for multiple tweets at once.
        
        Parameters:
        - texts: List of tweet texts
        
        Returns:
        - List of dictionaries with prediction results
        """
        results = []
        for text in texts:
            results.append(self.predict_single(text))
        return results
    
    def predict_from_jsonl(self, input_file, output_file=None):
        """
        Predict for tweets in a JSONL file.
        
        Parameters:
        - input_file: Path to input JSONL file
        - output_file: Path to output JSONL file (optional)
        
        Returns:
        - List of prediction results
        """
        results = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                tweet = json.loads(line)
                text = tweet.get('text', '')
                
                prediction = self.predict_single(text)
                prediction['id'] = idx
                
                results.append(prediction)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(result) + '\n')
            print(f"Predictions saved to: {output_file}")
        
        return results