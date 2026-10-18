"""Python script to print Bathukamma festival pattern using stars."""

def print_bathukamma_simple():
    """Print a simple Bathukamma flower stack pattern."""
    print("BATHUKAMMA FESTIVAL PATTERN")
    print("=" * 50)
    print()
    
    # Bathukamma - conical flower stack
    pattern = [
        "           @           ",
        "          @@@          ",
        "         @@@@@         ",
        "        @@@@@@@        ",
        "       @@@@@@@@@       ",
        "      @@@@@@@@@@@      ",
        "     @@@@@@@@@@@@@     ",
        "    @@@@@@@@@@@@@@@    ",
        "   @@@@@@@@@@@@@@@@@   ",
        "  @@@@@@@@@@@@@@@@@@@  ",
        " @@@@@@@@@@@@@@@@@@@@@ ",
        "@@@@@@@@@@@@@@@@@@@@@@@",
        "        |||||          ",
        "        |||||          ",
        "        |||||          ",
        "       =======         ",
        "      =========        ",
        "     ===========       ",
        "    =============      ",
        "   ===============     ",
        "  =================    ",
        " ===================   ",
        "======================="
    ]
    
    for line in pattern:
        print(line)


def print_bathukamma_colorful():
    """Print Bathukamma with different flower layers."""
    print("BATHUKAMMA - FLORAL FESTIVAL (Layered)")
    print("=" * 50)
    print()
    
    # Different flower types for each layer
    layers = [
        ("@", "  @  "),           # Top - small flower
        ("*", "  *  "),           # Layer 2
        ("@", " @@@ "),           # Layer 3
        ("*", " ***** "),         # Layer 4
        ("@", "@@@@@@@"),         # Layer 5
        ("*", "*********"),       # Layer 6
        ("@", "@@@@@@@@@@@"),     # Layer 7
        ("*", "*************"),   # Layer 8
        ("@", "@@@@@@@@@@@@@@@"), # Layer 9
        ("*", "*****************"),# Layer 10
    ]
    
    # Print layers from top to bottom
    for i, (flower, base) in enumerate(layers):
        spaces = " " * (10 - i)
        if i % 2 == 0:
            print(spaces + flower.center(9 + i * 2))
        else:
            print(spaces + flower.center(9 + i * 2))
    
    # Stem
    print(" " * 10 + "|||")
    print(" " * 10 + "|||")
    print(" " * 10 + "|||")
    
    # Base plate
    print(" " * 8 + "===========")
    print(" " * 7 + "=============")
    print(" " * 6 + "===============")
    print(" " * 5 + "=================")


def print_bathukamma_detailed():
    """Print detailed Bathukamma with decorative elements."""
    print("BATHUKAMMA - DETAILED FESTIVAL PATTERN")
    print("=" * 60)
    print()
    
    # Top decoration
    print("         🌸  🌸  🌸  🌸  🌸")
    print("       🌸  🌼  🌻  🌼  🌸")
    print()
    
    # Main conical stack
    rows = 12
    for i in range(rows):
        spaces = " " * (rows - i - 1)
        if i % 3 == 0:
            flower = "@"
        elif i % 3 == 1:
            flower = "*"
        else:
            flower = "#"
        
        # Create the conical shape
        width = 2 * i + 1
        line = flower * width
        print(spaces + line.center(width + 4))
    
    # Stem
    print(" " * (rows - 1) + " ||| ")
    print(" " * (rows - 1) + " ||| ")
    print(" " * (rows - 1) + " ||| ")
    
    # Base (thambalam/plate)
    print(" " * (rows - 3) + "===========")
    print(" " * (rows - 4) + "=============")
    print(" " * (rows - 5) + "===============")
    print(" " * (rows - 6) + "=================")
    
    print()
    print("  Happy Bathukamma Festival! 🌸🌼🌻")
    print("  Celebrated in Telangana, India")


def print_bathukamma_ascii():
    """Print Bathukamma using ASCII art style."""
    print("BATHUKAMMA ASCII ART")
    print("=" * 50)
    print()
    
    bathukamma = """
              @
             @@@
            @@@@@
           @@@@@@@
          @@@@@@@@@
         @@@@@@@@@@@
        @@@@@@@@@@@@@
       @@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@
     @@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@@@@@@@
           |||
           |||
           |||
          =====
         ========
        ===========
       ==============
      ==================
     ======================
    ==========================
    """
    print(bathukamma)


if __name__ == "__main__":
    print_bathukamma_simple()
    print("\n" + "=" * 50 + "\n")
    print_bathukamma_colorful()
    print("\n" + "=" * 50 + "\n")
    print_bathukamma_detailed()
    print("\n" + "=" * 50 + "\n")
    print_bathukamma_ascii()