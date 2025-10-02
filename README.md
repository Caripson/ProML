# PromptLang Language Specification (A Proposal)

*Author: Johan Carlsson*

This repository contains a proposal and an exploration into a structured language for interacting with Large Language Models (LLMs), tentatively named PromptLang.

## 🏛️ Vision

The idea behind PromptLang is to explore how concepts from software engineering (like versioning, testing, and modularity) could be applied to the world of prompt engineering. The hope is that this could lead to AI-powered applications that are more reliable, testable, and maintainable.

This repository contains two main components:

1.  **The Language Specification Wiki:** A complete guide to the principles and syntax of PromptLang.
2.  **A Proof-of-Concept Test Runner:** A Python script that demonstrates how to parse and test `.prompt` files.

---

## 📖 The Wiki

All documentation for the language specification can be found in the `/docs` directory.

**[➡️ Start browsing the Full Language Specification here](./docs/index.md)**

The wiki details all 29 core principles of the language, from `Declarative First` and `Strict I/O` to advanced concepts like `Caching` and `Pipelines`.

---

## 🧪 Proof-of-Concept Test Runner

We have built a simple test runner, `promptlang_test.py`, to demonstrate the feasibility of the `Testability` principle (#6).

### How to Run the Tests

You can run the test runner against the example `.prompt` files located in the `/test_prompts` directory.

1.  **Run the sentiment analysis test (demonstrates basic assertions):**
    ```bash
    python3 promptlang_test.py test_prompts/sentiment_analysis.prompt
    ```
    *(This test is expected to have 1 failing test case by design.)*

2.  **Run the caching test (demonstrates stateful, multi-step tests):**
    ```bash
    python3 promptlang_test.py test_prompts/caching_example.prompt
    ```

This script is a proof-of-concept for parsing the PromptLang DSL, executing tests defined in a `TEST` block, and validating outputs against assertions.

---

## 🌐 Static Site Generation

This project is configured to be built into a full documentation website by two popular static site generators: **MkDocs** and **Hugo**.

### Option 1: Build with MkDocs

MkDocs is a fast and simple static site generator geared towards project documentation.

1.  **Install dependencies:**
    ```bash
    pip install mkdocs mkdocs-material
    ```

2.  **Run the local dev server:**
    ```bash
    mkdocs serve
    ```
    This will start a local server, typically at `http://127.0.0.1:8000`.

### Option 2: Build with Hugo

Hugo is a powerful and extremely fast static site generator.

1.  **Install Hugo:** Follow the official installation guide for your operating system (e.g., `brew install hugo` on macOS or `sudo apt install hugo` on Debian/Ubuntu).

2.  **Initialize a Git repository (if you haven't already):**
    ```bash
    git init
    ```

3.  **Install the theme:** The configuration points to the "book" theme, which you can install as a Git submodule:
    ```bash
    git submodule add https://github.com/alex-shpak/hugo-book themes/book
    ```

4.  **Run the local dev server:**
    ```bash
    hugo server
    ```
    This will start a local server, typically at `http://localhost:1313`.

---

## 🚀 Next Steps

This project is actively evolving. The next steps involve:

*   Further refining the language specification.
*   Expanding the capabilities of the test runner.
*   Developing a static site generator to create a beautiful, searchable website from the wiki's Markdown files.
