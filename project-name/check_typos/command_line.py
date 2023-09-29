from collections import defaultdict
from pathlib import Path
import string
from Levenshtein import distance as levenshtein_distance


MINIMUM_CHANCES = 3000  # arbitrary cutoff
PUNC_LIST = ".!?,;:'\"'()[]®\\"  # Gets stripped from around, but not inside, words


def discard_word(word):
    if word in ["", "l_english:"]:
        return True
    for c in word:
        if c.isnumeric():
            return True
    return False


def strip_magic_word(line, lsep, rsep):
    lsep_position = line.find(lsep)
    if lsep_position >= 0:
        rsep_position = line[lsep_position + 1 :].find(rsep) + lsep_position
        if rsep_position >= lsep_position:
            # found one!
            result = strip_magic_word(line[:lsep_position] + line[(rsep_position + 1) :], lsep, rsep)
            return result
    return line


def clean_line(line):
    comment_pos = line.find("#")
    if comment_pos >= 0:
        # has an EOL comment, remove
        line = line[:comment_pos]
    # Remove some variables
    line = strip_magic_word(line, "[", "]")
    line = strip_magic_word(line, "§", "§")
    # Remve newlines, em & en hyphens
    line = (
        line.strip()
        .replace("\n", " ")
        .replace(r"\n", " ")
        .replace("-", " ")
        .replace("—", " ")
        .replace("–", " ")
        .replace("...", " ")
        .replace("‘", "'")
        .replace("’", "'")
    )
    # first word is a key, not interesting
    return line.split(" ")[1:]


def clean_word(word):
    return word.strip(PUNC_LIST).lower().strip()


def parse_file(file_path, word_count: defaultdict):
    with open(file_path, encoding="utf-8-sig") as f:
        text = f.read()
        for line in text.split("\n"):
            for word in clean_line(line):
                word = clean_word(word)
                if discard_word(word):
                    continue
                word_count[word] += 1


def main():
    word_count = defaultdict(int)
    root_path = Path("C:\Projects\equestria_dev") / "localisation" / "english"
    # file_paths = [root_path / "country_BOI_l_english.yml"]
    file_paths = root_path.glob("*.yml")

    for file_path in file_paths:
        if file_path.name in ["events_l_english.yml"]:
            # vanilla events?
            continue
        print(file_path)
        parse_file(file_path, word_count)

    total_words = sum(word_count.values())
    print(f"Found {total_words} words, and {len(word_count)} unique words")
    words_appearing_once = [word for word, count in word_count.items() if count == 1]

    # common words are more likely to have typos
    # longer words are more likely to have typos
    prior_word_is_typo = sorted(
        ((word, count * len(word)) for word, count in word_count.items()), key=lambda x: x[1], reverse=True
    )

    possible_typos = []
    for common_word, prior_weight in prior_word_is_typo:
        if prior_weight < MINIMUM_CHANCES:
            # arbitrary termination condition
            break
        if len(common_word) < 4:
            # skip these
            continue

        for rare_word in words_appearing_once[:]:
            if levenshtein_distance(common_word, rare_word) == 1:
                # Found a possible hit!
                possible_typos.append((common_word, rare_word, prior_weight))
                # Don't flag possible rare words more than once
                words_appearing_once.remove(rare_word) 
    print(f"Found {len(possible_typos)} possible typos")

    with open("output.csv", "w", encoding="utf-8-sig") as f:
        f.write("common_word,rare_word,prior_weight\n")
        for common_word, rare_word, prior_weight in possible_typos:
            f.write(f"{common_word},{rare_word},{prior_weight}\n")


if __name__ == "__main__":
    main()
