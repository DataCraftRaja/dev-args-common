"""Python script to check and print palindromes."""

def is_palindrome(text):
    """Check if a given text is a palindrome."""
    # Remove spaces and convert to lowercase for comparison
    cleaned = ''.join(char.lower() for char in text if char.isalnum())
    return cleaned == cleaned[::-1]


def find_palindromes(words):
    """Find and return palindromes from a list of words."""
    palindromes = []
    for word in words:
        if is_palindrome(word):
            palindromes.append(word)
    return palindromes


def main():
    # Test words
    test_words = [
        "radar",
        "level",
        "python",
        "madam",
        "hello",
        "racecar",
        "world",
        "deed",
        "A man a plan a canal Panama",
        "Was it a car or a cat I saw"
    ]
    
    print("Palindrome Checker")
    print("=" * 40)
    
    # Check each word
    for word in test_words:
        result = "✓ PALINDROME" if is_palindrome(word) else "✗ Not a palindrome"
        print(f"{word:<40} {result}")
    
    print("\n" + "=" * 40)
    print("Palindromes found:")
    palindromes = find_palindromes(test_words)
    for p in palindromes:
        print(f"  - {p}")


if __name__ == "__main__":
    main()