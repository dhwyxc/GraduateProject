import os
import re
from underthesea import word_tokenize

current_directory = os.path.dirname(os.path.abspath(__file__))

with open(current_directory + "/model/vn-stopword.txt", encoding="utf-8") as file:
    stopwords = file.readlines()
    stopwords = [word.rstrip() for word in stopwords]

punctuations = """!()-–=[]{}“”‘’;:'"|\,<>./?@#$%^&*_~"""

special_chars = ["\n", "\t"]

regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ip
    r"(?::\d+)?"  # port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002500-\U00002BEF"  # chinese char
    "\U00002702-\U000027B0"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"  # dingbats
    "\u3030"
    "]+",
    flags=re.UNICODE,
)


def tokenize(text):
    tokenized_text = word_tokenize(text)
    return tokenized_text


def is_punctuation(token):
    global punctuations
    return True if token in punctuations else False


def is_special_chars(token):
    global special_chars
    return True if token in special_chars else False


def is_link(token):
    return re.match(regex, token) is not None


def lowercase(token):
    return token.lower()


def is_stopword(token):
    global stopwords
    return True if token in stopwords else False


def vietnamese_text_preprocessing(text):
    tokens = tokenize(text)
    tokens = [emoji_pattern.sub(r"", token) for token in tokens]
    tokens = [token for token in tokens if not is_punctuation(token)]
    tokens = [token for token in tokens if not is_special_chars(token)]
    tokens = [token for token in tokens if not is_link(token)]
    tokens = [lowercase(token) for token in tokens]
    tokens = [token for token in tokens if not is_stopword(token)]
    return tokens

