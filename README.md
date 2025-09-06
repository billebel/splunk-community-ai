# Secure, Governable AI Gateway for Splunk

**A production-ready alternative to Splunk AI Assistant focused on safety, compliance, and predictable results using Configuration as Code.**

The `splunk-community-ai` project is an open-source, governable AI gateway for Splunk that addresses the core challenges of enterprise AI integration. If you're looking for a way to use LLMs with Splunk without the risk of inefficient queries, data exposure, or unpredictable AI behavior, this project provides auditable security guardrails and predictable workflows.

## The Problem: Why Enterprise AI Integration Fails

Current AI solutions for Splunk create significant risks in production environments:

*   **Uncontrolled AI Behavior:** AI assistants guess at index names, create inefficient searches, and potentially expose sensitive data
*   **No Security Guardrails:** Direct API access allows AI to run dangerous commands like `| delete` or `| outputlookup`
*   **Compliance Nightmares:** No audit trail of AI decisions or ability to prove data protection compliance
*   **Unpredictable Results:** Every AI interaction is different, making it impossible to ensure consistent, safe behavior
*   **Hidden Security Policies:** Security logic buried in application code that auditors can't easily review

## Our Solution: A Governance-First Approach

Instead of letting AI improvise with dangerous freedom, we implement **Configuration as Code** - a controlled approach where AI follows your organization's best practices every time. This creates a reliable governance layer where you can enforce data protection, search efficiency, and compliance requirements before any query runs.

## Key Features: Enterprise-Grade AI Governance

### 🛡️ Auditable Security Guardrails
Use a simple `guardrails.yaml` file to **block dangerous commands** like `| delete` or **mask sensitive fields** to prevent data leakage. Security policies are version-controlled and human-readable - no more security logic buried in code.

### 🔄 Predictable AI with Prompt Workflows  
Ensure consistent and reliable results by guiding AI with **version-controlled workflows**, preventing dangerous improvisations and ensuring repeatable outcomes.

### 📊 Complete Audit Trail via Git
Maintain a perfect, immutable record of every policy change for **compliance and security reviews**. When auditors ask "How do you control your AI?", show them your git history.

### ⚡ Performance Optimization
Built-in **query efficiency controls** and **resource management** prevent AI from creating expensive searches that impact Splunk performance.

### 🎯 Multi-LLM Support
Works with **OpenAI, Anthropic Claude, Google Gemini** - choose the right model for your security requirements and budget.

Show your auditors exactly how AI is controlled with simple, readable configuration:

```yaml
# guardrails.yaml - A clear, auditable security policy
blocked_commands:
  - "|delete"
  - "|outputlookup"
  - "|sendemail"

sensitive_fields:
  - "password"
  - "ssn"
  - "credit_card"
```

When your auditor asks to see your security policies, you don't have to show them Python code. You can show them this file.

## Who This Is For

This **secure AI gateway** is designed for organizations that need enterprise-grade AI governance:

### 🏢 **Security Teams**
Get auditable, version-controlled security policies that can be reviewed without reading code. Perfect for organizations with strict **AI governance** requirements.

### 📋 **Compliance Officers**  
Complete audit trail of all AI policy changes. Run `git log guardrails.yaml` to show auditors exactly who changed what, when, and why.

### 🔧 **Splunk Administrators**
Deploy predictable AI that follows your organization's best practices instead of improvising dangerous queries.

### 🛡️ **DevSecOps Teams**
Implement **"shift-left" security** for AI with configuration-as-code that integrates seamlessly with your existing GitOps workflows.

## Deployment Options and Validation

We've designed this reference model to work in different environments and use cases:

*   **Web Portal Integration:** Complete audit-ready interface with session management and user tracking
*   **MCP Server (MCP-only):** Lightweight integration with existing AI tools like Claude Desktop
*   **Development Environment:** Testing setup with sample Splunk data for evaluation

To ensure reliability, we've built comprehensive validation into the reference model. Our automated testing covers security guardrails, deployment procedures, and cross-platform compatibility. We believe that trust in AI systems comes from transparent validation of their behavior.

## Use Cases: Real-World AI Security Scenarios

### 🚨 **"We need AI but can't risk data exposure"**
**Solution:** Implement data masking and field filtering to ensure sensitive information never leaves your environment.

### ⚡ **"AI keeps creating expensive searches that impact performance"**  
**Solution:** Built-in query efficiency controls and resource management prevent costly AI mistakes.

### 📊 **"Auditors want to see how we control our AI"**
**Solution:** Version-controlled `guardrails.yaml` provides clear, auditable security policies that non-technical stakeholders can understand.

### 🎯 **"We want consistent AI results, not random improvisation"**
**Solution:** Prompt workflows ensure repeatable, predictable AI behavior aligned with your operational procedures.

---

## Why Choose This Over Splunk AI Assistant?

| Challenge | Splunk AI Assistant | This Secure AI Gateway |
|-----------|-------------------|----------------------|
| **Security Control** | Limited guardrails | Comprehensive `guardrails.yaml` configuration |
| **Audit Compliance** | Minimal audit trail | Complete git-based audit history |
| **Data Protection** | Basic controls | Advanced data masking and field filtering |
| **Query Efficiency** | AI improvises searches | Guided workflows prevent expensive queries |
| **Customization** | Vendor-controlled | Open-source, fully customizable |
| **Multi-LLM Support** | Single provider | OpenAI, Anthropic, Google Gemini support |

**This is a production-ready reference implementation** that gives you the AI capabilities you want with the enterprise controls you need.

## Quick Start: Get Secure AI Running in Minutes

Ready to deploy **governable AI for Splunk** with enterprise-grade security? Our interactive setup guides you through:

1. **Choose Your Deployment:** MCP-only integration, full web interface, or development environment
2. **Configure Security Guardrails:** Set up `guardrails.yaml` with your data protection rules  
3. **Connect Your LLM:** OpenAI, Anthropic Claude, or Google Gemini
4. **Test Security Controls:** Validate that dangerous commands are blocked and sensitive data is masked

```bash
# Clone and run interactive setup
git clone https://github.com/billebel/splunk-community-ai.git
cd splunk-community-ai
./scripts/deploy.sh  # Linux/Mac
# or
scripts/deploy.bat   # Windows
```

## Prerequisites

Before you begin, ensure you have:

*   **Docker and Docker Compose:** Required for containerized deployment
*   **API Keys (for web interface option):** At least one of:
    *   `ANTHROPIC_API_KEY` - For Claude models (recommended)
    *   `OPENAI_API_KEY` - For OpenAI GPT models
    *   `GOOGLE_API_KEY` - For Google Gemini models
*   **Splunk Access:** Connection details for your Splunk instance

## Getting Started

While this isn't a plug-and-play solution, we've created a set of documents to help you get started. We hope you'll find them useful.

*   **[Pack Setup Guide](docs/pack-setup.md):** This is the best place to start. It will walk you through the installation and configuration process.
*   **[Architecture Overview](docs/architecture.md):** If you want to understand how all the pieces fit together, this document provides a high-level overview of the system's architecture.
*   **[Security Guardrails](docs/security-guardrails.md):** This document details the security features of the project and explains how to configure them.
*   **[Usage Examples](docs/examples.md):** See the system in action with a variety of real-world usage examples.
*   **[Prompt Workflows](docs/prompt-workflows.md):** Learn how we use prompts to guide the AI's behavior and ensure consistent results.

**For those ready to evaluate:** We've created interactive deployment scripts (`scripts/deploy.sh` or `scripts/deploy.bat`) that guide you through the setup process and help you choose the right deployment option for your environment.

## Our Philosophy and Invitation to Collaborate

We are sharing this project in the hope that it will be a useful starting point for others who are facing the same challenges we are. We are not claiming to have all the answers, and we are eager to learn from the community.

We welcome your feedback, your questions, and your contributions. Please feel free to open an issue, start a discussion, or submit a pull request.