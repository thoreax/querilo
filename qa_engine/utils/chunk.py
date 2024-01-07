from typing import List, Tuple
import re


def chunk_corpus(corpus: str, chunk_size: int, sentence_word_count: Tuple[int, int]) -> List[
    List[str]]:
    all_sentences = []
    count_words = lambda sentence: sum([len(word.split(" ")) for word in sentence])
    sentence_acc = []

    # split if you see a dot followed by a space followed by a capital letter or a [

    for sentence in re.split(r"\. (?=[A-Z\[])|\.\[", corpus):
        if count_words(sentence_acc) + count_words(sentence) >= sentence_word_count[1]:

            if sentence_acc:
                all_sentences.append(".".join(sentence_acc))
            sentence_acc = [sentence]
        else:
            sentence_acc.append(sentence)

    # add leftover sentences
    if len(sentence_acc) > 0:
        all_sentences.append(".".join(sentence_acc))

    # now we have a list of chunks, we need to split them into smaller chunks according to chunk_size
    chunks = []
    stride = chunk_size
    ni = (len(all_sentences) + stride - 1) // stride

    for i in range(ni):
        start_index = i * stride
        end_index = min(start_index + stride, len(all_sentences))
        chunk = all_sentences[start_index:end_index]
        chunks.append(chunk)

    return chunks


def show_chunk(chunk):
    for i, sentence in enumerate(chunk):
        print(f"{i + 1} :: {sentence}")
