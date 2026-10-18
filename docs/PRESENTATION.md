# Prototype presentation outline

## 60-90 second explanation

“This prototype demonstrates the core loop behind autoregressive language generation. First, it tokenizes a small training corpus into words. During training, it counts which word tends to follow each previous word. During inference, it uses those counts as a probability distribution, samples a next word, and repeats the process to generate a response.s

## Live demo

1. Run `.\run`.
2. Enter `language models`.
3. Add a new sentence to `data/processed/physiology_training.txt`.
4. Run it again and show that the learned output changes.

## Honest takeaway

The project is a learning scaffold. The next engineering step would be replacing the counting model with a tiny Transformer, then measuring training loss and validation performance.
