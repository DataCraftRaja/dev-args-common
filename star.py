def print_star_pyramid(rows=5):
    for i in range(1, rows + 1):
        spaces = " " * (rows - i)
        stars = "*" * (2 * i - 1)
        print(spaces + stars)

def print_star_right_triangle(rows=5):
    for i in range(1, rows + 1):
        print("*" * i)

if __name__ == "__main__":
    print("Pyramid Star Pattern:")
    print_star_pyramid(5)
    print("\nRight Triangle Star Pattern:")
    print_star_right_triangle(5)
