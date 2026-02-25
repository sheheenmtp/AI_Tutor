from models import SessionLocal, Problem, TestCase


def seed_problems():
    db = SessionLocal()

    problems = [
        {
            "title": "Check Prime Number",
            "description": "Read an integer and print 'Prime' if it is a prime number, otherwise print 'Not Prime'.",
            "difficulty": "beginner",
            "order_index": 1,
            "starter_code": "# Read integer and check prime\n",
            "input_format": "An integer N",
            "output_format": "Prime or Not Prime",
            "hints": ["Check divisibility till sqrt(n)", "Handle n <= 1"],
            "tests": [
                ("7", "Prime", True),
                ("10", "Not Prime", True),
                ("1", "Not Prime", False),
                ("13", "Prime", False),
            ],
        },
        {
            "title": "Sum of N Numbers",
            "description": "Read N followed by N integers and print their sum.",
            "difficulty": "beginner",
            "order_index": 2,
            "starter_code": "# Read N and sum values\n",
            "input_format": "N followed by N integers",
            "output_format": "Sum of the numbers",
            "hints": ["Use a loop", "Convert input to int"],
            "tests": [
                ("3\n5\n10\n15", "30", True),
                ("1\n100", "100", True),
                ("5\n1\n2\n3\n4\n5", "15", False),
            ],
        },
        {
            "title": "Palindrome String",
            "description": "Read a string and print 'Palindrome' if it reads the same forwards and backwards.",
            "difficulty": "beginner",
            "order_index": 3,
            "starter_code": "# Check palindrome\n",
            "input_format": "A single string",
            "output_format": "Palindrome or Not Palindrome",
            "hints": ["Reverse string", "Compare"],
            "tests": [
                ("racecar", "Palindrome", True),
                ("hello", "Not Palindrome", True),
                ("madam", "Palindrome", False),
            ],
        },
        {
            "title": "Find Maximum",
            "description": "Read N integers and print the maximum value.",
            "difficulty": "beginner",
            "order_index": 4,
            "starter_code": "# Find maximum number\n",
            "input_format": "N followed by N integers",
            "output_format": "Maximum number",
            "hints": ["Track max value"],
            "tests": [
                ("3\n1\n5\n2", "5", True),
                ("1\n99", "99", True),
                ("5\n-1\n-2\n-3\n-4\n-5", "-1", False),
            ],
        },
        {
            "title": "Even or Odd",
            "description": "Read an integer and print 'Even' or 'Odd'.",
            "difficulty": "beginner",
            "order_index": 5,
            "starter_code": "# Check even or odd\n",
            "input_format": "A single integer",
            "output_format": "Even or Odd",
            "hints": ["Use modulo operator"],
            "tests": [
                ("4", "Even", True),
                ("7", "Odd", True),
                ("0", "Even", False),
            ],
        },
    ]

    for p in problems:
        problem = Problem(
            title=p["title"],
            description=p["description"],
            difficulty=p["difficulty"],
            order_index=p["order_index"],
            starter_code=p["starter_code"],
            input_format=p["input_format"],
            output_format=p["output_format"],
            hints=p["hints"],
        )

        db.add(problem)
        db.flush()  # get problem.id

        for input_data, expected, is_sample in p["tests"]:
            test_case = TestCase(
                problem_id=problem.id,
                input_data=input_data,
                expected_output=expected,
                is_sample=is_sample,
                is_hidden=not is_sample,
                points=10,
            )
            db.add(test_case)

    db.commit()
    db.close()
    print("✅ 5 problems and test cases inserted successfully")


if __name__ == "__main__":
    seed_problems()

