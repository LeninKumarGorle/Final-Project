import streamlit as st
from code_editor import code_editor
from leetscrape.questions_list import GetQuestionsList
from leetscrape.question import GetQuestion
import pandas as pd
import tempfile
import io
import os
import random
import re
import time


def extract_function_name(code: str) -> str:
    match = re.search(r'def (\w+)\(', code)
    return match.group(1) if match else None

# Sample input/output test runner
def run_user_code(code, func_name, test_cases):
    exec_globals = {}
    try:
        exec(code, exec_globals)
        Solution = exec_globals.get("Solution")
        if not Solution:
            return False, "No class 'Solution' found in code."
        
        instance = Solution()
        func = getattr(instance, func_name, None)

        if not func:
            return False, f"Function '{func_name}' not found in Solution class."

        results = []
        for inp, expected in test_cases:
            try:
                result = func(*inp)
                results.append((result == expected, inp, result, expected))
            except Exception as e:
                results.append((False, inp, str(e), expected))
        return True, results

    except Exception as e:
        return False, str(e)

# --- UI START ---

st.title("Mock Interview: OA Coding Practice")

# Company slug mapping from companies.csv
TOPICS = [
    "array", "string", "hash-table", "dynamic-programming", "greedy", "tree",
    "two-pointers", "sliding-window", "graph", "linked-list", "stack", "queue"
]

topic = st.selectbox("Select Topic", TOPICS)

# 1. Select company + role
if st.button("Load Question"):
    with st.spinner("Scraping LeetCode..."):
        scraper = GetQuestionsList()
        scraper.scrape()

        # Save to tempdir and load questions.csv
        with tempfile.TemporaryDirectory() as tmpdir:
            time.sleep(2)
            scraper.to_csv(tmpdir + "/")
            questions_path = os.path.join(tmpdir, "questions.csv")
            df = pd.read_csv(questions_path)

            # Filter questions that contain the selected topic
            filtered = df[df["topicTags"].str.contains(topic, na=False, case=False)]

            if filtered.empty:
                st.error("No matching question found for this topic.")
            else:
                meta = filtered.sample(1).iloc[0]
                question = GetQuestion(meta["titleSlug"]).scrape()
                print(f"Selected question: {question.title}")
                st.session_state.question = question

# 2. Show question
if "question" in st.session_state:
    q = st.session_state.question
    st.subheader(q.title)
    st.markdown(q.Body, unsafe_allow_html=True)

    st.markdown("### Write your solution here:")
    st.markdown("---")

    # Default template with placeholder function name
    starter_code = q.Code

    # 3. Show code editor
    editor_content = code_editor(starter_code, height=700)

    if st.button("Run Code"):
        user_code = editor_content["text"]
        func_name = extract_function_name(user_code)

        # 4. Run code with test cases
        test_cases = list(zip(q.inputs, q.outputs))  # list of (input, expected)
        success, result = run_user_code(user_code, q.function_name, test_cases)

        if not success:
            st.error(f"Error: {result}")
        else:
            # 5. Show results
            for passed, inp, out, expected in result:
                st.markdown(
                    f"{'✅' if passed else '❌'} **Input:** `{inp}` → **Output:** `{out}` | **Expected:** `{expected}`"
                )
