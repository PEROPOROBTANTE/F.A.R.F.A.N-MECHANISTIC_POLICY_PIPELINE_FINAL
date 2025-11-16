# F.A.R.F.A.N: Framework for Advanced Retrieval of Administrativa Narratives

**A Mechanistic Policy Pipeline for Colombian Development Plan Analysis**

**F.A.R.F.A.N** is a sophisticated, evidence-based analysis tool for Colombian municipal development plans. It leverages a deterministic pipeline, cryptographic proofs, and a comprehensive questionnaire to deliver rigorous, reproducible results.

---

## 🚀 Getting Started

For a complete guide to installation, system activation, and your first analysis, please refer to the **[OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md)**. This is the recommended starting point for all users.

## 🏛️ Architecture

For a deep dive into the system's architecture, including the 9-phase pipeline, cross-cut signals, and deterministic protocols, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

##  quick reference

For a quick reference of the project, see **[DEVELOPER_QUICK_REFERENCE.md](DEVELOPER_QUICK_REFERENCE.md)**.

## 📦 Installation

This project requires **Python 3.12** and enforces a strict dependency management system to ensure reproducibility.

### **MANDATORY**: Editable Install

You **MUST** install the package in editable mode before using it:

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install the package
pip install -e ".[all]"
```

For detailed installation instructions and troubleshooting, see the **[Installation & Setup](OPERATIONAL_GUIDE.md#installation--setup)** section of the operational guide.

---

## 🔐 Cryptographic Proof & Integrity

F.A.R.F.A.N enforces data and execution integrity through two key protocols:

1.  **Cryptographic Proof of Execution**: Every successful pipeline run generates a verifiable cryptographic proof, ensuring that the results are genuine and complete.
2.  **Questionnaire Integrity Protocol**: The 305-question monolith is loaded and validated in a deterministic, tamper-proof manner, guaranteeing the scientific integrity of the analysis.

For more details, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

