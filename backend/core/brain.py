import nltk
from sentence_transformers import SentenceTransformer

# Download the punkt tokenizer for sentence splitting
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

class NLPProcessor:
    def __init__(self):
        # Load the high-accuracy SBERT model
        # all-mpnet-base-v2 produces 768-dimensional vectors
        self.model = SentenceTransformer('all-mpnet-base-v2')

    def get_chunks(self, text):
        """
        Breaks text into paragraphs and sentences.
        """
        # 1. Paragraph Chunking (Splits by double newlines)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # 2. Sentence Chunking (Using NLTK's intelligent tokenizer)
        sentences = nltk.sent_tokenize(text)
        
        return paragraphs, sentences

    def generate_embeddings(self, text_list):
        """
        Converts a list of strings into a list of 768-dim vectors.
        """
        # The model.encode function handles the deep learning math
        embeddings = self.model.encode(text_list)
        
        # Convert numpy arrays to lists so they can be stored in Postgres
        return embeddings.tolist()

# --- Quick Test ---
if __name__ == "__main__":
    processor = NLPProcessor()
    sample_text = "Artificial Intelligence is transforming the world. It is a subset of Computer Science."
    
    paras, sents = processor.get_chunks(sample_text)
    print(f"Sentences found: {len(sents)}")
    
    vectors = processor.generate_embeddings(sents)
    print(f"Vector length: {len(vectors[0])}") # Should be 768