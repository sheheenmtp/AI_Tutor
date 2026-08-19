--
-- PostgreSQL database dump
--

\restrict pXeSiVHcYsyX8lIuEw3o9CCZOXAM4Mzzbexqf1VDe85RoRxdyhgCryxQfKYQVIf

-- Dumped from database version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_feedback_logs; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.ai_feedback_logs (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    prompt text,
    response text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ai_feedback_logs OWNER TO codemastery_user;

--
-- Name: ai_feedback_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.ai_feedback_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ai_feedback_logs_id_seq OWNER TO codemastery_user;

--
-- Name: ai_feedback_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.ai_feedback_logs_id_seq OWNED BY public.ai_feedback_logs.id;


--
-- Name: concepts; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.concepts (
    id character varying(20) NOT NULL,
    name character varying(255) NOT NULL,
    axis character varying(100),
    level character varying(50),
    mental_model text,
    repair_strategy text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.concepts OWNER TO codemastery_user;

--
-- Name: diagnostic_logs; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.diagnostic_logs (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    error_id character varying(50),
    concept_id character varying(20),
    confidence double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.diagnostic_logs OWNER TO codemastery_user;

--
-- Name: diagnostic_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.diagnostic_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.diagnostic_logs_id_seq OWNER TO codemastery_user;

--
-- Name: diagnostic_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.diagnostic_logs_id_seq OWNED BY public.diagnostic_logs.id;


--
-- Name: errors; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.errors (
    id character varying(50) NOT NULL,
    concept_id character varying(20) NOT NULL,
    description text,
    signal_type character varying(100),
    confidence_weight double precision DEFAULT 0.8
);


ALTER TABLE public.errors OWNER TO codemastery_user;

--
-- Name: learner_concept_state; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.learner_concept_state (
    user_id integer NOT NULL,
    concept_id character varying(20) NOT NULL,
    mastery_score double precision DEFAULT 0.7,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.learner_concept_state OWNER TO codemastery_user;

--
-- Name: problems; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.problems (
    id integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    difficulty text NOT NULL,
    order_index integer NOT NULL,
    starter_code text,
    hints json,
    input_format text NOT NULL,
    output_format text NOT NULL,
    concept_id character varying(20)
);


ALTER TABLE public.problems OWNER TO codemastery_user;

--
-- Name: problems_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.problems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.problems_id_seq OWNER TO codemastery_user;

--
-- Name: problems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.problems_id_seq OWNED BY public.problems.id;


--
-- Name: submissions; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.submissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    problem_id integer NOT NULL,
    code text NOT NULL,
    status character varying(20),
    passed_tests integer,
    total_tests integer,
    score integer,
    submitted_at timestamp without time zone
);


ALTER TABLE public.submissions OWNER TO codemastery_user;

--
-- Name: submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.submissions_id_seq OWNER TO codemastery_user;

--
-- Name: submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.submissions_id_seq OWNED BY public.submissions.id;


--
-- Name: test_cases; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.test_cases (
    id integer NOT NULL,
    problem_id integer NOT NULL,
    input_data text,
    expected_output text NOT NULL,
    is_sample boolean,
    is_hidden boolean,
    points integer
);


ALTER TABLE public.test_cases OWNER TO codemastery_user;

--
-- Name: test_cases_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.test_cases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_cases_id_seq OWNER TO codemastery_user;

--
-- Name: test_cases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.test_cases_id_seq OWNED BY public.test_cases.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    current_level character varying(20),
    total_score integer,
    problems_solved integer,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO codemastery_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO codemastery_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ai_feedback_logs id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.ai_feedback_logs ALTER COLUMN id SET DEFAULT nextval('public.ai_feedback_logs_id_seq'::regclass);


--
-- Name: diagnostic_logs id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs ALTER COLUMN id SET DEFAULT nextval('public.diagnostic_logs_id_seq'::regclass);


--
-- Name: problems id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.problems ALTER COLUMN id SET DEFAULT nextval('public.problems_id_seq'::regclass);


--
-- Name: submissions id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions ALTER COLUMN id SET DEFAULT nextval('public.submissions_id_seq'::regclass);


--
-- Name: test_cases id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.test_cases ALTER COLUMN id SET DEFAULT nextval('public.test_cases_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: ai_feedback_logs; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.ai_feedback_logs (id, submission_id, prompt, response, created_at) FROM stdin;
\.


--
-- Data for Name: concepts; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.concepts (id, name, axis, level, mental_model, repair_strategy, created_at) FROM stdin;
AM3	Return Values	Abstraction	Beginner	\N	\N	2026-02-10 14:48:53.322599
SM2	Assignment Semantics	State & Memory	Beginner	\N	\N	2026-02-10 14:48:53.322599
CF4	Loop Termination	Control Flow	Beginner	\N	\N	2026-02-10 14:48:53.322599
\.


--
-- Data for Name: diagnostic_logs; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.diagnostic_logs (id, submission_id, error_id, concept_id, confidence, created_at) FROM stdin;
\.


--
-- Data for Name: errors; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.errors (id, concept_id, description, signal_type, confidence_weight) FROM stdin;
E_PRINT_RETURN	AM3	Function prints but does not return	\N	0.8
E_ASSIGN_COPY	SM2	Assignment does not create copy	\N	0.8
E_LOOP_TERM	CF4	Infinite or non-terminating loop	\N	0.8
\.


--
-- Data for Name: learner_concept_state; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.learner_concept_state (user_id, concept_id, mastery_score, last_updated) FROM stdin;
3	AM3	0.7	2026-02-10 14:49:30.150602
3	SM2	0.7	2026-02-10 14:49:30.150602
3	CF4	0.7	2026-02-10 14:49:30.150602
\.


--
-- Data for Name: problems; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.problems (id, title, description, difficulty, order_index, starter_code, hints, input_format, output_format, concept_id) FROM stdin;
1	Check Prime Number	Read an integer and print 'Prime' if it is a prime number, otherwise print 'Not Prime'.	beginner	1	# Read integer and check prime\n	["Check divisibility till sqrt(n)", "Handle n <= 1"]	An integer N	Prime or Not Prime	\N
2	Sum of N Numbers	Read N followed by N integers and print their sum.	beginner	2	# Read N and sum values\n	["Use a loop", "Convert input to int"]	N followed by N integers	Sum of the numbers	\N
3	Palindrome String	Read a string and print 'Palindrome' if it reads the same forwards and backwards.	beginner	3	# Check palindrome\n	["Reverse string", "Compare"]	A single string	Palindrome or Not Palindrome	\N
4	Find Maximum	Read N integers and print the maximum value.	beginner	4	# Find maximum number\n	["Track max value"]	N followed by N integers	Maximum number	\N
5	Even or Odd	Read an integer and print 'Even' or 'Odd'.	beginner	5	# Check even or odd\n	["Use modulo operator"]	A single integer	Even or Odd	\N
6	Second Largest Element	Read N integers and print the second largest unique element. If no second largest exists, print -1.	intermediate	6	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\n# Your code here	["Sort the list and remove duplicates", "Check if at least 2 unique values exist"]	First line: N. Second line: N space-separated integers.	A single integer: the second largest, or -1.	\N
7	Rotate Array Left	Read N integers and a number K, then print the array left-rotated by K positions.	intermediate	7	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\nk = int(input())\n# Your code here	["Use slicing: nums[k:] + nums[:k]", "Use modulo to handle K > N"]	First line: N. Second line: N space-separated integers. Third line: K.	N space-separated integers after rotation.	\N
8	Remove Duplicates	Read N integers and print the list with duplicates removed, preserving original order.	intermediate	8	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\n# Your code here	["Use a set to track seen elements", "Iterate and only append unseen elements"]	First line: N. Second line: N space-separated integers.	Space-separated integers with duplicates removed.	\N
9	Two Sum	Read N integers and a target T. Print the 0-based indices (i j) of the two numbers that add up to T. Guaranteed exactly one solution.	intermediate	9	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\nt = int(input())\n# Your code here	["Use a dictionary to store complement and index", "For each number check if target-num is already seen"]	First line: N. Second line: N space-separated integers. Third line: target T.	Two space-separated 0-based indices i and j.	\N
10	Subarray Sum Equals K	Read N integers and a target K. Print the count of contiguous subarrays whose sum equals K.	intermediate	10	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\nk = int(input())\n# Your code here	["Use prefix sums with a hashmap", "For each prefix sum check if prefix_sum - K was seen before"]	First line: N. Second line: N space-separated integers. Third line: K.	A single integer: count of subarrays.	\N
11	Anagram Check	Read two strings and print "Anagram" if they are anagrams of each other, otherwise print "Not Anagram". Case-insensitive.	intermediate	11	# Read two strings\na = input()\nb = input()\n# Your code here	["Sort both strings and compare", "Or use a character frequency counter"]	Two lines, each containing one string.	"Anagram" or "Not Anagram".	\N
12	Longest Common Prefix	Read N strings and print their longest common prefix. If none exists, print an empty line.	intermediate	12	# Read N\nn = int(input())\nwords = [input() for _ in range(n)]\n# Your code here	["Start with the first word as prefix", "Shorten it until all words start with it"]	First line: N. Next N lines: one string each.	The longest common prefix string, or empty line if none.	\N
13	Count Vowels and Consonants	Read a string and print two space-separated integers: count of vowels and count of consonants. Ignore non-alphabetic characters. Case-insensitive.	intermediate	13	# Read string\ns = input()\n# Your code here	["Define vowels as a,e,i,o,u", "Iterate and classify each alphabetic character"]	A single string.	Two space-separated integers: vowel count and consonant count.	\N
14	Reverse Words in Sentence	Read a sentence and print it with the words in reversed order.	intermediate	14	# Read sentence\ns = input()\n# Your code here	["Split the string into words", "Reverse the list and join with spaces"]	A single line sentence.	The sentence with word order reversed.	\N
15	Longest Substring Without Repeating Characters	Read a string and print the length of the longest substring without repeating characters.	intermediate	15	# Read string\ns = input()\n# Your code here	["Use a sliding window with two pointers", "Use a set to track characters in the current window"]	A single string.	A single integer: the length of the longest substring.	\N
16	Binary Search	Read N sorted integers and a target T. Print the 0-based index of T if found, otherwise print -1.	intermediate	16	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\nt = int(input())\n# Your code here	["Use low and high pointers", "Compare mid element with target and adjust range"]	First line: N. Second line: N sorted space-separated integers. Third line: target T.	0-based index of target, or -1 if not found.	\N
17	Merge Two Sorted Arrays	Read two sorted arrays (sizes M and N) and print the merged sorted array.	intermediate	17	# Read M\nm = int(input())\na = list(map(int, input().split()))\nn = int(input())\nb = list(map(int, input().split()))\n# Your code here	["Use two pointers, one per array", "Always pick the smaller current element"]	Line 1: M. Line 2: M sorted integers. Line 3: N. Line 4: N sorted integers.	Space-separated merged sorted integers.	\N
18	Find Kth Smallest	Read N integers and a number K. Print the K-th smallest element (1-based).	intermediate	18	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\nk = int(input())\n# Your code here	["Sort the array", "Return element at index K-1"]	First line: N. Second line: N space-separated integers. Third line: K.	A single integer: the K-th smallest element.	\N
19	Count Inversions	Read N integers and print the number of inversions: pairs (i, j) where i < j but nums[i] > nums[j].	intermediate	19	# Read N\nn = int(input())\nnums = list(map(int, input().split()))\n# Your code here	["Brute force: check all pairs O(n^2)", "Optimal: use merge sort and count during merge"]	First line: N. Second line: N space-separated integers.	A single integer: the number of inversions.	\N
\.

--
-- Backfill concept tags for recommendation routing
--
UPDATE public.problems SET concept_id = 'CF4' WHERE id IN (1, 2, 4, 5, 10, 13, 14);
UPDATE public.problems SET concept_id = 'SM2' WHERE id IN (6, 7, 8, 9, 16, 17, 18, 19);
UPDATE public.problems SET concept_id = 'AM3' WHERE id IN (3, 11, 12, 15);


--
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.submissions (id, user_id, problem_id, code, status, passed_tests, total_tests, score, submitted_at) FROM stdin;
1	3	1	# Read integer and check prime\nprint("Prime")	failed	2	4	20	2026-01-09 04:41:08.464506
2	3	1	# Read integer and check prime\nprint("hello")	failed	0	4	0	2026-01-13 10:38:25.915177
3	3	1	# Read integer and check prime\n	failed	0	4	0	2026-01-17 07:04:18.912491
4	3	1	# Read integer and check prime\n	failed	0	4	0	2026-01-17 07:27:17.664488
5	3	1	# Read integer and check prime\nn = int(input().strip())\n\nif n <= 1:\n    print("Not Prime")\nelif n == 2:\n    print("Prime")\nelif n % 2 == 0:\n    print("Not Prime")\nelse:\n    is_prime = True\n    i = 3\n    while i * i <= n:\n        if n % i == 0:\n            is_prime = False\n            break\n        i += 2\n    print("Prime" if is_prime else "Not Prime")\n	passed	4	4	40	2026-01-17 09:02:05.242939
6	3	2	# Read N and sum values\n	failed	0	3	0	2026-01-17 10:51:18.315497
7	3	2	# Read N and sum values\nprint()	failed	0	3	0	2026-02-10 10:36:51.943614
8	3	2	def sum_of_numbers():\n    \n    total = 0\n    \n    for _ in range(N):\n        total += int(input())\n    \n    return total\n\n# Call the function\nN = int(input())\nsum_of_numbers(N)\n	failed	0	3	0	2026-02-10 10:47:46.627881
9	3	2	# Read N and sum values\n# Read number of inputs\nN = int(input())\n\ntotal = 0\n\n# Loop N times\nfor _ in range(N):\n    num = int(input())\n    total += num\n\n# Print the sum\nprint(total)\n	passed	3	3	30	2026-02-10 10:48:06.132685
10	3	3	# Check palindrome\n# Read input\ns = input().strip()\n\n# Check palindrome\nif s == s[::-1]:\n    print("Palindrome")\nelse:\n    print("Not Palindrome")	passed	3	3	30	2026-02-21 11:03:35.002947
11	3	4	# Read number of integers\nn = int(input())\n\nmaximum = float('-inf')\n\n# Read N integers (each on a new line)\nfor _ in range(n):\n    num = int(input())\n    if num > maximum:\n        maximum = num\n\nprint(maximum)	passed	3	3	30	2026-02-21 11:09:47.247463
12	3	5	n = int(input())\n\nif n % 2 == 0:\n    print("Even")\nelse:\n    print("Odd")	passed	10	10	100	2026-02-21 11:39:15.101791
13	3	6	# Read N\nn = int(input())\n\n# Read integers (space-separated)\narr = list(map(int, input().split()))\n\n# Remove duplicates\nunique_vals = list(set(arr))\n\n# If fewer than 2 unique numbers → no second largest\nif len(unique_vals) < 2:\n    print(-1)\nelse:\n    unique_vals.sort(reverse=True)\n    print(unique_vals[1])	passed	5	5	50	2026-02-21 11:43:18.456891
14	3	7	# Read input\nn = int(input())\narr = list(map(int, input().split()))\nk = int(input())\n\n# handle large k\nk = k % n\n\n# left rotate\nrotated = arr[k:] + arr[:k]\n\n# print result\nprint(*rotated)	passed	4	4	40	2026-02-25 05:37:18.269768
15	3	8	# Read input\nn = int(input())\narr = list(map(int, input().split()))\n\nseen = set()\nresult = []\n\nfor num in arr:\n    if num not in seen:\n        seen.add(num)\n        result.append(num)\n\n# Print result\nprint(*result)	passed	4	4	40	2026-02-25 11:20:20.673618
\.


--
-- Data for Name: test_cases; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.test_cases (id, problem_id, input_data, expected_output, is_sample, is_hidden, points) FROM stdin;
1	1	7	Prime	t	f	10
2	1	10	Not Prime	t	f	10
3	1	1	Not Prime	f	t	10
4	1	13	Prime	f	t	10
5	2	3\n5\n10\n15	30	t	f	10
6	2	1\n100	100	t	f	10
7	2	5\n1\n2\n3\n4\n5	15	f	t	10
8	3	racecar	Palindrome	t	f	10
9	3	hello	Not Palindrome	t	f	10
10	3	madam	Palindrome	f	t	10
11	4	3\n1\n5\n2	5	t	f	10
12	4	1\n99	99	t	f	10
13	4	5\n-1\n-2\n-3\n-4\n-5	-1	f	t	10
14	5	4	Even	t	f	10
15	5	7	Odd	t	f	10
16	5	0	Even	f	t	10
135	19	5\n1 5 2 4 3	4	t	f	10
136	19	5\n1 5 2 4 3	4	t	f	10
137	1	2	Prime	f	f	10
138	1	1	Not Prime	f	t	10
139	1	0	Not Prime	f	t	10
140	1	17	Prime	f	f	10
141	1	100	Not Prime	f	t	10
142	1	97	Prime	f	t	10
143	1	4	Not Prime	t	f	10
144	1	49	Not Prime	f	t	10
145	2	1\n5	5	f	f	10
146	2	4\n1 2 3 4	10	t	f	10
147	2	5\n0 0 0 0 0	0	f	t	10
148	2	3\n-1 -2 -3	-6	f	t	10
149	2	6\n10 20 30 40 50 60	210	f	f	10
150	2	2\n-5 5	0	f	t	10
151	2	5\n1 1 1 1 1	5	t	f	10
152	3	level	Palindrome	f	f	10
153	3	world	Not Palindrome	t	f	10
154	3	a	Palindrome	f	t	10
155	3	abcba	Palindrome	f	f	10
156	3	abcd	Not Palindrome	f	t	10
157	3	noon	Palindrome	f	t	10
158	3	python	Not Palindrome	t	f	10
159	4	1\n42	42	f	f	10
160	4	4\n-1 -2 -3 -4	-1	f	t	10
161	4	5\n3 3 3 3 3	3	f	t	10
162	4	6\n100 200 50 300 150 250	300	t	f	10
163	4	3\n0 -1 1	1	f	f	10
164	4	5\n9 7 5 3 1	9	f	t	10
165	4	5\n1 3 5 7 9	9	t	f	10
166	5	1	Odd	f	f	10
167	5	2	Even	t	f	10
168	5	-3	Odd	f	t	10
169	5	-4	Even	f	t	10
170	5	100	Even	f	f	10
171	5	999	Odd	f	t	10
172	5	0	Even	t	f	10
77	6	5\n3 1 4 1 5	4	t	f	10
78	6	4\n10 10 10 10	-1	f	t	10
79	6	3\n7 3 7	3	f	f	10
80	6	6\n1 2 3 4 5 6	5	f	t	10
81	6	2\n9 1	1	t	f	10
82	7	5\n1 2 3 4 5\n2	3 4 5 1 2	t	f	10
83	7	4\n10 20 30 40\n0	10 20 30 40	f	f	10
84	7	3\n5 6 7\n3	5 6 7	f	t	10
85	7	6\n1 2 3 4 5 6\n4	5 6 1 2 3 4	t	f	10
86	8	6\n1 2 2 3 3 4	1 2 3 4	t	f	10
87	8	5\n5 5 5 5 5	5	f	f	10
88	8	4\n4 3 2 1	4 3 2 1	f	t	10
89	8	7\n1 3 1 2 3 4 2	1 3 2 4	t	f	10
90	9	4\n2 7 11 15\n9	0 1	t	f	10
91	9	3\n3 2 4\n6	1 2	f	f	10
92	9	5\n1 4 6 8 3\n7	0 4	f	t	10
93	9	4\n0 4 3 0\n0	0 3	t	f	10
94	10	5\n1 1 1 1 1\n2	4	t	f	10
95	10	3\n1 2 3\n3	2	f	f	10
96	10	5\n-1 -1 1 1 0\n0	3	f	t	10
97	10	4\n1 2 1 3\n4	1	t	f	10
98	11	listen\nsilent	Anagram	t	f	10
99	11	hello\nworld	Not Anagram	f	f	10
100	11	abc\nab	Not Anagram	f	t	10
101	11	Triangle\nIntegral	Anagram	t	f	10
102	12	3\nflower\nflow\nflight	fl	t	f	10
103	12	3\ndog\nracecar\ncar		f	f	10
104	12	2\ninterface\ninternal	inter	f	t	10
105	12	4\nprefix\npre\nprefix\npresent	pre	t	f	10
106	13	Hello World	3 7	t	f	10
107	13	aeiou	5 0	f	f	10
108	13	rhythm	0 6	f	t	10
109	13	Programming	3 8	t	f	10
110	14	Hello World	World Hello	t	f	10
111	14	I love coding	coding love I	f	f	10
112	14	one	one	f	t	10
113	14	the sky is blue	blue is sky the	t	f	10
114	15	abcabcbb	3	t	f	10
115	15	bbbbb	1	f	f	10
116	15	pwwkew	3	f	t	10
117	15	dvdf	3	t	f	10
118	16	5\n1 3 5 7 9\n5	2	t	f	10
119	16	5\n1 3 5 7 9\n6	-1	f	f	10
120	16	4\n2 4 6 8\n8	3	f	t	10
121	16	1\n42\n42	0	t	f	10
122	16	6\n10 20 30 40 50 60\n25	-1	f	t	10
123	17	3\n1 3 5\n3\n2 4 6	1 2 3 4 5 6	t	f	10
124	17	2\n1 2\n3\n3 4 5	1 2 3 4 5	f	f	10
125	17	1\n5\n1\n5	5 5	f	t	10
126	17	3\n1 4 7\n2\n2 6	1 2 4 6 7	t	f	10
127	18	5\n7 2 1 6 3\n2	2	t	f	10
128	18	4\n4 3 2 1\n4	4	f	f	10
129	18	6\n10 5 8 1 9 3\n3	5	f	t	10
130	18	3\n100 200 300\n1	100	t	f	10
131	19	5\n2 4 1 3 5	3	t	f	10
132	19	4\n4 3 2 1	6	f	f	10
133	19	3\n1 2 3	0	f	t	10
134	19	5\n1 5 2 4 3	4	t	f	10
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: codemastery_user
--

COPY public.users (id, username, current_level, total_score, problems_solved, created_at) FROM stdin;
3	test_user	intermediate	360	8	\N
\.


--
-- Name: ai_feedback_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codemastery_user
--

SELECT pg_catalog.setval('public.ai_feedback_logs_id_seq', 1, false);


--
-- Name: diagnostic_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codemastery_user
--

SELECT pg_catalog.setval('public.diagnostic_logs_id_seq', 1, false);


--
-- Name: problems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codemastery_user
--

SELECT pg_catalog.setval('public.problems_id_seq', 5, true);


--
-- Name: submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codemastery_user
--

SELECT pg_catalog.setval('public.submissions_id_seq', 15, true);


--
-- Name: test_cases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codemastery_user
--

SELECT pg_catalog.setval('public.test_cases_id_seq', 172, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codemastery_user
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- Name: ai_feedback_logs ai_feedback_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.ai_feedback_logs
    ADD CONSTRAINT ai_feedback_logs_pkey PRIMARY KEY (id);


--
-- Name: concepts concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_pkey PRIMARY KEY (id);


--
-- Name: diagnostic_logs diagnostic_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_pkey PRIMARY KEY (id);


--
-- Name: errors errors_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (id);


--
-- Name: learner_concept_state learner_concept_state_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.learner_concept_state
    ADD CONSTRAINT learner_concept_state_pkey PRIMARY KEY (user_id, concept_id);


--
-- Name: problems problems_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_pkey PRIMARY KEY (id);


--
-- Name: submissions submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_pkey PRIMARY KEY (id);


--
-- Name: test_cases test_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.test_cases
    ADD CONSTRAINT test_cases_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: ix_problems_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_problems_id ON public.problems USING btree (id);


--
-- Name: ix_submissions_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_submissions_id ON public.submissions USING btree (id);


--
-- Name: ix_test_cases_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_test_cases_id ON public.test_cases USING btree (id);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ai_feedback_logs ai_feedback_logs_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.ai_feedback_logs
    ADD CONSTRAINT ai_feedback_logs_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- Name: diagnostic_logs diagnostic_logs_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: diagnostic_logs diagnostic_logs_error_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_error_id_fkey FOREIGN KEY (error_id) REFERENCES public.errors(id);


--
-- Name: diagnostic_logs diagnostic_logs_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- Name: errors errors_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE CASCADE;


--
-- Name: problems fk_problem_concept; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT fk_problem_concept FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE SET NULL;


--
-- Name: learner_concept_state learner_concept_state_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.learner_concept_state
    ADD CONSTRAINT learner_concept_state_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE CASCADE;


--
-- Name: learner_concept_state learner_concept_state_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.learner_concept_state
    ADD CONSTRAINT learner_concept_state_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: submissions submissions_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problems(id);


--
-- Name: submissions submissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: test_cases test_cases_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.test_cases
    ADD CONSTRAINT test_cases_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problems(id);


--
-- PostgreSQL database dump complete
--

\unrestrict pXeSiVHcYsyX8lIuEw3o9CCZOXAM4Mzzbexqf1VDe85RoRxdyhgCryxQfKYQVIf
