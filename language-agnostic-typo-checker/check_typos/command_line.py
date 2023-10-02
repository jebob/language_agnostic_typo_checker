from collections import defaultdict
from pathlib import Path
from Levenshtein import distance as levenshtein_distance


DETECTION_THRESHOLD = 3000  # arbitrary units
PUNC_LIST = ".!?,;:\"'()[]®\\"  # Gets stripped from around, but not inside, words


def clean_line(line):
    comment_pos = line.find("#")
    if comment_pos >= 0:
        # has an EOL comment, remove
        line = line[:comment_pos]
    # Remove some variables
    line = strip_magic_word(line, "[", "]")
    line = strip_magic_word(line, "§", "§")
    # Remve newlines, some word separators
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


def discard_word(word):
    if word in ["", "l_english:"]:
        return True
    for c in word:
        if c.isnumeric():
            return True
    return False


def strip_magic_word(line, lsep, rsep):
    """In e.g. the string 'I am going to [GetUserDestination]', remove the magic word [GetUserDestination]"""
    lsep_position = line.find(lsep)
    if lsep_position >= 0:
        rsep_position = line[lsep_position + 1 :].find(rsep) + lsep_position
        if rsep_position >= lsep_position:
            # found one!
            result = strip_magic_word(line[:lsep_position] + line[(rsep_position + 1) :], lsep, rsep)
            return result
    return line


def parse_file(file_path, word_count: defaultdict):
    with open(file_path, encoding="utf-8-sig") as file:
        for line in file:
            for word in clean_line(line):
                word = clean_word(word)
                if discard_word(word):
                    continue
                word_count[word] += 1


def main():
    word_count = defaultdict(int)
    root_path = Path("C:\Projects\equestria_dev") / "localisation" / "english"
    for file_path in root_path.glob("*.yml"):
        if file_path.name in ["events_l_english.yml"]:
            # vanilla events?
            continue
        print(file_path)
        parse_file(file_path, word_count)

    total_words = sum(word_count.values())
    print(f"Found {total_words} words, and {len(word_count)} unique words")
    words_appearing_once = [word for word, count in word_count.items() if count == 1]

    # common words have more chances to form a typo
    # longer words have more characters that could turn into a typo
    # NOT DONE: longer words are less likely to be unique words
    common_word_and_prior = sorted(
        ((word, count * len(word)) for word, count in word_count.items()), key=lambda x: x[1], reverse=True
    )

    possible_typos = []
    for common_word, prior_weight in common_word_and_prior:
        if prior_weight < DETECTION_THRESHOLD:
            # termination condition
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
