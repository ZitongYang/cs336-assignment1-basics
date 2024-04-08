# pytest /home/groups/candes/zitong/cs336-assignment1-basics/tests/test_train_bpe.py
import regex as re
from typing import Iterable
from tqdm import tqdm
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from cs336_basics.utils import GPT2_PRETOKENIZER_PATTERN


def _update_byte_tuple(byte_tuple: Iterable[bytes], merge_loc: int):
    """
    Merge the byte tuple at the merge location.
    """
    assert len(byte_tuple) > 1, "Cannot merge a byte tuple with length less than 2."
    prefix = byte_tuple[:merge_loc]
    tomerge = byte_tuple[merge_loc:merge_loc+2]
    suffix = byte_tuple[merge_loc+2:]
    new_byte_tuple = prefix + (b"".join(tomerge),) + suffix
    return new_byte_tuple, prefix, suffix

def train_bpe(input_path: str, vocab_size: int, special_tokens: Iterable[str],
              progress_bar: bool = False):
    """
    Train a byte pair encoding tokenizer on the input text file.

    Args:
        input_path: Path to the input text file.
        vocab_size: Size of the vocabulary.
        special_tokens: List of special tokens to add to the vocabulary.

    Returns:
        Tuple of the learned vocab and merges.
    """
    # Read the input text file
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Initialize the vocab with 256 bytes and sepcial tokens
    vocab = {i: bytes([i]) for i in range(256)}
    for i, token in enumerate(special_tokens):
        vocab[256+i] = token.encode("utf-8")

    # Remove special tokens from teh text
    for token in special_tokens:
        text = text.replace(token, "")
    
    logging.info("Initializing pretoken frequency table")
    pretoken_freq = {}
    pretokes = re.findall(GPT2_PRETOKENIZER_PATTERN, text)
    for pretoken in tqdm(pretokes, disable=not progress_bar):
        pretoken_tuple = tuple([bytes([b]) for b in tuple(pretoken.encode("utf-8"))])
        if pretoken_tuple not in pretoken_freq:
            pretoken_freq[pretoken_tuple] = 0
        pretoken_freq[pretoken_tuple] += 1
    
    logging.info("Initializing byte pair frequency table")
    pair_freq = {}
    for pretoken_tuple, freq in tqdm(pretoken_freq.items(), disable=not progress_bar):
        for i in range(len(pretoken_tuple) - 1):
            pair = pretoken_tuple[i:i+2]
            if pair not in pair_freq:
                pair_freq[pair] = 0
            pair_freq[pair] += freq
    
    logging.info("Performing BPE algorithm")
    pbar = tqdm(total=vocab_size) if progress_bar else None
    merges = []
    while len(vocab) < vocab_size:
        # Find the most frequent pair
        most_freq_pair = max(pair_freq, key=lambda k: (pair_freq[k], k))

        # Add the pair to the merges list
        merges.append(most_freq_pair)
        
        # Update the vocab
        new_id = max(vocab.keys()) + 1
        vocab[new_id] = b"".join(most_freq_pair)

        # Update the pre-token frequency table and pair frequency table
        new_pretoken_freq = {}
        for pretoken_tuple, freq in pretoken_freq.items():
            i=0
            while i < len(pretoken_tuple):
                pair = pretoken_tuple[i:i+2]
                if pair == most_freq_pair:
                    pretoken_tuple, prefix, suffix = _update_byte_tuple(pretoken_tuple, i)

                    # Update the pair frequency table
                    if prefix:
                        add_pair = (prefix[-1], vocab[new_id])
                        pair_freq[add_pair] = pair_freq.get(add_pair, 0) + freq
                        del_pair = (prefix[-1], most_freq_pair[0])
                        pair_freq[del_pair] -= freq
                    if suffix:
                        add_pair = (vocab[new_id], suffix[0])
                        pair_freq[add_pair] = pair_freq.get(add_pair, 0) + freq
                        del_pair = (most_freq_pair[1], suffix[0])
                        pair_freq[del_pair] -= freq
                    pair_freq[most_freq_pair] -= freq
                i+=1
            # Update the pre-token frequency table
            new_pretoken_freq[pretoken_tuple] = freq
        pretoken_freq = new_pretoken_freq
        pbar.update(len(vocab) - pbar.n) if progress_bar else None
    pbar.close() if progress_bar else None

    return vocab, merges
        

    

    
if __name__ == '__main__':
    # print(_contain_pair((b'ads', b'q', b'bs', b'c', b'd', b'bs', b'c'), (b'bs', b'c'))) 
    # print(_merge_byte_tuple((b'ads', b'q', b'bs', b'c', b'd', b'bs', b'c'), [2, 5]))


    txt_path = '/home/groups/candes/zitong/cs336-assignment1-basics/tests/fixtures/corpus.en'
    special_tokens = ['<|endoftext|>']
    vocab_size = 100*(10**3)
    train_bpe(txt_path, vocab_size, special_tokens)

    # txt_path = '/home/groups/candes/zitong/cs336-assignment1-basics/cs336_basics/test_text.txt'
    # special_tokens = ['<|endoftext|>']
    # vocab_size = 1000
    # train_bpe(txt_path, vocab_size, special_tokens)