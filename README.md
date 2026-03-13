# OTC Markets Selenium Test Automation

Automated UI test suite for validating stock quote data on [otcmarkets.com](http://www.otcmarkets.com) using Selenium WebDriver. The project follows the **Page Object Model (POM)** design pattern to keep test logic, page locators, and business-logic validations cleanly separated.

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Java | 1.7+ | Programming language |
| Maven | 3.x | Build & dependency management |
| Selenium WebDriver | 2.45.0 | Browser automation |
| TestNG | 6.8.21 | Test framework & runner |
| Hamcrest | 1.3 | Assertion matchers |
| REST Assured | 2.4.1 | REST API testing utilities |
| JExcelApi (JXL) | 2.6.12 | Excel file support for data-driven tests |
| SikuliX | 1.1.0-SNAPSHOT | Image-based UI interaction |

## Getting Started

### Prerequisites

- **JDK 1.7** or higher
- **Apache Maven 3.x**
- **Mozilla Firefox** (compatible with Selenium 2.45.0 — Firefox 35–38 recommended)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/srebiz/otcmarket_selenium.git
   cd otcmarket_selenium
   ```

2. **Install dependencies**

   ```bash
   mvn clean install -DskipTests
   ```

3. **Run the tests**

   ```bash
   mvn clean test
   ```

## Available Commands

| Command | Description |
|---|---|
| `mvn clean install` | Download dependencies, compile, and run tests |
| `mvn clean install -DskipTests` | Download dependencies and compile without running tests |
| `mvn clean test` | Compile and execute all TestNG test cases |
| `mvn compile` | Compile source code only |

## Project Structure

```
otcmarket_selenium/
├── pom.xml                          # Maven project configuration & dependencies
└── src/
    └── test/
        └── java/
            └── com/otc/selenium/
                ├── ScriptBase.java       # Base class — WebDriver setup & teardown
                ├── OTCModel.java         # Page Object — element locators (@FindBy)
                ├── OTCController.java    # Business logic — verification methods
                └── OTCTestCase001.java   # Test case — quote header & price range checks
```

### Architecture (Page Object Model)

The project uses a three-layer Page Object Model architecture:

- **ScriptBase** — Base test class that handles browser lifecycle (setup/teardown), configures the Firefox WebDriver, sets implicit waits, and provides a URL hook for subclasses.
- **OTCModel** — Page Object that maps UI elements on the OTC Markets quote page to `WebElement` fields using Selenium's `@FindBy` annotations. Includes a highlight helper for visual debugging.
- **OTCController** — Contains the business-logic verification methods (e.g., checking that the quote header matches a ticker symbol, verifying the open price falls within the 52-week range).
- **OTCTestCase001** — A concrete test class that extends `ScriptBase`, targets a specific stock quote page (`CSTI`), and calls controller methods to assert expected behavior.

## Test Coverage

The current test suite (`OTCTestCase001`) validates:

1. **Quote Header Verification** — Asserts the stock symbol displayed on the page matches the expected ticker.
2. **Open Price vs. 52-Week Range** — Asserts the opening price falls within the 52-week high/low range.

## Contributing

Contributions are welcome! To get started:

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b feature/my-feature`)
3. **Commit your changes** (`git commit -m 'feat: add my feature'`)
4. **Push to the branch** (`git push origin feature/my-feature`)
5. **Open a Pull Request** against `master`

### Guidelines

- Follow existing code conventions and the Page Object Model pattern
- Add new page elements to `OTCModel`, business logic to `OTCController`, and tests to new `OTCTestCase*` classes
- Use [conventional commit messages](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, etc.)
- Do not commit IDE-specific files, credentials, or API keys

## License

This project does not currently specify a license. Please contact the repository owner for usage terms.
