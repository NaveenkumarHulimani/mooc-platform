import json

from werkzeug.security import generate_password_hash

from app import create_app
from models import Course, Problem, User, db

ADMIN_EMAIL = "admin@mooc.local"
ADMIN_PASSWORD = "admin123"

COURSES = [
    {
        "key": "python",
        "title": "Python Programming",
        "tag": "Programming",
        "description": "Syntax, data structures, and the idioms that make Python feel like Python — solved with real, executed code.",
    },
    {
        "key": "java",
        "title": "Java Programming",
        "tag": "Programming",
        "description": "Strongly-typed fundamentals, Scanner-based I/O, and the discipline Java rewards — solved with real, executed code.",
    },
    {
        "key": "c",
        "title": "C Programming",
        "tag": "Programming",
        "description": "Pointers, manual memory, and the low-level thinking that everything else is built on — solved with real, executed code.",
    },
    {
        "key": "javascript",
        "title": "JavaScript Programming",
        "tag": "Programming",
        "description": "Dynamic typing, first-class functions, and the async-first mindset the web is built on — solved with real, executed code.",
    },
]

# Each problem template carries the same statement/test-cases across all courses,
# with per-language starter code — this is content shared once and split per course below,
# not duplicated by hand.
PROBLEM_TEMPLATES = [
    {
        "title": "Sum of Two Numbers",
        "difficulty": "easy",
        "description": (
            "Read two integers from input, separated by a space, and print their sum.\n\n"
            "Example input: 3 5\nExample output: 8"
        ),
        "starter_code": {
            "python": "a, b = map(int, input().split())\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int a = sc.nextInt();\n"
                "        int b = sc.nextInt();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int a, b;\n"
                "    scanf(\"%d %d\", &a, &b);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const [a, b] = require('fs').readFileSync(0, 'utf-8').trim().split(' ').map(Number);\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "3 5", "expected_output": "8"},
            {"input": "10 -2", "expected_output": "8"},
            {"input": "0 0", "expected_output": "0"},
        ],
    },
    {
        "title": "Reverse a String",
        "difficulty": "easy",
        "description": "Read a single word and print it reversed.\n\nExample input: hello\nExample output: olleh",
        "starter_code": {
            "python": "s = input()\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String s = sc.nextLine();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main() {\n"
                "    char s[1000];\n"
                "    scanf(\"%s\", s);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const s = require('fs').readFileSync(0, 'utf-8').trim();\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "hello", "expected_output": "olleh"},
            {"input": "python", "expected_output": "nohtyp"},
        ],
    },
    {
        "title": "Count Vowels",
        "difficulty": "easy",
        "description": (
            "Read a single word and print how many vowels (a, e, i, o, u — case-insensitive) it "
            "contains.\n\nExample input: programming\nExample output: 3"
        ),
        "starter_code": {
            "python": "s = input()\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String s = sc.nextLine();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main() {\n"
                "    char s[1000];\n"
                "    scanf(\"%s\", s);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const s = require('fs').readFileSync(0, 'utf-8').trim();\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "programming", "expected_output": "3"},
            {"input": "rhythm", "expected_output": "0"},
        ],
    },
    {
        "title": "Check Prime",
        "difficulty": "medium",
        "description": (
            "Read a positive integer n and print 'Yes' if it is prime, otherwise print 'No'.\n\n"
            "Example input: 7\nExample output: Yes"
        ),
        "starter_code": {
            "python": "n = int(input())\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int n = sc.nextInt();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int n;\n"
                "    scanf(\"%d\", &n);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const n = Number(require('fs').readFileSync(0, 'utf-8').trim());\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "7", "expected_output": "Yes"},
            {"input": "10", "expected_output": "No"},
            {"input": "2", "expected_output": "Yes"},
            {"input": "1", "expected_output": "No"},
        ],
    },
    {
        "title": "Fibonacci Nth Term",
        "difficulty": "medium",
        "description": (
            "Read an integer n and print the nth Fibonacci number (0-indexed: F(0)=0, F(1)=1).\n\n"
            "Example input: 6\nExample output: 8"
        ),
        "starter_code": {
            "python": "n = int(input())\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int n = sc.nextInt();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int n;\n"
                "    scanf(\"%d\", &n);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const n = Number(require('fs').readFileSync(0, 'utf-8').trim());\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "0", "expected_output": "0"},
            {"input": "1", "expected_output": "1"},
            {"input": "6", "expected_output": "8"},
            {"input": "10", "expected_output": "55"},
        ],
    },
    {
        "title": "Sum of Digits",
        "difficulty": "medium",
        "description": (
            "Read a positive integer and print the sum of its digits.\n\n"
            "Example input: 1234\nExample output: 10"
        ),
        "starter_code": {
            "python": "n = int(input())\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int n = sc.nextInt();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int n;\n"
                "    scanf(\"%d\", &n);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const n = require('fs').readFileSync(0, 'utf-8').trim();\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "1234", "expected_output": "10"},
            {"input": "9", "expected_output": "9"},
            {"input": "1000", "expected_output": "1"},
        ],
    },
    {
        "title": "Longest Word in a Sentence",
        "difficulty": "hard",
        "description": (
            "Read a sentence and print the longest word in it. If there is a tie, print the "
            "first one that appears.\n\nExample input: the quick brown fox\nExample output: quick"
        ),
        "starter_code": {
            "python": "sentence = input()\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String sentence = sc.nextLine();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main() {\n"
                "    char sentence[1000];\n"
                "    fgets(sentence, sizeof(sentence), stdin);\n"
                "    sentence[strcspn(sentence, \"\\n\")] = 0;\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const sentence = require('fs').readFileSync(0, 'utf-8').trim();\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "the quick brown fox", "expected_output": "quick"},
            {"input": "a bb ccc dd", "expected_output": "ccc"},
        ],
    },
    {
        "title": "Balanced Parentheses",
        "difficulty": "hard",
        "description": (
            "Read a string containing only '(', ')', '{', '}', '[' and ']'. Print 'Balanced' if "
            "brackets are properly matched and nested, otherwise print 'Not Balanced'.\n\n"
            "Example input: {[()]}\nExample output: Balanced"
        ),
        "starter_code": {
            "python": "s = input()\n# write your code here\n",
            "java": (
                "import java.util.Scanner;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String s = sc.nextLine();\n"
                "        // write your code here\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main() {\n"
                "    char s[1000];\n"
                "    scanf(\"%s\", s);\n"
                "    // write your code here\n"
                "    return 0;\n"
                "}\n"
            ),
            "javascript": (
                "const s = require('fs').readFileSync(0, 'utf-8').trim();\n"
                "// write your code here\n"
            ),
        },
        "test_cases": [
            {"input": "{[()]}", "expected_output": "Balanced"},
            {"input": "{[(])}", "expected_output": "Not Balanced"},
            {"input": "()", "expected_output": "Balanced"},
        ],
    },
]


def seed():
    app = create_app()
    with app.app_context():
        if not User.query.filter_by(email=ADMIN_EMAIL).first():
            db.session.add(
                User(
                    name="Admin",
                    email=ADMIN_EMAIL,
                    password_hash=generate_password_hash(ADMIN_PASSWORD),
                    is_admin=True,
                )
            )
            db.session.commit()
            print(f"Created admin account: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        else:
            print("Admin account already exists — skipping.")

        # Idempotent per-course: only creates courses (and their problems) that don't
        # already exist yet, so re-running this after adding a new course to COURSES
        # never touches or duplicates existing courses/problems/student progress.
        new_course_count = 0
        new_problem_count = 0
        for c in COURSES:
            course = Course.query.filter_by(key=c["key"]).first()
            if course:
                continue

            course = Course(key=c["key"], title=c["title"], tag=c["tag"], description=c["description"])
            db.session.add(course)
            db.session.flush()  # assign an id without a full commit yet
            new_course_count += 1

            for template in PROBLEM_TEMPLATES:
                db.session.add(
                    Problem(
                        course_id=course.id,
                        title=template["title"],
                        difficulty=template["difficulty"],
                        description=template["description"],
                        starter_code=template["starter_code"][c["key"]],
                        test_cases=json.dumps(template["test_cases"]),
                    )
                )
                new_problem_count += 1

        db.session.commit()
        if new_course_count:
            print(f"Seeded {new_course_count} new course(s) and {new_problem_count} new problem(s).")
        else:
            print("All courses already exist — nothing new to seed.")


if __name__ == "__main__":
    seed()
