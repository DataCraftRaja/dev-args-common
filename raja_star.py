"""Python script to print 'RAJA' using star pattern."""

def print_raja_star():
    """Print RAJA using star (*) pattern."""
    # Define the pattern for each letter
    patterns = {
        'R': [
            "***** ",
            "*    *",
            "***** ",
            "*   * ",
            "*    *"
        ],
        'A': [
            "  *   ",
            " * *  ",
            "***** ",
            "*   * ",
            "*   * "
        ],
        'J': [
            "***** ",
            "    * ",
            "    * ",
            "*   * ",
            " ***  "
        ],
        'A': [
            "  *   ",
            " * *  ",
            "***** ",
            "*   * ",
            "*   * "
        ]
    }
    
    # Print each row
    for row in range(5):
        line = ""
        for letter in ['R', 'A', 'J', 'A']:
            line += patterns[letter][row] + "  "
        print(line)


def print_raja_simple():
    """Print RAJA using a simpler star pattern."""
    raja_pattern = [
        "*   *  ***  ***** *   *",
        "*   * *   *   *   *   *",
        "***** *****   *   *****",
        "*   * *   *   *   *   *",
        "*   * *   *   *   *   *"
    ]
    
    print("RAJA in Star Pattern:")
    print("=" * 30)
    for line in raja_pattern:
        print(line)


def print_raja_block():
    """Print RAJA using block letters with stars."""
    # R
    r = [
        "****** ",
        "*     *",
        "****** ",
        "*   *  ",
        "*    * "
    ]
    
    # A
    a = [
        "  ***  ",
        " *   * ",
        " ***** ",
        "*     *",
        "*     *"
    ]
    
    # J
    j = [
        "*******",
        "     * ",
        "     * ",
        "*    * ",
        " ****  "
    ]
    
    # A (again)
    a2 = [
        "  ***  ",
        " *   * ",
        " ***** ",
        "*     *",
        "*     *"
    ]
    
    print("RAJA in Block Star Pattern:")
    print("=" * 40)
    for i in range(5):
        print(r[i] + " " + a[i] + " " + j[i] + " " + a2[i])


if __name__ == "__main__":
    print_raja_simple()
    print()
    print_raja_block()
    print()
    print_raja_star()