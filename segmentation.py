import torch
import torch.nn as nn
import torch.nn.functional as F
import spacy
import numpy as np
import random
from scipy.signal import find_peaks
import os

# Set random seed for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

# Load spaCy tokenizer
nlp = spacy.load("en_core_web_sm")

def get_base_path():
    """Return the base path dynamically (works across devices)."""
    return os.path.dirname(os.path.realpath(__file__))

def load_text_file(file_path):
    """Load transcript with sentence-level timestamps."""
    sentences = []
    timestamps = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 3):
      if i + 1 >= len(lines):  # Skip if not enough lines left
          continue

      time_range = lines[i].strip().split(" --> ")

      # Skip invalid time ranges
      if len(time_range) != 2:
          continue

      try:
          start_time = float(time_range[0])
          end_time = float(time_range[1])
      except ValueError:
          continue

      text = lines[i + 1].strip()

      if text:  # Only add if text is not empty
          sentences.append(text)
          timestamps.append((start_time, end_time))

    tokens = [token.text for sent in sentences for token in nlp(sent)]
    return sentences, tokens, timestamps


class Encoder(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super(Encoder, self).__init__()
        self.hidden_dim = hidden_dim
        self.bigru = nn.GRU(input_dim, hidden_dim, bidirectional=True, batch_first=True)

    def forward(self, x):
        h, _ = self.bigru(x)
        return h  # h ∈ R^(N × 2H)


class Decoder(nn.Module):
    def __init__(self, hidden_dim):
        super(Decoder, self).__init__()
        self.hidden_dim = hidden_dim
        self.gru = nn.GRU(hidden_dim * 2, hidden_dim, batch_first=True)

    def forward(self, x, hidden_state):
        d, hidden_state = self.gru(x, hidden_state)
        return d, hidden_state


class Pointer(nn.Module):
    def __init__(self, encoder_hidden_dim, decoder_hidden_dim):
        super(Pointer, self).__init__()
        self.W1 = nn.Linear(encoder_hidden_dim, decoder_hidden_dim)
        self.W2 = nn.Linear(decoder_hidden_dim, decoder_hidden_dim)
        self.v = nn.Linear(decoder_hidden_dim, 1, bias=False)

    def forward(self, encoder_outputs, decoder_state):
        scores = self.v(torch.tanh(self.W1(encoder_outputs) + self.W2(decoder_state)))
        attention_weights = F.softmax(scores, dim=1)
        return attention_weights


class SEGBOT(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super(SEGBOT, self).__init__()
        self.encoder = Encoder(input_dim, hidden_dim)
        self.decoder = Decoder(hidden_dim)
        self.pointer = Pointer(hidden_dim * 2, hidden_dim)

    def forward(self, x, start_units):
        encoder_outputs = self.encoder(x)
        decoder_hidden = torch.zeros(1, x.size(0), self.decoder.hidden_dim).to(x.device)
        decoder_inputs = encoder_outputs[:, start_units, :].unsqueeze(1)
        decoder_outputs, _ = self.decoder(decoder_inputs, decoder_hidden)
        attention_weights = self.pointer(encoder_outputs, decoder_outputs.squeeze(1))
        return attention_weights

    def segment_text(self, sentences, tokens, timestamps, attention_weights):
        """Segment text and get start/end timestamps."""
        attention_weights = attention_weights.squeeze().detach().cpu().numpy()

        # Normalize attention weights
        attention_weights = (attention_weights - np.min(attention_weights)) / (
            np.max(attention_weights) - np.min(attention_weights)
        )

        # Find peaks in attention scores
        peak_indices, _ = find_peaks(attention_weights, height=0.5, distance=5)

        if len(peak_indices) == 0:
            return [{"text": " ".join(sentences), "start_time": timestamps[0][0], "end_time": timestamps[-1][1]}]

        segments = []
        start_idx = 0
        for i in peak_indices:
          if i > 0 and i - start_idx >= 5:  # Ensure valid range and at least 5 sentences per segment
              segment_text = " ".join(sentences[start_idx:i]).strip()

              if segment_text:
                  start_time = timestamps[start_idx][0]

                  # Check if `i - 1` is within range to prevent out-of-bounds error
                  if i - 1 < len(timestamps):
                      end_time = timestamps[i - 1][1]
                  else:
                      end_time = timestamps[-1][1]  # Fallback to the last timestamp

                  segments.append({"text": segment_text, "start_time": start_time, "end_time": end_time})

              start_idx = i


        # Add last segment
        last_segment = " ".join(sentences[start_idx:]).strip()
        if last_segment:
            start_time = timestamps[start_idx][0]
            end_time = timestamps[-1][1]
            segments.append({"text": last_segment, "start_time": start_time, "end_time": end_time})

        return segments if segments else None


# Model Hyperparameters
input_dim = 128  # Example input size
hidden_dim = 256  # Hidden layer size
model = SEGBOT(input_dim, hidden_dim)

# Load text file and process with sentence-level timestamps
file_path = os.path.join(get_base_path(), 'sentence_timestamps.txt')  # Dynamic path
sentences, tokens, timestamps = load_text_file(file_path)

# Example Input (Dummy Tensor)
x = torch.randn(1, len(tokens), input_dim)  # Batch size of 1, sequence length based on text
start_units = 0
output = model(x, start_units)

# Segment the text and get timestamps
segments = model.segment_text(sentences, tokens, timestamps, output)

# Save segmented transcript with timestamps
output_path = os.path.join(get_base_path(), 'segmented_transcript_with_timestamps.txt')  # Dynamic path
if segments:
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments):
            start_time = segment["start_time"]
            end_time = segment["end_time"]
            text = segment["text"]
            f.write(f"Segment {i+1} [{start_time:.2f}s - {end_time:.2f}s]:\n{text}\n\n")
    print(f"Segmented transcript with timestamps saved successfully to {output_path}")
else:
    print("No valid segments found. Terminating execution.")
